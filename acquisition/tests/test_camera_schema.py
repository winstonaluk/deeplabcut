"""The camera backend schema: what a backend reports about itself, and what
preflight does with the answer.

Every test here runs against MockCamera with no hardware attached
(acquisition/CLAUDE.md invariant 2). The point of the schema is that the
config-versus-hardware comparisons are exercised by the ordinary test suite
rather than only discovered on the rig -- which is how a 1280x720 config
value meeting a 720x540 sensor went unnoticed. See HARDWARE.md.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pytest

from acquisition.camera_backend import CameraBackend, CameraError, NodeCheck
from acquisition.frame import Frame, PixelFormat
from acquisition.mock_camera import MockCamera
from acquisition.preflight import run_preflight_checks
from acquisition.writer import WriterError, WriterThread
from app.config import load_config
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


# -- PixelFormat --------------------------------------------------------------


@pytest.mark.parametrize(
    "fmt,channels,ffmpeg,shape",
    [
        (PixelFormat.MONO8, 1, "gray8", (540, 720)),
        (PixelFormat.BGR8, 3, "bgr24", (540, 720, 3)),
    ],
)
def test_pixel_format_carries_its_own_ffmpeg_and_shape_contract(fmt, channels, ffmpeg, shape):
    assert fmt.channels == channels
    assert fmt.ffmpeg_pixel_format == ffmpeg
    assert fmt.expected_shape(720, 540) == shape


def test_frame_defaults_to_mono8():
    frame = Frame(image=np.zeros((4, 4), dtype=np.uint8), hardware_timestamp_ns=1, frame_id=0)
    assert frame.pixel_format is PixelFormat.MONO8


# -- MockCamera reports the same things a real backend does -------------------


def test_mock_camera_reports_its_own_geometry_and_rate():
    camera = MockCamera(serial="mock-1", width=720, height=540, fps=30)
    assert camera.resolution == (720, 540)
    assert camera.frame_rate == 30
    assert camera.pixel_format is PixelFormat.MONO8
    assert camera.incomplete_frame_count == 0


def test_mock_camera_emits_frames_in_its_declared_pixel_format():
    for fmt in (PixelFormat.MONO8, PixelFormat.BGR8):
        camera = MockCamera(serial="m", width=8, height=6, fps=10, pixel_format=fmt)
        frames: list[Frame] = []
        camera.open()
        camera.start_streaming(frames.append)
        for _ in range(100):
            if frames:
                break
            import time as _t

            _t.sleep(0.01)
        camera.stop_streaming()
        camera.close()

        assert frames, f"no frames delivered for {fmt}"
        assert frames[0].pixel_format is fmt
        assert frames[0].image.shape == fmt.expected_shape(8, 6)


def test_open_is_idempotent():
    """Preflight opens the camera and leaves it open; CaptureController then
    opens it again. Both are legitimate, so the second must be a no-op."""
    camera = MockCamera(serial="m", width=8, height=8, fps=10)
    camera.open()
    camera.open()
    camera.close()
    camera.close()


# -- verify_settings ----------------------------------------------------------


class _WrongSettingsCamera(MockCamera):
    """A camera whose UserSet did not install what config expects."""

    def verify_settings(self, expected: Mapping[str, str]) -> tuple[NodeCheck, ...]:
        actuals = {"ExposureAuto": "Continuous", "GammaEnable": "True"}
        return tuple(
            NodeCheck(
                node=node,
                expected=value,
                actual=actuals.get(node, value),
                passed=actuals.get(node, value) == value,
            )
            for node, value in expected.items()
        )


def test_node_check_describes_a_mismatch_usefully():
    ok = NodeCheck(node="ExposureAuto", expected="Off", actual="Off", passed=True)
    bad = NodeCheck(node="ExposureAuto", expected="Off", actual="Continuous", passed=False)
    assert ok.describe() == "ExposureAuto: Off"
    assert "expected 'Off', got 'Continuous'" in bad.describe()


def test_mock_verify_settings_passes_everything_so_the_no_hardware_path_works():
    camera = MockCamera(serial="m", width=8, height=8, fps=10)
    checks = camera.verify_settings({"ExposureAuto": "Off", "GainAuto": "Off"})
    assert [c.node for c in checks] == ["ExposureAuto", "GainAuto"]
    assert all(c.passed for c in checks)


# -- preflight ----------------------------------------------------------------


def test_preflight_blocks_on_resolution_mismatch(tmp_path):
    camera = MockCamera(serial="m", width=720, height=540, fps=30)
    result = run_preflight_checks(
        camera, "UserSet1", tmp_path, min_free_gb=0.0,
        expected_resolution=(1280, 720),
    )
    assert result.passed is False
    assert any("resolution" in f.lower() for f in result.failures)
    assert any("720x540" in f for f in result.failures)


def test_preflight_passes_when_resolution_agrees(tmp_path):
    camera = MockCamera(serial="m", width=720, height=540, fps=30)
    result = run_preflight_checks(
        camera, "UserSet1", tmp_path, min_free_gb=0.0,
        expected_resolution=(720, 540),
    )
    assert [f for f in result.failures if "resolution" in f.lower()] == []


def test_preflight_blocks_on_frame_rate_mismatch(tmp_path):
    """A camera left free-running delivers far more frames than the rate
    stamped on the video, which makes trial duration wrong."""
    camera = MockCamera(serial="m", width=720, height=540, fps=66.12)
    result = run_preflight_checks(
        camera, "UserSet1", tmp_path, min_free_gb=0.0,
        expected_fps=30.0, fps_tolerance=0.5,
    )
    assert result.passed is False
    assert any("frame rate" in f.lower() for f in result.failures)


def test_preflight_accepts_frame_rate_inside_tolerance(tmp_path):
    camera = MockCamera(serial="m", width=720, height=540, fps=30.2)
    result = run_preflight_checks(
        camera, "UserSet1", tmp_path, min_free_gb=0.0,
        expected_fps=30.0, fps_tolerance=0.5,
    )
    assert [f for f in result.failures if "frame rate" in f.lower()] == []


def test_preflight_reports_each_wrong_camera_setting_separately(tmp_path):
    camera = _WrongSettingsCamera(serial="m", width=720, height=540, fps=30)
    result = run_preflight_checks(
        camera, "UserSet1", tmp_path, min_free_gb=0.0,
        expected_nodes={"ExposureAuto": "Off", "GammaEnable": "False", "TriggerMode": "Off"},
    )
    assert result.passed is False
    assert any("ExposureAuto" in f for f in result.failures)
    assert any("GammaEnable" in f for f in result.failures)
    # TriggerMode was correct, so it must not appear as a failure.
    assert not any("TriggerMode" in f for f in result.failures)


def test_preflight_reports_every_failure_in_one_pass(tmp_path):
    """An experimenter with an animal in hand should see everything that
    needs fixing at once, not one problem at a time."""
    camera = _WrongSettingsCamera(serial="m", width=720, height=540, fps=66.0)
    result = run_preflight_checks(
        camera, "UserSet1", tmp_path, min_free_gb=1e9,
        expected_resolution=(1280, 720),
        expected_fps=30.0,
        expected_nodes={"ExposureAuto": "Off"},
    )
    assert result.passed is False
    assert len(result.failures) >= 4  # resolution, fps, ExposureAuto, disk


def test_preflight_retains_passing_checks_for_display(tmp_path):
    camera = MockCamera(serial="mock-serial-1", width=720, height=540, fps=30)
    result = run_preflight_checks(
        camera, "UserSet1", tmp_path, min_free_gb=0.0,
        expected_resolution=(720, 540),
    )
    passed_names = [c.name for c in result.passed_checks]
    assert "Camera detected" in passed_names
    assert any("mock-serial-1" in c.detail for c in result.passed_checks)


def test_preflight_skips_camera_checks_when_the_camera_will_not_open(tmp_path):
    class _DeadCamera(MockCamera):
        def open(self) -> None:
            raise CameraError("no camera with serial 22514545 found")

    result = run_preflight_checks(
        _DeadCamera(serial="m", width=8, height=8, fps=10),
        "UserSet1", tmp_path, min_free_gb=0.0,
        expected_resolution=(720, 540),
        expected_nodes={"ExposureAuto": "Off"},
    )
    assert result.passed is False
    assert any("Camera detected" in f for f in result.failures)
    # One root cause, one failure -- not a cascade of unreadable-node reports.
    assert not any("ExposureAuto" in f for f in result.failures)


# -- writer geometry guard ----------------------------------------------------


def test_writer_rejects_frames_that_do_not_match_its_ffmpeg_pipe(tmp_path):
    """The bug this exists for: FFmpeg does not error on a size mismatch, it
    silently re-slices the byte stream into sheared video."""
    from acquisition.frame_queue import BoundedFrameQueue

    writer = WriterThread(
        frame_queue=BoundedFrameQueue(maxsize=4),
        output_path=tmp_path / "out.mp4",
        width=1280, height=720, fps=30,
        codec="libx264", crf=28, pixel_format="yuv420p",
        source_pixel_format=PixelFormat.MONO8,
    )
    wrong = Frame(
        image=np.zeros((540, 720), dtype=np.uint8),
        hardware_timestamp_ns=0,
        frame_id=0,
    )
    with pytest.raises(WriterError) as exc:
        writer._assert_frame_matches_pipe(wrong)
    assert "720x540" not in str(exc.value)  # reports the configured size...
    assert "(540, 720)" in str(exc.value)  # ...and what actually arrived
    assert "config.toml" in str(exc.value)


def test_writer_rejects_a_pixel_format_it_was_not_configured_for(tmp_path):
    from acquisition.frame_queue import BoundedFrameQueue

    writer = WriterThread(
        frame_queue=BoundedFrameQueue(maxsize=4),
        output_path=tmp_path / "out.mp4",
        width=720, height=540, fps=30,
        codec="libx264", crf=28, pixel_format="yuv420p",
        source_pixel_format=PixelFormat.MONO8,
    )
    colour = Frame(
        image=np.zeros((540, 720, 3), dtype=np.uint8),
        hardware_timestamp_ns=0,
        frame_id=0,
        pixel_format=PixelFormat.BGR8,
    )
    with pytest.raises(WriterError, match="mono8"):
        writer._assert_frame_matches_pipe(colour)


# -- config -------------------------------------------------------------------


def test_config_matches_the_rig_camera():
    """These values were read off the camera, not chosen. See HARDWARE.md."""
    config = load_config(CONFIG_PATH)
    assert config.capture.resolution == (720, 540)
    assert config.capture.source_pixel_format is PixelFormat.MONO8
    assert config.capture.stream_buffer_count >= 30  # >= 1 s of slack at 30 fps


def test_camera_verify_table_covers_the_settings_that_corrupt_training_data():
    config = load_config(CONFIG_PATH)
    assert config.camera_verify["ExposureAuto"] == "Off"
    assert config.camera_verify["GainAuto"] == "Off"
    assert config.camera_verify["GammaEnable"] == "False"
    assert config.camera_verify["AcquisitionFrameRateEnable"] == "True"
    assert config.camera_verify["SensorShutterMode"] == "Global"


def test_camera_verify_pixel_format_agrees_with_capture_pixel_format():
    """Two places name the pixel format and they must not drift: the camera
    is told what to produce, and the writer is told what to expect."""
    config = load_config(CONFIG_PATH)
    assert (
        config.camera_verify["PixelFormat"].lower()
        == config.capture.source_pixel_format.value.lower()
    )


def test_qsv_and_x264_get_their_own_quality_scale():
    """-crf and -global_quality are different scales. One shared number meant
    two different qualities depending on which encoder resolved at run time."""
    from app.config import EncoderConfig

    encoder = EncoderConfig(
        codec="h264_qsv", fallback_codec="libx264",
        crf=20, qsv_global_quality=22, pixel_format="yuv420p",
    )
    assert encoder.quality_for("h264_qsv") == ("-global_quality", 22)
    assert encoder.quality_for("libx264") == ("-crf", 20)
    assert encoder.preset_for("h264_qsv") == encoder.qsv_preset
    assert encoder.preset_for("libx264") == encoder.preset


def test_qsv_quality_falls_back_to_crf_when_unset():
    """So a config.toml written before the split still loads."""
    from app.config import EncoderConfig

    encoder = EncoderConfig(
        codec="h264_qsv", fallback_codec="libx264", crf=18, pixel_format="yuv420p",
    )
    assert encoder.quality_for("h264_qsv") == ("-global_quality", 18)


@pytest.mark.parametrize(
    "codec,flag", [("h264_qsv", "-global_quality"), ("libx264", "-crf")]
)
def test_writer_command_carries_the_right_quality_flag(tmp_path, codec, flag):
    from acquisition.frame_queue import BoundedFrameQueue

    writer = WriterThread(
        frame_queue=BoundedFrameQueue(maxsize=4),
        output_path=tmp_path / "out.mp4",
        width=720, height=540, fps=30,
        codec=codec, crf=21, pixel_format="yuv420p",
        preset="slow", gop=120,
    )
    cmd = writer.build_command()
    assert cmd[cmd.index("-c:v") + 1] == codec
    assert cmd[cmd.index(flag) + 1] == "21"
    assert cmd[cmd.index("-preset") + 1] == "slow"
    assert cmd[cmd.index("-g") + 1] == "120"
    # Raw input geometry must describe the frames, not the output.
    assert cmd[cmd.index("-video_size") + 1] == "720x540"
    assert cmd[cmd.index("-pixel_format") + 1] == "gray8"
    assert cmd[cmd.index("-pix_fmt") + 1] == "yuv420p"


def test_keyframe_interval_becomes_a_gop_in_frames():
    config = load_config(CONFIG_PATH)
    gop = round(config.encoder.keyframe_interval_s * config.capture.fps)
    assert gop == 120  # 4 s at 30 fps


def test_config_rejects_an_unknown_pixel_format():
    from app.config import CaptureConfig, ConfigError

    capture = CaptureConfig(
        fps=30, width=720, height=540, queue_maxsize=10,
        preview_fps=15, preroll_buffer_s=2.0, pixel_format="rgb999",
    )
    with pytest.raises(ConfigError):
        _ = capture.source_pixel_format

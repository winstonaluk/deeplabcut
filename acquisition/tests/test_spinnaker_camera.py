"""SpinnakerCamera: structural behaviour with no hardware, plus a
hardware-marked suite that needs the real camera.

The unmarked tests must pass with nothing plugged in (invariant 2) and with no
Spinnaker SDK installed at all -- which is why the module under test imports
PySpin lazily inside methods rather than at module scope.

Hardware tests are deselected by default (see pyproject.toml addopts). Run them
at the rig with:

    pytest -m hardware
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from acquisition.camera_backend import CameraBackend, CameraError
from acquisition.frame import PixelFormat
from acquisition.spinnaker_camera import (
    REQUIRED_CHUNKS,
    STREAM_BUFFER_HANDLING_MODE,
    SpinnakerCamera,
    _values_match,
)

SERIAL = "22514545"  # the rig camera; see acquisition/HARDWARE.md


# -- structural, no hardware --------------------------------------------------


def test_satisfies_camera_backend():
    camera = SpinnakerCamera(serial=SERIAL)
    assert isinstance(camera, CameraBackend)
    assert camera.serial == SERIAL
    assert camera.is_streaming is False
    assert camera.incomplete_frame_count == 0


def test_pixel_format_is_known_before_the_camera_is_open():
    """The target format is a construction-time decision from config, unlike
    resolution and frame rate, which are read from the camera."""
    assert SpinnakerCamera(serial=SERIAL).pixel_format is PixelFormat.MONO8
    assert (
        SpinnakerCamera(serial=SERIAL, pixel_format=PixelFormat.BGR8).pixel_format
        is PixelFormat.BGR8
    )


@pytest.mark.parametrize("prop", ["resolution", "frame_rate"])
def test_hardware_reported_properties_refuse_to_guess(prop):
    """These must come from the camera. Returning the configured value instead
    is the exact failure the schema exists to prevent."""
    camera = SpinnakerCamera(serial=SERIAL)
    with pytest.raises(CameraError):
        getattr(camera, prop)


def test_close_is_idempotent_on_a_camera_that_never_opened():
    camera = SpinnakerCamera(serial=SERIAL)
    camera.close()
    camera.close()
    assert camera.is_streaming is False


def test_load_user_set_reports_why_it_failed_rather_than_raising():
    camera = SpinnakerCamera(serial=SERIAL)
    assert camera.load_user_set("UserSet1") is False
    assert camera.last_user_set_error == "camera is not open"


def test_verify_settings_requires_an_open_camera():
    with pytest.raises(CameraError):
        SpinnakerCamera(serial=SERIAL).verify_settings({"ExposureAuto": "Off"})


def test_recording_critical_constants_are_pinned():
    """Both are load-bearing and easy to regress silently. NewestOnly drops
    frames without telling us (right for a viewer, wrong for a recorder), and
    invariant 6 is unsatisfiable without both chunks, which ship disabled."""
    assert STREAM_BUFFER_HANDLING_MODE == "OldestFirst"
    assert set(REQUIRED_CHUNKS) == {"FrameID", "Timestamp"}


@pytest.mark.parametrize(
    "actual,expected,matches",
    [
        ("Off", "Off", True),
        ("off", "Off", True),          # symbolic case varies by node
        ("True", "True", True),
        ("False", "false", True),      # TOML writes `false`, camera says "False"
        ("30.000000123", "30", True),  # float nodes read back with noise
        ("30.0", "30.0", True),
        ("Continuous", "Off", False),
        ("BayerRG8", "Mono8", False),
        ("<unreadable>", "Off", False),
    ],
)
def test_node_value_comparison_tolerates_formatting_but_not_difference(actual, expected, matches):
    assert _values_match(actual, expected) is matches


# -- hardware -----------------------------------------------------------------


@pytest.fixture
def camera():
    cam = SpinnakerCamera(serial=SERIAL, stream_buffer_count=64)
    cam.open()
    yield cam
    cam.close()


@pytest.mark.hardware
def test_open_reports_real_geometry_and_is_idempotent(camera):
    camera.open()  # second open must be a no-op, not an error
    width, height = camera.resolution
    assert (width, height) == (720, 540)
    assert camera.frame_rate > 0


@pytest.mark.hardware
def test_streaming_delivers_frames_with_intact_chunk_data(camera):
    frames = []
    camera.start_streaming(frames.append)
    camera.start_streaming(frames.append)  # idempotent
    time.sleep(2.0)
    camera.stop_streaming()
    camera.stop_streaming()  # idempotent

    assert len(frames) > 10, "camera delivered almost nothing"
    assert camera.incomplete_frame_count == 0

    width, height = camera.resolution
    first = frames[0]
    assert first.pixel_format is PixelFormat.MONO8
    assert first.image.shape == (height, width)
    assert first.image.dtype == np.uint8

    ids = [f.frame_id for f in frames]
    assert all(b - a == 1 for a, b in zip(ids, ids[1:])), "frame ID gaps"

    stamps = [f.hardware_timestamp_ns for f in frames]
    assert all(b > a for a, b in zip(stamps, stamps[1:])), "timestamps not increasing"


@pytest.mark.hardware
def test_frames_own_their_memory(camera):
    """GetNDArray() views a buffer the SDK recycles at Release(). Without the
    copy, retained frames all alias whatever the camera wrote most recently --
    so held frames would converge to identical content."""
    frames = []
    camera.start_streaming(frames.append)
    time.sleep(1.5)
    camera.stop_streaming()

    assert len(frames) > 5
    held = frames[:5]
    distinct = {f.image.tobytes() for f in held}
    assert len(distinct) > 1, "retained frames are aliasing one recycled buffer"


@pytest.mark.hardware
def test_verify_settings_reads_the_camera_back(camera):
    checks = camera.verify_settings({"SensorShutterMode": "Global", "TriggerMode": "Off"})
    assert [c.node for c in checks] == ["SensorShutterMode", "TriggerMode"]
    assert all(c.passed for c in checks), [c.describe() for c in checks]


@pytest.mark.hardware
def test_unknown_serial_raises_camera_error():
    camera = SpinnakerCamera(serial="00000000")
    with pytest.raises(CameraError, match="no camera with serial"):
        camera.open()
    camera.close()  # must not leak the System reference

"""Checkpoint A6 core: RecordingSessionController orchestrates capture,
writing, trial state, and flag targeting for N cameras, with no Qt
dependency (acquisition/CLAUDE.md invariant 4)."""

from __future__ import annotations

import time

import pytest

from acquisition.capture_controller import CaptureController
from acquisition.mock_camera import MockCamera
from acquisition.recording_session import CameraRig, RecordingSessionController, hardware_fps
from acquisition.trial_state_machine import KeypressStopCondition, TrialPhase, TrialStateMachine, TrialToggleAction
from acquisition.writer import WriterError
from app.config import (
    CaptureConfig,
    EncoderConfig,
    StorageConfig,
    TrialTimingConfig,
)
from schema.timestamps import TimestampRow, read_timestamps_csv

FAST_TIMING = TrialTimingConfig(min_trial_duration_s=0.05, suspicious_duration_s=0.2, max_trial_duration_s=5.0)


class _FakeConfig:
    """Just the sub-configs RecordingSessionController actually reads."""

    def __init__(self, include_view_token: bool = False):
        self.capture = CaptureConfig(fps=100, width=16, height=16, queue_maxsize=200, preview_fps=15, preroll_buffer_s=0.1)
        self.encoder = EncoderConfig(codec="libx264", fallback_codec="libx264", crf=28, pixel_format="yuv420p")
        self.storage = StorageConfig(session_root="unused", min_free_gb=0, filename_include_view_token=include_view_token)


def _make_rig(name: str, config) -> CameraRig:
    camera = MockCamera(serial=f"mock-{name}", width=config.capture.width, height=config.capture.height, fps=config.capture.fps)
    controller = CaptureController(camera, preroll_duration_s=config.capture.preroll_buffer_s, fps=config.capture.fps)
    controller.start()
    return CameraRig(view_name=name, controller=controller)


def _make_controller(tmp_path, n_cameras=1, include_view_token=False, timing=FAST_TIMING):
    config = _FakeConfig(include_view_token=include_view_token)
    rigs = [_make_rig(f"cam{i}", config) for i in range(n_cameras)]
    state_machine = TrialStateMachine(config=timing, stop_condition=KeypressStopCondition(), clock=time.monotonic)
    controller = RecordingSessionController(
        session_dir=tmp_path,
        animal_id="R042",
        project_name="pdct-pilot",
        date="20260811",
        initials="WL",
        config=config,
        state_machine=state_machine,
        rigs=rigs,
    )
    return controller, rigs


def _teardown(rigs):
    for rig in rigs:
        rig.controller.stop()


@pytest.mark.requires_ffmpeg
def test_full_trial_lifecycle_writes_video_timestamps_and_trials_csv(tmp_path):
    controller, rigs = _make_controller(tmp_path)
    try:
        assert controller.toggle_trial() is TrialToggleAction.STARTED
        assert controller.phase is TrialPhase.RECORDING
        time.sleep(0.3)  # > min_trial_duration_s, > suspicious_duration_s
        assert controller.toggle_trial() is TrialToggleAction.STOPPED
        assert controller.phase is TrialPhase.IDLE

        records = controller.trial_records()
        assert len(records) == 1
        assert records[0].trial_number == 1
        assert records[0].n_frames > 0
        assert records[0].included is True

        assert (tmp_path / "trials.csv").exists()
        mp4_files = list(tmp_path.glob("*.mp4"))
        ts_files = list(tmp_path.glob("*_timestamps.csv"))
        assert len(mp4_files) == 1
        assert len(ts_files) == 1
        assert mp4_files[0].stat().st_size > 0
    finally:
        _teardown(rigs)


def test_min_duration_swallow_leaves_trial_recording(tmp_path):
    controller, rigs = _make_controller(tmp_path)
    try:
        controller.toggle_trial()  # start
        result = controller.toggle_trial()  # immediate second press: swallowed
        assert result is TrialToggleAction.SWALLOWED_MIN_DURATION
        assert controller.phase is TrialPhase.RECORDING
    finally:
        controller.toggle_trial()  # let cleanup close writers/files cleanly
        time.sleep(0.1)
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_multi_camera_writes_one_file_pair_per_camera(tmp_path):
    controller, rigs = _make_controller(tmp_path, n_cameras=2, include_view_token=True)
    try:
        controller.toggle_trial()
        time.sleep(0.3)
        controller.toggle_trial()

        mp4_files = sorted(p.name for p in tmp_path.glob("*.mp4"))
        assert len(mp4_files) == 2
        assert any("cam0" in name for name in mp4_files)
        assert any("cam1" in name for name in mp4_files)

        record = controller.trial_records()[0]
        assert record.n_frames > 0  # aggregated across both cameras
    finally:
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_flag_toggle_targets_current_recording_trial(tmp_path):
    controller, rigs = _make_controller(tmp_path)
    try:
        controller.toggle_trial()  # start trial 1
        controller.toggle_flag("fall")
        assert controller.active_flags(1) == frozenset({"fall"})

        time.sleep(0.3)
        controller.toggle_trial()  # stop

        record = controller.trial_records()[0]
        assert record.flags == frozenset({"fall"})
        assert record.included is False
    finally:
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_flag_toggle_targets_most_recent_completed_trial_after_stop(tmp_path):
    controller, rigs = _make_controller(tmp_path)
    try:
        controller.toggle_trial()
        time.sleep(0.3)
        controller.toggle_trial()  # trial 1 completed, IDLE

        assert controller.target_trial_number() == 1
        controller.toggle_flag("freeze")

        record = controller.trial_records()[0]
        assert record.flags == frozenset({"freeze"})
        # trials.csv re-persisted immediately (annotation is never blocking)
        assert (tmp_path / "trials.csv").read_text(encoding="utf-8").count("freeze") == 1
    finally:
        _teardown(rigs)


def test_flag_toggle_is_a_toggle_not_a_set(tmp_path):
    controller, rigs = _make_controller(tmp_path)
    try:
        controller.toggle_trial()
        controller.toggle_flag("fall")
        controller.toggle_flag("fall")  # toggled back off
        assert controller.active_flags(1) == frozenset()
    finally:
        controller.toggle_trial()
        time.sleep(0.1)
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_discard_last_removes_files_and_record(tmp_path):
    controller, rigs = _make_controller(tmp_path)
    try:
        controller.toggle_trial()
        time.sleep(0.3)
        controller.toggle_trial()

        mp4_before = list(tmp_path.glob("*.mp4"))
        assert len(mp4_before) == 1

        discarded = controller.discard_last()
        assert discarded == 1
        assert controller.trial_records() == []
        assert controller.current_trial_number == 0
        assert list(tmp_path.glob("*.mp4")) == []
        assert list(tmp_path.glob("*_timestamps.csv")) == []

        assert controller.discard_last() is None
    finally:
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_max_duration_auto_stop_via_tick_finalizes_the_trial(tmp_path):
    timing = TrialTimingConfig(min_trial_duration_s=0.05, suspicious_duration_s=0.1, max_trial_duration_s=0.2)
    controller, rigs = _make_controller(tmp_path, timing=timing)
    try:
        controller.toggle_trial()
        time.sleep(0.3)
        controller.tick()

        assert controller.phase is TrialPhase.IDLE
        records = controller.trial_records()
        assert len(records) == 1
        assert "max_duration_reached" in records[0].auto_flags
        assert (tmp_path / "trials.csv").exists()
        assert len(list(tmp_path.glob("*.mp4"))) == 1
    finally:
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_dropped_frame_count_aggregates_across_cameras(tmp_path):
    controller, rigs = _make_controller(tmp_path, n_cameras=2)
    try:
        assert controller.dropped_frame_count == 0  # nothing recording yet
        controller.toggle_trial()
        time.sleep(0.3)
        controller.toggle_trial()
        assert controller.dropped_frame_count >= 0  # aggregated, not per-camera-only
    finally:
        _teardown(rigs)


def test_hardware_fps_is_measured_on_the_camera_clock():
    period_ns = 33_333_333  # 30 fps
    rows = [TimestampRow(frame_index=i, hardware_timestamp_ns=i * period_ns, frame_id=i) for i in range(31)]
    assert hardware_fps(rows) == pytest.approx(30.0, rel=1e-6)
    # A dropped frame is one longer interval, so it lowers the achieved rate.
    assert hardware_fps(rows[:10] + rows[11:]) < 30.0
    assert hardware_fps(rows[:1]) == 0.0
    assert hardware_fps([]) == 0.0


@pytest.mark.requires_ffmpeg
def test_achieved_fps_is_not_inflated_by_the_preroll(tmp_path):
    """Pre-roll frames are in the file but precede the trial's start, so
    counting them against the trial's duration overstated achieved_fps --
    31.7 fps on a 35 s trial and 37.3 on an 8 s one, from a camera running at
    29.996. Analysis stage 1 checks achieved_fps against the nominal rate."""
    controller, rigs = _make_controller(tmp_path)
    try:
        time.sleep(0.2)  # fill the 0.1 s pre-roll
        controller.toggle_trial()
        time.sleep(0.3)
        controller.toggle_trial()

        record = controller.trial_records()[0]
        _, rows = read_timestamps_csv(next(tmp_path.glob("*_timestamps.csv")))
        assert record.achieved_fps == pytest.approx(hardware_fps(rows))
        # The old formula: every written frame over the trial's own duration.
        assert record.achieved_fps < record.n_frames / record.duration_s
    finally:
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_sidecar_frame_ids_are_contiguous_across_the_preroll_boundary(tmp_path):
    controller, rigs = _make_controller(tmp_path)
    try:
        time.sleep(0.2)  # fill the pre-roll so the file starts with it
        controller.toggle_trial()
        time.sleep(0.3)
        controller.toggle_trial()

        _, rows = read_timestamps_csv(next(tmp_path.glob("*_timestamps.csv")))
        ids = [r.frame_id for r in rows]
        assert len(ids) > rigs[0].controller.preroll.maxlen  # pre-roll plus live frames
        assert ids == list(range(ids[0], ids[0] + len(ids))), "gap or duplicate in frame IDs"
    finally:
        _teardown(rigs)


@pytest.mark.requires_ffmpeg
def test_one_camera_failing_does_not_cost_the_other_cameras_trial(tmp_path):
    controller, rigs = _make_controller(tmp_path, n_cameras=2, include_view_token=True)
    try:
        controller.toggle_trial()
        time.sleep(0.3)
        failing, healthy = rigs[0].writer, rigs[1].writer

        def fail() -> None:
            raise WriterError("simulated ffmpeg failure on cam0")

        failing.raise_if_failed = fail

        with pytest.raises(WriterError, match="cam0"):
            controller.toggle_trial()

        # The healthy camera was stopped and finalised, not left recording...
        assert not healthy.is_alive()
        assert all(rig.writer is None for rig in rigs)
        assert len(list(tmp_path.glob("*_timestamps.csv"))) == 2
        # ...and the trial is on record despite the failure.
        assert [r.trial_number for r in controller.trial_records()] == [1]
        assert (tmp_path / "trials.csv").exists()
    finally:
        _teardown(rigs)

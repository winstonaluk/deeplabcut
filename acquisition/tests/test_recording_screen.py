"""Checkpoint A6 GUI shell: spacebar control, reason-code hotkeys, visual
flag feedback, preview tiles -- thin rendering over RecordingSessionController."""

from __future__ import annotations

import time

import pytest

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from acquisition.capture_controller import CaptureController
from acquisition.mock_camera import MockCamera
from acquisition.recording_session import CameraRig, RecordingSessionController
from acquisition.trial_state_machine import KeypressStopCondition, TrialPhase, TrialStateMachine
from app.config import CaptureConfig, EncoderConfig, StorageConfig, TrialTimingConfig
from gui.recording_screen import _CHIP_ACTIVE, _CHIP_INACTIVE, RecordingScreen
from paradigms.paradigm import ReasonCode

FAST_TIMING = TrialTimingConfig(min_trial_duration_s=0.05, suspicious_duration_s=0.2, max_trial_duration_s=5.0)
REASON_CODES = (
    ReasonCode(key="F", code="fall", label="Fell from the pole"),
    ReasonCode(key="Z", code="freeze", label="Froze partway down"),
)


class _FakeConfig:
    def __init__(self):
        self.capture = CaptureConfig(fps=100, width=16, height=16, queue_maxsize=200, preview_fps=15, preroll_buffer_s=0.1)
        self.encoder = EncoderConfig(codec="libx264", fallback_codec="libx264", crf=28, pixel_format="yuv420p")
        self.storage = StorageConfig(session_root="unused", min_free_gb=0, filename_include_view_token=False)


def _make_screen(tmp_path):
    config = _FakeConfig()
    camera = MockCamera(serial="mock-1", width=config.capture.width, height=config.capture.height, fps=config.capture.fps)
    cam_controller = CaptureController(camera, preroll_duration_s=0.1, fps=config.capture.fps)
    cam_controller.start()
    rig = CameraRig(view_name="cam0", controller=cam_controller)

    state_machine = TrialStateMachine(config=FAST_TIMING, stop_condition=KeypressStopCondition(), clock=time.monotonic)
    session = RecordingSessionController(
        session_dir=tmp_path, animal_id="R042", project_name="pdct-pilot", date="20260811",
        initials="WL", config=config, state_machine=state_machine, rigs=[rig],
    )
    screen = RecordingScreen(session, REASON_CODES, preview_fps=15)
    return screen, session, [rig]


def _key_event(key, text="", modifiers=Qt.KeyboardModifier.NoModifier):
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)


def test_preview_tile_created_per_camera_rig(qapp, tmp_path):
    screen, session, rigs = _make_screen(tmp_path)
    try:
        assert len(screen.preview_labels) == 1
    finally:
        for rig in rigs:
            rig.controller.stop()


@pytest.mark.requires_ffmpeg
def test_spacebar_starts_and_stops_a_trial(qapp, tmp_path):
    screen, session, rigs = _make_screen(tmp_path)
    try:
        screen.keyPressEvent(_key_event(Qt.Key.Key_Space))
        assert session.phase is TrialPhase.RECORDING
        assert screen.state_label.text() == "RECORDING"
        assert screen.trial_counter_label.text() == "Trial 1"

        time.sleep(0.3)
        screen.keyPressEvent(_key_event(Qt.Key.Key_Space))
        assert session.phase is TrialPhase.IDLE
        assert screen.state_label.text() == "IDLE"
    finally:
        for rig in rigs:
            rig.controller.stop()


def test_reason_code_hotkey_toggles_flag_and_chip_style(qapp, tmp_path):
    screen, session, rigs = _make_screen(tmp_path)
    try:
        screen.keyPressEvent(_key_event(Qt.Key.Key_Space))  # start trial 1

        screen.keyPressEvent(_key_event(Qt.Key.Key_F, text="F"))
        assert session.active_flags(1) == frozenset({"fall"})
        assert screen.flag_chips["fall"].styleSheet() == _CHIP_ACTIVE
        assert screen.flag_chips["freeze"].styleSheet() == _CHIP_INACTIVE

        screen.keyPressEvent(_key_event(Qt.Key.Key_F, text="F"))  # toggle off
        assert session.active_flags(1) == frozenset()
        assert screen.flag_chips["fall"].styleSheet() == _CHIP_INACTIVE
    finally:
        screen.keyPressEvent(_key_event(Qt.Key.Key_Space))
        time.sleep(0.1)
        for rig in rigs:
            rig.controller.stop()


@pytest.mark.requires_ffmpeg
def test_ctrl_delete_discards_last_trial(qapp, tmp_path):
    screen, session, rigs = _make_screen(tmp_path)
    try:
        screen.keyPressEvent(_key_event(Qt.Key.Key_Space))
        time.sleep(0.3)
        screen.keyPressEvent(_key_event(Qt.Key.Key_Space))
        assert len(session.trial_records()) == 1

        screen.keyPressEvent(
            _key_event(Qt.Key.Key_Delete, modifiers=Qt.KeyboardModifier.ControlModifier)
        )
        assert session.trial_records() == []
        assert screen.trial_counter_label.text() == "Trial 0"
    finally:
        for rig in rigs:
            rig.controller.stop()


def test_dropped_frames_readout_updates_via_timer_tick(qapp, tmp_path):
    screen, session, rigs = _make_screen(tmp_path)
    try:
        assert screen.dropped_frames_label.text() == "Dropped: 0"
        screen._on_timer()  # simulate one timer tick without waiting for the real QTimer
        assert screen.dropped_frames_label.text().startswith("Dropped:")
    finally:
        for rig in rigs:
            rig.controller.stop()

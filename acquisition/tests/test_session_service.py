"""Checkpoint A12: the composition root runs a whole session with no UI.

These tests are the done-criteria for A12 -- every one drives SessionService
against MockCamera, with no hardware, no display and no HTTP layer, and
asserts on what actually landed on disk.

The load-bearing one is test_max_duration_auto_stops_with_nobody_ticking:
under the retired Qt screen the trial-duration guard was driven by a UI timer,
so it silently stopped working whenever the UI did. It now lives in a daemon
thread this service owns.
"""

from __future__ import annotations

import dataclasses
import time
from pathlib import Path

import pytest

from acquisition.camera_backend import CameraError
from acquisition.camera_registry import CAMERA_BACKENDS
from acquisition.mock_camera import MockCamera
from acquisition.trial_state_machine import TrialToggleAction
from app.config import ConfigError, load_config
from app.session_service import PreflightFailed, SessionError, SessionService
from schema.session_metadata import SessionMetadata
from schema.timestamps import read_timestamps_csv
from schema.trials import read_trials_csv

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"

TRIAL_S = 0.4
WAIT_S = 15.0


def _config(tmp_path, **overrides):
    """The real config.toml, shrunk to test speed.

    Deliberately built from the shipped file rather than a fake: a key added
    to config.toml without a matching loader change fails here too.
    """
    base = load_config(CONFIG_PATH)
    config = dataclasses.replace(
        base,
        cameras=tuple(dataclasses.replace(c, type="mock") for c in base.cameras),
        capture=dataclasses.replace(
            base.capture, fps=50, width=32, height=32, preroll_buffer_s=0.1, queue_maxsize=400
        ),
        encoder=dataclasses.replace(
            base.encoder, codec="libx264", fallback_codec="libx264", crf=30
        ),
        trial_timing=dataclasses.replace(
            base.trial_timing,
            min_trial_duration_s=0.05,
            suspicious_duration_s=0.1,
            max_trial_duration_s=5.0,
        ),
        storage=dataclasses.replace(base.storage, session_root=str(tmp_path), min_free_gb=0),
    )
    return dataclasses.replace(config, **overrides) if overrides else config


@pytest.fixture
def service(tmp_path):
    svc = SessionService(_config(tmp_path), tick_interval_s=0.02)
    yield svc
    svc.end_session()


def _start(service):
    config = service.config
    return service.start_session(
        animal_id="R042",
        project_name=config.metadata.projects[0],
        experimenter_initials=config.metadata.experimenter_initials[0],
        date="20260915",
    )


def _wait_until(predicate, timeout=WAIT_S):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


# -- preflight and validation (no FFmpeg needed) -----------------------------


def test_preflight_passes_against_the_mock_and_reports_every_check(service):
    result = service.preflight()

    assert result.passed, result.failures
    names = {c.name for c in result.checks}
    assert "Camera detected" in names
    assert "FFmpeg available" in names
    assert "Free disk space" in names


def test_preflight_blocks_the_session_when_the_camera_disagrees_with_config(
    tmp_path, monkeypatch
):
    # A camera that reports a different width than [capture] claims. Editing
    # the config alone proves nothing, because MockCamera is *built from*
    # [capture] and would simply move with it -- the two have to be able to
    # disagree for the check to mean anything. This is the silent-shearing
    # failure described in acquisition/CLAUDE.md "Preflight checks".
    monkeypatch.setitem(
        CAMERA_BACKENDS,
        "mock",
        lambda cam, cap: MockCamera(
            serial=cam.serial, width=cap.width + 32, height=cap.height, fps=float(cap.fps)
        ),
    )
    svc = SessionService(_config(tmp_path), tick_interval_s=0.02)
    try:
        with pytest.raises(PreflightFailed):
            _start(svc)
        assert not list(tmp_path.iterdir()), "no session directory on a blocked start"
    finally:
        svc.end_session()


@pytest.mark.parametrize(
    "field,value",
    [
        ("animal_id", "bad id!"),
        ("project_name", "not-a-project"),
        ("experimenter_initials", "ZZ"),
    ],
)
def test_session_metadata_is_validated_before_anything_is_created(service, field, value):
    config = service.config
    kwargs = {
        "animal_id": "R042",
        "project_name": config.metadata.projects[0],
        "experimenter_initials": config.metadata.experimenter_initials[0],
        field: value,
    }
    with pytest.raises(SessionError):
        service.start_session(**kwargs)


def test_unknown_camera_type_is_a_config_error(tmp_path):
    config = _config(tmp_path)
    config = dataclasses.replace(
        config, cameras=tuple(dataclasses.replace(c, type="nope") for c in config.cameras)
    )
    with pytest.raises(ConfigError):
        SessionService(config).preflight()


def test_a_camera_that_fails_to_start_leaves_no_session_directory(tmp_path, monkeypatch):
    class _FailingCamera(MockCamera):
        def start_streaming(self, on_frame):
            raise CameraError("simulated stream failure")

    monkeypatch.setitem(
        CAMERA_BACKENDS,
        "mock",
        lambda cam, cap: _FailingCamera(
            serial=cam.serial, width=cap.width, height=cap.height, fps=float(cap.fps)
        ),
    )
    svc = SessionService(_config(tmp_path), tick_interval_s=0.02)
    try:
        with pytest.raises(CameraError):
            _start(svc)
        assert not list(tmp_path.iterdir())
    finally:
        svc.end_session()


def test_toggle_flag_rejects_a_code_that_is_not_in_the_keymap(service):
    _start(service)
    with pytest.raises(SessionError):
        service.toggle_flag("not_a_reason_code")


def test_trial_control_before_start_is_an_error(service):
    with pytest.raises(SessionError):
        service.toggle_trial()


# -- full session (needs FFmpeg) ---------------------------------------------


@pytest.mark.requires_ffmpeg
def test_full_session_writes_every_artifact_and_they_validate(service):
    session_dir = _start(service)

    assert service.toggle_trial() is TrialToggleAction.STARTED
    time.sleep(TRIAL_S)
    service.toggle_flag("fall")
    assert service.toggle_trial() is TrialToggleAction.STOPPED

    service.end_session()

    metadata = SessionMetadata.read_json(session_dir / "session_metadata.json")
    assert metadata.animal_id == "R042"
    assert metadata.rig_id == service.config.rig_id
    assert metadata.ffmpeg_encoder == "libx264"
    assert len(metadata.cameras) == len(service.config.cameras)
    assert metadata.cameras[0].user_set_verified is True

    version, records = read_trials_csv(session_dir / "trials.csv")
    assert version == 1
    assert len(records) == 1
    record = records[0]
    assert record.trial_number == 1
    assert record.flags == frozenset({"fall"})
    assert record.included is False  # a flagged trial is excluded
    assert record.n_frames > 0
    assert record.achieved_fps > 0

    videos = sorted(session_dir.glob("*.mp4"))
    sidecars = sorted(session_dir.glob("*_timestamps.csv"))
    assert len(videos) == len(sidecars) == len(service.config.cameras)
    assert videos[0].stat().st_size > 0

    _, rows = read_timestamps_csv(sidecars[0])
    assert len(rows) == record.n_frames
    assert [r.frame_index for r in rows] == list(range(len(rows)))
    assert all(b.frame_id == a.frame_id + 1 for a, b in zip(rows, rows[1:]))
    assert (session_dir / "session.log").exists()


@pytest.mark.requires_ffmpeg
def test_max_duration_auto_stops_with_nobody_ticking(tmp_path):
    """The guard the Qt timer used to own. Nothing here calls tick()."""
    config = _config(tmp_path)
    config = dataclasses.replace(
        config, trial_timing=dataclasses.replace(config.trial_timing, max_trial_duration_s=0.5)
    )
    svc = SessionService(config, tick_interval_s=0.02)
    try:
        _start(svc)
        svc.toggle_trial()

        assert _wait_until(lambda: svc.state().phase == "idle"), "trial never auto-stopped"

        records = svc.trial_records()
        assert len(records) == 1
        assert "max_duration_reached" in records[0].auto_flags
    finally:
        svc.end_session()


@pytest.mark.requires_ffmpeg
def test_discard_last_removes_the_trial_and_its_files(service):
    session_dir = _start(service)

    service.toggle_trial()
    time.sleep(TRIAL_S)
    service.toggle_trial()
    assert sorted(session_dir.glob("*.mp4"))

    assert service.discard_last() == 1

    assert not sorted(session_dir.glob("*.mp4"))
    assert not sorted(session_dir.glob("*_timestamps.csv"))
    _, records = read_trials_csv(session_dir / "trials.csv")
    assert records == []
    assert service.state().trial_number == 0


@pytest.mark.requires_ffmpeg
def test_state_tracks_the_session_through_its_phases(service):
    assert service.state().phase == "setup"

    _start(service)
    state = service.state()
    assert state.phase == "idle"
    assert state.animal_id == "R042"
    assert state.session_dir is not None
    assert len(state.cameras) == len(service.config.cameras)
    assert state.cameras[0].width == 32

    service.toggle_trial()
    assert service.state().phase == "recording"
    assert _wait_until(lambda: service.state().elapsed_s > 0)
    time.sleep(TRIAL_S)
    service.toggle_trial()

    state = service.state()
    assert state.phase == "idle"
    assert state.completed_trials == 1
    assert state.free_gb > 0

    service.end_session()
    assert service.state().phase == "closed"

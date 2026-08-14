"""Checkpoint A1: interfaces exist with full signatures and no implementation
bodies. These tests are structural -- behavior lands in A2/A3."""

import pytest

from acquisition.camera_backend import CameraBackend
from acquisition.trial_state_machine import (
    KeypressStopCondition,
    TrialPhase,
    TrialStateMachine,
    TrialStopCondition,
)
from app.config import TrialTimingConfig
from paradigms.paradigm import Paradigm, ReasonCode
from paradigms.pdct import PDCTParadigm
from pose.null_pose_provider import NullPoseProvider
from pose.pose_provider import PoseProvider
from pose.trigger_service import TriggerService


def test_camera_backend_is_abstract():
    with pytest.raises(TypeError):
        CameraBackend()  # type: ignore[abstract]


def test_paradigm_is_abstract():
    with pytest.raises(TypeError):
        Paradigm()  # type: ignore[abstract]


def test_trial_stop_condition_is_abstract():
    with pytest.raises(TypeError):
        TrialStopCondition()  # type: ignore[abstract]


def test_null_pose_provider_satisfies_protocol_and_returns_none():
    provider: PoseProvider = NullPoseProvider()
    assert provider.infer(frame=None) is None  # type: ignore[arg-type]


def test_trigger_service_on_pose_is_a_noop():
    assert TriggerService().on_pose(None) is None


def test_pdct_paradigm_exposes_reason_codes_from_config():
    keymap = {"F": "fall", "Z": "freeze"}
    labels = {"fall": "Fell from the pole", "freeze": "Froze partway down"}
    paradigm = PDCTParadigm(keymap=keymap, reason_code_labels=labels)

    assert paradigm.name == "pdct"
    assert set(paradigm.reason_codes) == {
        ReasonCode(key="F", code="fall", label="Fell from the pole"),
        ReasonCode(key="Z", code="freeze", label="Froze partway down"),
    }
    assert isinstance(paradigm.default_stop_condition(), KeypressStopCondition)


def test_keypress_stop_condition_flag_semantics():
    condition = KeypressStopCondition()
    assert condition.should_stop() is False
    condition.signal_stop()
    assert condition.should_stop() is True
    condition.reset()
    assert condition.should_stop() is False


def test_trial_state_machine_starts_idle():
    config = TrialTimingConfig(min_trial_duration_s=5, suspicious_duration_s=30, max_trial_duration_s=600)
    machine = TrialStateMachine(config=config, stop_condition=KeypressStopCondition(), clock=lambda: 0.0)

    assert machine.phase is TrialPhase.IDLE
    assert machine.current_trial_number == 0
    # Guard behavior (min-duration swallow, max-duration auto-stop,
    # suspicious-short auto-flag, discard-last) is covered in depth by
    # test_trial_state_machine.py (checkpoint A3).

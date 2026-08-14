"""Checkpoint A3: min-duration swallow, max-duration auto-stop,
suspicious-short auto-flag, discard-last, pluggable stop condition."""

from __future__ import annotations

import pytest

from acquisition.trial_state_machine import (
    TrialPhase,
    TrialStateMachine,
    TrialStopCondition,
    TrialToggleAction,
)
from app.config import TrialTimingConfig

CONFIG = TrialTimingConfig(min_trial_duration_s=5, suspicious_duration_s=30, max_trial_duration_s=600)


class FakeClock:
    """Deterministic clock so guard boundaries can be tested exactly."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class ManualStopCondition(TrialStopCondition):
    def __init__(self) -> None:
        self._stop = False

    def should_stop(self) -> bool:
        return self._stop

    def set(self, value: bool) -> None:
        self._stop = value


def _machine(config: TrialTimingConfig = CONFIG, stop_condition=None, clock=None):
    clock = clock or FakeClock()
    stop_condition = stop_condition or ManualStopCondition()
    return TrialStateMachine(config=config, stop_condition=stop_condition, clock=clock), clock, stop_condition


def test_spacebar_starts_a_trial_from_idle():
    machine, clock, _ = _machine()

    result = machine.request_toggle()

    assert result.action is TrialToggleAction.STARTED
    assert result.trial_number == 1
    assert machine.phase is TrialPhase.RECORDING
    assert machine.current_trial_number == 1


def test_spacebar_within_min_duration_is_swallowed():
    machine, clock, _ = _machine()
    machine.request_toggle()  # start

    clock.advance(4.999)
    result = machine.request_toggle()

    assert result.action is TrialToggleAction.SWALLOWED_MIN_DURATION
    assert machine.phase is TrialPhase.RECORDING  # still recording


def test_spacebar_after_min_duration_stops_the_trial():
    machine, clock, _ = _machine()
    machine.request_toggle()  # start

    clock.advance(5.0)  # exactly at the boundary counts as elapsed
    result = machine.request_toggle()

    assert result.action is TrialToggleAction.STOPPED
    assert machine.phase is TrialPhase.IDLE


def test_short_trial_gets_suspiciously_short_auto_flag():
    machine, clock, _ = _machine()
    machine.request_toggle()  # start
    clock.advance(10.0)  # > min, < suspicious
    machine.request_toggle()  # stop

    outcome = machine.discard_last()
    assert outcome is not None
    assert outcome.duration_s == pytest.approx(10.0)
    assert outcome.auto_flags == frozenset({"suspiciously_short"})


def test_normal_trial_gets_no_auto_flags():
    machine, clock, _ = _machine()
    machine.request_toggle()  # start
    clock.advance(45.0)  # > suspicious_duration_s
    machine.request_toggle()  # stop

    outcome = machine.discard_last()
    assert outcome is not None
    assert outcome.auto_flags == frozenset()


def test_max_duration_auto_stops_via_tick():
    machine, clock, _ = _machine()
    machine.request_toggle()  # start

    clock.advance(600.0)
    machine.tick()

    assert machine.phase is TrialPhase.IDLE
    outcome = machine.discard_last()
    assert outcome is not None
    assert outcome.duration_s == pytest.approx(600.0)
    assert "max_duration_reached" in outcome.auto_flags


def test_tick_is_a_noop_while_idle():
    machine, clock, _ = _machine()
    machine.tick()  # must not raise
    assert machine.phase is TrialPhase.IDLE


def test_tick_is_a_noop_before_any_threshold():
    machine, clock, _ = _machine()
    machine.request_toggle()  # start
    clock.advance(1.0)
    machine.tick()
    assert machine.phase is TrialPhase.RECORDING


def test_stop_condition_triggers_auto_stop_via_tick_after_min_duration():
    machine, clock, stop_condition = _machine()
    machine.request_toggle()  # start
    clock.advance(1.0)
    stop_condition.set(True)
    machine.tick()
    assert machine.phase is TrialPhase.RECORDING  # still within min duration -- swallowed

    clock.advance(4.5)  # now past 5s min duration
    machine.tick()
    assert machine.phase is TrialPhase.IDLE


def test_discard_last_decrements_counter_and_clears_outcome():
    machine, clock, _ = _machine()
    machine.request_toggle()
    clock.advance(45.0)
    machine.request_toggle()
    assert machine.current_trial_number == 1

    outcome = machine.discard_last()
    assert outcome is not None
    assert outcome.trial_number == 1
    assert machine.current_trial_number == 0

    assert machine.discard_last() is None  # nothing left to discard


def test_discard_last_returns_none_when_nothing_completed():
    machine, clock, _ = _machine()
    assert machine.discard_last() is None

    machine.request_toggle()  # still recording, nothing completed yet
    assert machine.discard_last() is None

"""IDLE -> RECORDING -> IDLE trial state machine.

Guards: min-duration swallow, suspicious-short auto-flag, max-duration
auto-stop, discard-last (acquisition/CLAUDE.md "Trial state machine").

Stop condition is a pluggable predicate (invariant 8) so a future pose-driven
paradigm can replace ``KeypressStopCondition`` without the GUI's spacebar
handler changing at all -- the handler only ever calls
``TrialStateMachine.request_toggle()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from app.config import TrialTimingConfig


class TrialPhase(Enum):
    IDLE = "idle"
    RECORDING = "recording"


class TrialToggleAction(Enum):
    """What ``request_toggle()`` actually did, so the GUI can react (e.g. show
    the min-duration countdown when a press is swallowed)."""

    STARTED = "started"
    STOPPED = "stopped"
    SWALLOWED_MIN_DURATION = "swallowed_min_duration"


@dataclass(frozen=True)
class TrialToggleResult:
    action: TrialToggleAction
    trial_number: int | None


@dataclass(frozen=True)
class TrialOutcome:
    """A completed trial's timing and auto-applied flags.

    Experimenter-assigned flags (fall, freeze, ...) are tracked separately by
    the annotation/flag-targeting component, not here -- this is timing only.
    """

    trial_number: int
    start_time: float  # monotonic seconds, from the injected clock
    duration_s: float
    auto_flags: frozenset[str]


class TrialStopCondition(ABC):
    """Pluggable predicate consulted by ``TrialStateMachine.tick()`` to decide
    whether a RECORDING trial should end on its own (distinct from an
    experimenter-initiated spacebar stop).

    Concrete strategies: ``KeypressStopCondition`` (A3, external signal set by
    the Qt spacebar handler) and a future pose-driven condition. Never embed
    stop logic directly in a Qt event handler -- route through this interface.
    """

    @abstractmethod
    def should_stop(self) -> bool: ...


class KeypressStopCondition(TrialStopCondition):
    """The PDCT default: stops only when externally signalled.

    The Qt spacebar handler calls ``signal_stop()``; it never decides
    start/stop policy itself, only relays the keypress (invariant 8). This
    class holds no timing logic -- it is a flag, not a guard.
    """

    def __init__(self) -> None:
        self._signalled = False

    def signal_stop(self) -> None:
        self._signalled = True

    def should_stop(self) -> bool:
        return self._signalled

    def reset(self) -> None:
        self._signalled = False


class TrialStateMachine:
    """Owns trial phase and timing guards for one paradigm's trials.

    Not itself a Qt object -- the GUI calls ``request_toggle()`` from the
    spacebar handler and ``tick()`` from a periodic timer, and renders
    ``phase`` / elapsed time / flags. Recording integrity (invariant 4) means
    this class never touches the capture/writer pipeline directly; it only
    signals start/stop and the caller wires that to capture control.
    """

    def __init__(
        self,
        config: TrialTimingConfig,
        stop_condition: TrialStopCondition,
        clock: Callable[[], float],
    ) -> None:
        self._config = config
        self._stop_condition = stop_condition
        self._clock = clock
        self._phase = TrialPhase.IDLE
        self._trial_number = 0
        self._trial_start_time: float | None = None
        self._last_outcome: TrialOutcome | None = None

    @property
    def phase(self) -> TrialPhase:
        return self._phase

    @property
    def current_trial_number(self) -> int:
        return self._trial_number

    @property
    def elapsed_s(self) -> float:
        """Seconds since the current trial started; 0.0 while IDLE."""
        if self._phase is not TrialPhase.RECORDING:
            return 0.0
        return self._elapsed()

    @property
    def last_outcome(self) -> TrialOutcome | None:
        """Non-destructive peek at the most recently completed trial's
        outcome -- unlike discard_last(), does not clear it. Used by the
        recording orchestration layer (A6) to build the persisted
        TrialRecord right after a trial ends."""
        return self._last_outcome

    def request_toggle(self) -> TrialToggleResult:
        """Spacebar handler entry point. Starts a trial from IDLE, stops one
        from RECORDING -- unless within ``min_trial_duration_s`` of trial
        start, in which case the press is swallowed entirely.
        """
        if self._phase is TrialPhase.IDLE:
            self._trial_number += 1
            self._trial_start_time = self._clock()
            self._phase = TrialPhase.RECORDING
            return TrialToggleResult(TrialToggleAction.STARTED, self._trial_number)

        elapsed = self._elapsed()
        if elapsed < self._config.min_trial_duration_s:
            return TrialToggleResult(TrialToggleAction.SWALLOWED_MIN_DURATION, self._trial_number)

        self._finalize_trial(extra_auto_flags=frozenset())
        return TrialToggleResult(TrialToggleAction.STOPPED, self._trial_number)

    def tick(self) -> None:
        """Periodic check (e.g. a Qt timer) for max-duration auto-stop and
        stop_condition.should_stop(). No-op outside RECORDING.

        # TODO(QUESTIONS.md): trial-state-machine-min-duration-vs-predicate
        A predicate-triggered stop is still subject to min_trial_duration_s,
        same as a manual spacebar stop -- most conservative reading, since
        CLAUDE.md ties the guard to "double-tap zero-length trials" without
        saying whether it should also gate a future pose-driven stop.
        """
        if self._phase is not TrialPhase.RECORDING:
            return

        elapsed = self._elapsed()
        if elapsed >= self._config.max_trial_duration_s:
            self._finalize_trial(extra_auto_flags=frozenset({"max_duration_reached"}))
            return

        if elapsed >= self._config.min_trial_duration_s and self._stop_condition.should_stop():
            self._finalize_trial(extra_auto_flags=frozenset())

    def discard_last(self) -> TrialOutcome | None:
        """Ctrl+Delete handler: discards the last completed trial after
        confirmation is handled by the caller. Decrements the trial counter.

        Only removes this state machine's bookkeeping (the outcome record and
        the counter) -- deleting the video/sidecar/metadata files is the
        caller's job (storage layer), keeping recording integrity independent
        of this class (invariant 4).
        """
        if self._last_outcome is None:
            return None
        outcome = self._last_outcome
        self._last_outcome = None
        self._trial_number -= 1
        return outcome

    def _elapsed(self) -> float:
        assert self._trial_start_time is not None
        return self._clock() - self._trial_start_time

    def _finalize_trial(self, extra_auto_flags: frozenset[str]) -> TrialOutcome:
        duration = self._elapsed()
        auto_flags = set(extra_auto_flags)
        if duration < self._config.suspicious_duration_s:
            auto_flags.add("suspiciously_short")
        outcome = TrialOutcome(
            trial_number=self._trial_number,
            start_time=self._trial_start_time,  # type: ignore[arg-type]
            duration_s=duration,
            auto_flags=frozenset(auto_flags),
        )
        self._last_outcome = outcome
        self._phase = TrialPhase.IDLE
        self._trial_start_time = None
        return outcome

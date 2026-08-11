"""IDLE -> RECORDING -> IDLE trial state machine.

Guards (min-duration swallow, suspicious-short auto-flag, max-duration
auto-stop) are implemented at checkpoint A3. This module defines the shape
only: phases, the stop-condition seam, and the controller's public API.

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

    def request_toggle(self) -> TrialToggleResult:
        """Spacebar handler entry point. Starts a trial from IDLE, stops one
        from RECORDING -- unless within ``min_trial_duration_s`` of trial
        start, in which case the press is swallowed entirely (A3).
        """
        raise NotImplementedError("state machine guards implemented at checkpoint A3")

    def tick(self) -> None:
        """Periodic check for max-duration auto-stop and stop_condition.should_stop() (A3)."""
        raise NotImplementedError("state machine guards implemented at checkpoint A3")

    def discard_last(self) -> TrialOutcome | None:
        """Ctrl+Delete handler: discards the last completed trial after
        confirmation is handled by the caller. Decrements the trial counter (A3).
        """
        raise NotImplementedError("discard-last implemented at checkpoint A3")

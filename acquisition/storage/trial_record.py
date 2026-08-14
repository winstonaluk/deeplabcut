"""Bridges TrialStateMachine's TrialOutcome (monotonic timing, no wall-clock
knowledge) to the schema's TrialRecord (ISO start time, experimenter flags).

The caller captures wall-clock time itself at the moment it observes
``TrialToggleAction.STARTED`` -- TrialStateMachine deliberately only knows
about the injected monotonic clock (acquisition/CLAUDE.md invariant 9 doesn't
require this, but mixing wall-clock and monotonic time inside one guard
class is a classic source of drift bugs, so the split is kept explicit here).
"""

from __future__ import annotations

from datetime import datetime

from acquisition.trial_state_machine import TrialOutcome
from schema.trials import TrialRecord


def build_trial_record(
    outcome: TrialOutcome,
    wall_clock_start: datetime,
    flags: frozenset[str],
    note: str,
    n_frames: int,
    dropped_frames: int,
    achieved_fps: float,
) -> TrialRecord:
    return TrialRecord(
        trial_number=outcome.trial_number,
        start_time=wall_clock_start.isoformat(),
        duration_s=outcome.duration_s,
        flags=flags,
        auto_flags=outcome.auto_flags,
        note=note,
        n_frames=n_frames,
        dropped_frames=dropped_frames,
        achieved_fps=achieved_fps,
    )

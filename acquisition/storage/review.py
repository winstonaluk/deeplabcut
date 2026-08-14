"""Loads a completed session's trials.csv for review: flag editing, note
entry, and other_invalid reason assignment (the note field is where the
specific reason goes -- there's no separate structured field for it).

Every edit re-persists trials.csv immediately, same as the recording
screen's live annotation (acquisition/CLAUDE.md "Annotation is subtractive
and never blocking").
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from schema.trials import TrialRecord, read_trials_csv, write_trials_csv


class ReviewSessionController:
    def __init__(self, session_dir: Path) -> None:
        self._trials_csv_path = Path(session_dir) / "trials.csv"
        _, records = read_trials_csv(self._trials_csv_path)
        self._records: dict[int, TrialRecord] = {r.trial_number: r for r in records}

    def trial_records(self) -> list[TrialRecord]:
        return [self._records[n] for n in sorted(self._records)]

    def toggle_flag(self, trial_number: int, reason_code: str) -> None:
        record = self._records[trial_number]
        flags = set(record.flags)
        flags.symmetric_difference_update({reason_code})
        self._records[trial_number] = replace(record, flags=frozenset(flags))
        self._persist()

    def set_note(self, trial_number: int, note: str) -> None:
        record = self._records[trial_number]
        self._records[trial_number] = replace(record, note=note)
        self._persist()

    def _persist(self) -> None:
        write_trials_csv(self._trials_csv_path, self.trial_records())

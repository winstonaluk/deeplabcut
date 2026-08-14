"""``trials.csv`` — one row per trial, the machine-readable valid/invalid table.

Plain CSV (not JSON) so downstream analysis can filter the training-frame pool
on flags without a JSON parser. The schema_version travels as a leading
``#schema_version=N`` comment line, which both ``csv.DictReader`` and
``pandas.read_csv(comment="#")`` tolerate.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from schema.errors import SchemaValidationError, SchemaVersionError

TRIALS_SCHEMA_VERSION = 1

_FIELDNAMES = [
    "trial_number",
    "start_time",
    "duration_s",
    "flags",
    "auto_flags",
    "note",
    "n_frames",
    "dropped_frames",
    "achieved_fps",
]


@dataclass(frozen=True)
class TrialRecord:
    """One trial's outcome: identity, timing, flags, and capture stats."""

    trial_number: int
    start_time: str  # ISO 8601
    duration_s: float
    flags: frozenset[str] = field(default_factory=frozenset)
    auto_flags: frozenset[str] = field(default_factory=frozenset)
    note: str = ""
    n_frames: int = 0
    dropped_frames: int = 0
    achieved_fps: float = 0.0

    @property
    def included(self) -> bool:
        """Valid by default; only experimenter flags make a trial invalid.

        auto_flags (e.g. suspiciously_short) are informational and do not by
        themselves exclude a trial -- see acquisition/CLAUDE.md trial state
        machine table and analysis/CLAUDE.md stage 1 qc_gate rules.
        """
        return len(self.flags) == 0

    def to_row(self) -> dict[str, Any]:
        return {
            "trial_number": self.trial_number,
            "start_time": self.start_time,
            "duration_s": self.duration_s,
            "flags": ";".join(sorted(self.flags)),
            "auto_flags": ";".join(sorted(self.auto_flags)),
            "note": self.note,
            "n_frames": self.n_frames,
            "dropped_frames": self.dropped_frames,
            "achieved_fps": self.achieved_fps,
        }

    @staticmethod
    def from_row(row: dict[str, Any]) -> "TrialRecord":
        missing = set(_FIELDNAMES) - row.keys()
        if missing:
            raise SchemaValidationError(f"trials.csv row missing fields: {sorted(missing)}")
        return TrialRecord(
            trial_number=int(row["trial_number"]),
            start_time=str(row["start_time"]),
            duration_s=float(row["duration_s"]),
            flags=frozenset(f for f in row["flags"].split(";") if f),
            auto_flags=frozenset(f for f in row["auto_flags"].split(";") if f),
            note=str(row["note"]),
            n_frames=int(row["n_frames"]),
            dropped_frames=int(row["dropped_frames"]),
            achieved_fps=float(row["achieved_fps"]),
        )


def write_trials_csv(
    path: Path,
    records: list[TrialRecord],
    schema_version: int = TRIALS_SCHEMA_VERSION,
) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        fh.write(f"#schema_version={schema_version}\n")
        writer = csv.DictWriter(fh, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_row())


def read_trials_csv(path: Path) -> tuple[int, list[TrialRecord]]:
    path = Path(path)
    with path.open("r", newline="", encoding="utf-8") as fh:
        first_line = fh.readline()
        if not first_line.startswith("#schema_version="):
            raise SchemaValidationError(
                f"trials.csv: expected leading #schema_version= comment, got {first_line!r}"
            )
        found_version = int(first_line.strip().split("=", 1)[1])
        if found_version != TRIALS_SCHEMA_VERSION:
            raise SchemaVersionError("trials.csv", found_version, TRIALS_SCHEMA_VERSION)
        reader = csv.DictReader(fh)
        records = [TrialRecord.from_row(row) for row in reader]
    return found_version, records

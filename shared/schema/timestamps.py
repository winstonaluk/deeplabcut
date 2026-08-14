"""Per-trial timestamp sidecar CSV — hardware chunk-data timestamps and frame IDs.

Per acquisition/CLAUDE.md invariant 6: hardware timestamps only, never host
wall-clock arrival time. One sidecar per trial video, same base filename with
a ``_timestamps`` suffix (see acquisition storage/naming, A4).
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from schema.errors import SchemaValidationError, SchemaVersionError

TIMESTAMPS_SCHEMA_VERSION = 1

_FIELDNAMES = ["frame_index", "hardware_timestamp_ns", "frame_id"]


@dataclass(frozen=True)
class TimestampRow:
    """One captured frame's chunk-data identity."""

    frame_index: int
    hardware_timestamp_ns: int
    frame_id: int

    def to_row(self) -> dict[str, int]:
        return asdict(self)

    @staticmethod
    def from_row(row: dict[str, str]) -> "TimestampRow":
        missing = set(_FIELDNAMES) - row.keys()
        if missing:
            raise SchemaValidationError(f"timestamps.csv row missing fields: {sorted(missing)}")
        return TimestampRow(
            frame_index=int(row["frame_index"]),
            hardware_timestamp_ns=int(row["hardware_timestamp_ns"]),
            frame_id=int(row["frame_id"]),
        )


def write_timestamps_csv(
    path: Path,
    rows: list[TimestampRow],
    schema_version: int = TIMESTAMPS_SCHEMA_VERSION,
) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        fh.write(f"#schema_version={schema_version}\n")
        writer = csv.DictWriter(fh, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_row())


def read_timestamps_csv(path: Path) -> tuple[int, list[TimestampRow]]:
    path = Path(path)
    with path.open("r", newline="", encoding="utf-8") as fh:
        first_line = fh.readline()
        if not first_line.startswith("#schema_version="):
            raise SchemaValidationError(
                f"timestamps.csv: expected leading #schema_version= comment, got {first_line!r}"
            )
        found_version = int(first_line.strip().split("=", 1)[1])
        if found_version != TIMESTAMPS_SCHEMA_VERSION:
            raise SchemaVersionError("timestamps.csv", found_version, TIMESTAMPS_SCHEMA_VERSION)
        reader = csv.DictReader(fh)
        rows = [TimestampRow.from_row(row) for row in reader]
    return found_version, rows

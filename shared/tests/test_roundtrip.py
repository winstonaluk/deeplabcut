"""Round-trip proof of the acquisition <-> analysis contract (checkpoint A0).

Builds a synthetic session entirely through the shared schema's own
write/read helpers -- the same functions the acquisition writer (A4) and the
analysis manifest reader (B2) will call -- and asserts what comes back
out is what went in. This is deliberately app-agnostic: it exercises the
contract itself, not either app's business logic.
"""

from __future__ import annotations

import pytest

from schema.errors import SchemaVersionError
from schema.session_metadata import CameraInfo, SessionMetadata
from schema.timestamps import TimestampRow, read_timestamps_csv, write_timestamps_csv
from schema.trials import TrialRecord, read_trials_csv, write_trials_csv


def _synthetic_session_metadata() -> SessionMetadata:
    return SessionMetadata(
        animal_id="R042",
        project_name="pdct-pilot",
        date="20260811",
        experimenter_initials="WL",
        session_start_timestamp="2026-08-11T09:00:00",
        cameras=(
            CameraInfo(serial="21334455", user_set_loaded="UserSet1", user_set_verified=True),
        ),
        app_version="0.1.0",
        git_commit="deadbeef",
        ffmpeg_encoder="h264_qsv",
        ffmpeg_params="-crf 18",
        rig_id="rig-1",
    )


def _synthetic_trials() -> list[TrialRecord]:
    return [
        TrialRecord(
            trial_number=1,
            start_time="2026-08-11T09:05:00",
            duration_s=42.5,
            flags=frozenset(),
            auto_flags=frozenset(),
            note="",
            n_frames=1275,
            dropped_frames=0,
            achieved_fps=30.0,
        ),
        TrialRecord(
            trial_number=2,
            start_time="2026-08-11T09:08:00",
            duration_s=12.0,
            flags=frozenset({"fall"}),
            auto_flags=frozenset({"suspiciously_short"}),
            note="fell near base",
            n_frames=360,
            dropped_frames=2,
            achieved_fps=29.9,
        ),
    ]


def _synthetic_timestamps() -> list[TimestampRow]:
    return [TimestampRow(frame_index=i, hardware_timestamp_ns=1_000_000 * i, frame_id=i) for i in range(5)]


def test_session_metadata_round_trip(tmp_path):
    meta = _synthetic_session_metadata()
    path = tmp_path / "session_metadata.json"
    meta.write_json(path)

    loaded = SessionMetadata.read_json(path)

    assert loaded == meta
    assert loaded.schema_version == 1


def test_trials_csv_round_trip(tmp_path):
    records = _synthetic_trials()
    path = tmp_path / "trials.csv"
    write_trials_csv(path, records)

    schema_version, loaded = read_trials_csv(path)

    assert schema_version == 1
    assert loaded == records
    assert loaded[0].included is True
    assert loaded[1].included is False  # non-empty flags -> invalid


def test_timestamps_csv_round_trip(tmp_path):
    rows = _synthetic_timestamps()
    path = tmp_path / "t001_timestamps.csv"
    write_timestamps_csv(path, rows)

    schema_version, loaded = read_timestamps_csv(path)

    assert schema_version == 1
    assert loaded == rows


def test_full_session_round_trip(tmp_path):
    """Simulates the contract end-to-end: everything one session directory holds."""
    session_dir = tmp_path / "R042_pdct-pilot_20260811_WL"
    session_dir.mkdir()

    meta = _synthetic_session_metadata()
    meta.write_json(session_dir / "session_metadata.json")

    trials = _synthetic_trials()
    write_trials_csv(session_dir / "trials.csv", trials)

    write_timestamps_csv(
        session_dir / "R042_pdct-pilot_20260811_WL_0905_t001_timestamps.csv",
        _synthetic_timestamps(),
    )

    reloaded_meta = SessionMetadata.read_json(session_dir / "session_metadata.json")
    _, reloaded_trials = read_trials_csv(session_dir / "trials.csv")

    assert reloaded_meta == meta
    assert reloaded_trials == trials


def test_session_metadata_rejects_future_schema_version(tmp_path):
    meta = _synthetic_session_metadata()
    path = tmp_path / "session_metadata.json"
    meta.write_json(path)

    text = path.read_text(encoding="utf-8").replace('"schema_version": 1', '"schema_version": 99')
    path.write_text(text, encoding="utf-8")

    with pytest.raises(SchemaVersionError):
        SessionMetadata.read_json(path)


def test_trials_csv_rejects_future_schema_version(tmp_path):
    path = tmp_path / "trials.csv"
    write_trials_csv(path, _synthetic_trials())

    text = path.read_text(encoding="utf-8").replace("#schema_version=1", "#schema_version=99")
    path.write_text(text, encoding="utf-8")

    with pytest.raises(SchemaVersionError):
        read_trials_csv(path)

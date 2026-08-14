"""Checkpoint B2: stage 0 build_manifest against a synthetic session tree."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.provenance import Provenance
from pipeline.stages.manifest import (
    build_manifest,
    compute_manifest_input_hashes,
    dataframe_to_manifest_rows,
    trial_uid,
    write_manifest,
)
from schema.session_metadata import CameraInfo, SessionMetadata
from schema.trials import TrialRecord, write_trials_csv


def _write_session(
    archive_root: Path,
    animal_id: str,
    project_name: str,
    date: str,
    initials: str,
    trials: list[TrialRecord],
    views: list[str] | None = None,
) -> Path:
    """Builds a synthetic session directory using the same shared schema
    writers the acquisition app uses -- this is the A0 contract exercised
    from the analysis side."""
    session_dir = archive_root / f"{animal_id}_{project_name}_{date}_{initials}"
    session_dir.mkdir(parents=True)

    meta = SessionMetadata(
        animal_id=animal_id, project_name=project_name, date=date, experimenter_initials=initials,
        session_start_timestamp=f"{date}T09:00:00",
        cameras=(CameraInfo(serial="123", user_set_loaded="UserSet1", user_set_verified=True),),
        app_version="0.1.0", git_commit="deadbeef", ffmpeg_encoder="h264_qsv",
        ffmpeg_params="-global_quality 18", rig_id="rig-1",
    )
    meta.write_json(session_dir / "session_metadata.json")
    write_trials_csv(session_dir / "trials.csv", trials)

    view_tokens = views or [None]
    for trial in trials:
        for view in view_tokens:
            base = f"{animal_id}_{project_name}_{date}_{initials}"
            if view:
                base += f"_{view}"
            base += f"_0905_t{trial.trial_number:03d}"
            (session_dir / f"{base}.mp4").write_bytes(b"fake-video")
            (session_dir / f"{base}_timestamps.csv").write_text("#schema_version=1\n", encoding="utf-8")

    return session_dir


def _trial(n: int, duration=42.5, flags=frozenset(), auto_flags=frozenset()) -> TrialRecord:
    return TrialRecord(
        trial_number=n, start_time=f"2026-08-11T09:0{n}:00", duration_s=duration,
        flags=flags, auto_flags=auto_flags, note="", n_frames=int(duration * 30),
        dropped_frames=0, achieved_fps=30.0,
    )


def test_trial_uid_is_deterministic():
    assert trial_uid("R042", "pdct-pilot", "20260811", "WL", "lateral_L", 1) == \
        "R042_pdct-pilot_20260811_WL_lateral_L_t001"


def test_build_manifest_single_session_single_view(tmp_path):
    archive_root = tmp_path / "archive"
    _write_session(archive_root, "R042", "pdct-pilot", "20260811", "WL", [_trial(1), _trial(2)])

    df = build_manifest(archive_root, views=("lateral_L",))

    assert len(df) == 2
    assert set(df["trial_uid"]) == {
        "R042_pdct-pilot_20260811_WL_lateral_L_t001",
        "R042_pdct-pilot_20260811_WL_lateral_L_t002",
    }
    assert all(df["video_path"] != "")
    assert all(df["timestamps_path"] != "")


def test_build_manifest_two_sessions(tmp_path):
    archive_root = tmp_path / "archive"
    _write_session(archive_root, "R042", "pdct-pilot", "20260811", "WL", [_trial(1)])
    _write_session(archive_root, "R043", "pdct-pilot", "20260811", "WL", [_trial(1), _trial(2)])

    df = build_manifest(archive_root, views=("lateral_L",))

    assert len(df) == 3
    assert set(df["animal_id"]) == {"R042", "R043"}


def test_build_manifest_multi_view_produces_one_row_per_trial_per_view(tmp_path):
    archive_root = tmp_path / "archive"
    _write_session(
        archive_root, "R042", "pdct-pilot", "20260811", "WL", [_trial(1)],
        views=["lateral_L", "top_down"],
    )

    df = build_manifest(archive_root, views=("lateral_L", "top_down"))

    assert len(df) == 2
    assert set(df["view"]) == {"lateral_L", "top_down"}
    # each view's video_path should reference that view's own file
    lateral_row = df[df["view"] == "lateral_L"].iloc[0]
    topdown_row = df[df["view"] == "top_down"].iloc[0]
    assert "lateral_L" in lateral_row["video_path"]
    assert "top_down" in topdown_row["video_path"]
    assert lateral_row["video_path"] != topdown_row["video_path"]


def test_build_manifest_preserves_flags_through_dataframe_round_trip(tmp_path):
    archive_root = tmp_path / "archive"
    _write_session(
        archive_root, "R042", "pdct-pilot", "20260811", "WL",
        [_trial(1, flags=frozenset({"fall"}), auto_flags=frozenset({"suspiciously_short"}))],
    )

    df = build_manifest(archive_root, views=("lateral_L",))
    rows = dataframe_to_manifest_rows(df)

    assert rows[0].flags == frozenset({"fall"})
    assert rows[0].auto_flags == frozenset({"suspiciously_short"})


def test_build_manifest_skips_non_session_directories(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    (archive_root / "not_a_session").mkdir()
    (archive_root / "not_a_session" / "readme.txt").write_text("hello", encoding="utf-8")
    _write_session(archive_root, "R042", "pdct-pilot", "20260811", "WL", [_trial(1)])

    df = build_manifest(archive_root, views=("lateral_L",))
    assert len(df) == 1


def test_write_manifest_produces_parquet_and_provenance(tmp_path):
    archive_root = tmp_path / "archive"
    _write_session(archive_root, "R042", "pdct-pilot", "20260811", "WL", [_trial(1)])
    output_path = tmp_path / "derived" / "manifest.parquet"

    prov = write_manifest(archive_root, views=("lateral_L",), output_path=output_path, config_hash="cfg123")

    assert output_path.exists()
    df = pd.read_parquet(output_path)
    assert len(df) == 1

    prov_path = tmp_path / "derived" / "manifest.parquet.provenance.json"
    assert prov_path.exists()
    reloaded = Provenance.read_json(prov_path)
    assert reloaded == prov
    assert reloaded.config_hash == "cfg123"
    assert reloaded.matches_inputs(compute_manifest_input_hashes(archive_root), "cfg123")


def test_write_manifest_provenance_changes_when_a_session_changes(tmp_path):
    archive_root = tmp_path / "archive"
    _write_session(archive_root, "R042", "pdct-pilot", "20260811", "WL", [_trial(1)])
    output_path = tmp_path / "derived" / "manifest.parquet"
    prov = write_manifest(archive_root, views=("lateral_L",), output_path=output_path, config_hash="cfg123")

    # mutate the session (e.g. a late flag edit via the review screen)
    session_dir = archive_root / "R042_pdct-pilot_20260811_WL"
    write_trials_csv(session_dir / "trials.csv", [_trial(1, flags=frozenset({"fall"}))])

    fresh_hashes = compute_manifest_input_hashes(archive_root)
    assert prov.matches_inputs(fresh_hashes, "cfg123") is False

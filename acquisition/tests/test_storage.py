"""Checkpoint A4: filename generation, session_metadata.json, trials.csv,
timestamp sidecars, flag/auto_flag sets -- all against shared/schema/."""

from __future__ import annotations

from datetime import datetime

import pytest

from acquisition.trial_state_machine import TrialOutcome
from schema.session_metadata import CameraInfo, SessionMetadata
from schema.timestamps import TimestampRow, read_timestamps_csv, write_timestamps_csv
from schema.trials import read_trials_csv, write_trials_csv
from storage.metadata import build_session_metadata
from storage.naming import (
    SessionDirectoryExistsError,
    create_session_directory,
    session_dir_name,
    session_dir_path,
    trial_timestamps_filename,
    trial_video_filename,
)
from storage.trial_record import build_trial_record


def test_session_dir_name_matches_spec_pattern():
    assert session_dir_name("R042", "pdct-pilot", "20260811", "WL") == "R042_pdct-pilot_20260811_WL"


def test_create_session_directory_never_overwrites(tmp_path):
    path = create_session_directory(tmp_path, "R042", "pdct-pilot", "20260811", "WL")
    assert path.is_dir()
    assert path == session_dir_path(tmp_path, "R042", "pdct-pilot", "20260811", "WL")

    with pytest.raises(SessionDirectoryExistsError):
        create_session_directory(tmp_path, "R042", "pdct-pilot", "20260811", "WL")


def test_trial_video_filename_matches_spec_pattern():
    start = datetime(2026, 8, 11, 9, 5)
    name = trial_video_filename("R042", "pdct-pilot", "20260811", "WL", start, trial_number=1)
    assert name == "R042_pdct-pilot_20260811_WL_0905_t001.mp4"

    name_42 = trial_video_filename("R042", "pdct-pilot", "20260811", "WL", start, trial_number=42)
    assert name_42.endswith("_t042.mp4")


def test_trial_timestamps_filename_matches_video_basename():
    start = datetime(2026, 8, 11, 9, 5)
    video = trial_video_filename("R042", "pdct-pilot", "20260811", "WL", start, trial_number=1)
    timestamps = trial_timestamps_filename("R042", "pdct-pilot", "20260811", "WL", start, trial_number=1)
    assert timestamps == video.removesuffix(".mp4") + "_timestamps.csv"


def test_view_token_is_off_by_default_and_opt_in():
    start = datetime(2026, 8, 11, 9, 5)
    default = trial_video_filename("R042", "pdct-pilot", "20260811", "WL", start, trial_number=1)
    assert "lateral" not in default

    with_view = trial_video_filename(
        "R042", "pdct-pilot", "20260811", "WL", start, trial_number=1,
        view="lateral", include_view_token=True,
    )
    assert with_view == "R042_pdct-pilot_20260811_WL_lateral_0905_t001.mp4"


def test_view_token_requires_a_view_name():
    start = datetime(2026, 8, 11, 9, 5)
    with pytest.raises(ValueError):
        trial_video_filename(
            "R042", "pdct-pilot", "20260811", "WL", start, trial_number=1, include_view_token=True
        )


def test_build_trial_record_maps_outcome_to_schema_fields():
    outcome = TrialOutcome(
        trial_number=3, start_time=123.0, duration_s=42.5, auto_flags=frozenset({"suspiciously_short"})
    )
    wall_clock = datetime(2026, 8, 11, 9, 5, 30)

    record = build_trial_record(
        outcome, wall_clock, flags=frozenset({"fall"}), note="fell near base",
        n_frames=1275, dropped_frames=1, achieved_fps=29.9,
    )

    assert record.trial_number == 3
    assert record.start_time == wall_clock.isoformat()
    assert record.duration_s == 42.5
    assert record.flags == frozenset({"fall"})
    assert record.auto_flags == frozenset({"suspiciously_short"})
    assert record.included is False  # non-empty experimenter flags


def test_build_session_metadata_maps_config_and_runtime_info():
    meta = build_session_metadata(
        animal_id="R042", project_name="pdct-pilot", date="20260811",
        experimenter_initials="WL",
        session_start_timestamp=datetime(2026, 8, 11, 9, 0),
        cameras=(CameraInfo(serial="123", user_set_loaded="UserSet1", user_set_verified=True),),
        app_version="0.1.0", git_commit="deadbeef",
        ffmpeg_encoder="h264_qsv", ffmpeg_params="-global_quality 18", rig_id="rig-1",
    )
    assert isinstance(meta, SessionMetadata)
    assert meta.session_start_timestamp == "2026-08-11T09:00:00"
    assert meta.schema_version == 1


def test_full_session_round_trip_via_acquisition_naming_and_glue(tmp_path):
    """A4's proof: build a real session directory using only this app's own
    naming/glue code plus the shared schema writers, then read it all back."""
    session_dir = create_session_directory(tmp_path, "R042", "pdct-pilot", "20260811", "WL")

    meta = build_session_metadata(
        animal_id="R042", project_name="pdct-pilot", date="20260811",
        experimenter_initials="WL",
        session_start_timestamp=datetime(2026, 8, 11, 9, 0),
        cameras=(CameraInfo(serial="123", user_set_loaded="UserSet1", user_set_verified=True),),
        app_version="0.1.0", git_commit="deadbeef",
        ffmpeg_encoder="h264_qsv", ffmpeg_params="-global_quality 18", rig_id="rig-1",
    )
    meta.write_json(session_dir / "session_metadata.json")

    trial1_start = datetime(2026, 8, 11, 9, 5)
    outcome1 = TrialOutcome(trial_number=1, start_time=0.0, duration_s=42.5, auto_flags=frozenset())
    record1 = build_trial_record(
        outcome1, trial1_start, flags=frozenset(), note="", n_frames=1275, dropped_frames=0, achieved_fps=30.0
    )
    write_timestamps_csv(
        session_dir / trial_timestamps_filename("R042", "pdct-pilot", "20260811", "WL", trial1_start, 1),
        [TimestampRow(frame_index=i, hardware_timestamp_ns=i * 1_000_000, frame_id=i) for i in range(5)],
    )

    trial2_start = datetime(2026, 8, 11, 9, 8)
    outcome2 = TrialOutcome(
        trial_number=2, start_time=200.0, duration_s=12.0, auto_flags=frozenset({"suspiciously_short"})
    )
    record2 = build_trial_record(
        outcome2, trial2_start, flags=frozenset({"fall"}), note="fell near base",
        n_frames=360, dropped_frames=2, achieved_fps=29.9,
    )

    write_trials_csv(session_dir / "trials.csv", [record1, record2])

    video1_path = session_dir / trial_video_filename("R042", "pdct-pilot", "20260811", "WL", trial1_start, 1)
    video1_path.write_bytes(b"fake-mp4-bytes")

    # -- read it all back --
    reloaded_meta = SessionMetadata.read_json(session_dir / "session_metadata.json")
    schema_version, reloaded_trials = read_trials_csv(session_dir / "trials.csv")
    _, reloaded_timestamps = read_timestamps_csv(
        session_dir / trial_timestamps_filename("R042", "pdct-pilot", "20260811", "WL", trial1_start, 1)
    )

    assert reloaded_meta == meta
    assert schema_version == 1
    assert reloaded_trials == [record1, record2]
    assert reloaded_trials[0].included is True
    assert reloaded_trials[1].included is False
    assert len(reloaded_timestamps) == 5
    assert video1_path.exists()
    assert session_dir.name == "R042_pdct-pilot_20260811_WL"

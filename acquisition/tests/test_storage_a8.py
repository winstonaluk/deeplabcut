"""Checkpoint A8: free-space indicator + remaining-time estimate, hard block
below threshold (preflight), staging with checksum verification, confirm-
gated purge."""

from __future__ import annotations

import hashlib

import pytest

from acquisition.mock_camera import MockCamera
from acquisition.preflight import run_preflight_checks
from storage.disk import (
    check_disk_status,
    estimate_remaining_minutes,
    free_space_gb,
    measure_bitrate_mb_per_min,
)
from storage.staging import StagingResult, purge_session, stage_session


# -- disk.py --

def test_free_space_gb_is_positive_for_an_existing_path(tmp_path):
    assert free_space_gb(tmp_path) > 0


def test_free_space_gb_walks_up_to_an_existing_ancestor(tmp_path):
    not_yet_created = tmp_path / "session" / "nested"
    assert free_space_gb(not_yet_created) == free_space_gb(tmp_path)


def test_estimate_remaining_minutes_computes_from_bitrate():
    # 10 GB free at 100 MB/min -> 100 minutes
    assert estimate_remaining_minutes(free_gb=10.0, bitrate_mb_per_min=100.0) == pytest.approx(100.0)


def test_estimate_remaining_minutes_none_without_a_bitrate():
    assert estimate_remaining_minutes(free_gb=10.0, bitrate_mb_per_min=None) is None
    assert estimate_remaining_minutes(free_gb=10.0, bitrate_mb_per_min=0.0) is None


def test_measure_bitrate_from_real_completed_trial_files(tmp_path):
    video1 = tmp_path / "t001.mp4"
    video2 = tmp_path / "t002.mp4"
    video1.write_bytes(b"x" * 1_000_000)  # 1 MB
    video2.write_bytes(b"x" * 2_000_000)  # 2 MB

    # 3 MB total over 90 seconds (1.5 min) -> 2 MB/min
    bitrate = measure_bitrate_mb_per_min([video1, video2], total_duration_s=90.0)
    assert bitrate == pytest.approx(2.0)


def test_measure_bitrate_none_with_zero_duration():
    assert measure_bitrate_mb_per_min([], total_duration_s=0.0) is None


def test_check_disk_status_below_threshold(tmp_path):
    status = check_disk_status(tmp_path, min_free_gb=1e9)  # absurdly high threshold
    assert status.below_threshold is True

    status_ok = check_disk_status(tmp_path, min_free_gb=0.0)
    assert status_ok.below_threshold is False


def test_preflight_blocks_session_start_below_disk_threshold(tmp_path):
    camera = MockCamera(serial="mock-1", width=8, height=8, fps=10)
    result = run_preflight_checks(camera, "UserSet1", tmp_path, min_free_gb=1e9)

    assert result.passed is False
    assert any("disk space" in f.lower() for f in result.failures)


# -- staging.py --

def _make_session(tmp_path):
    session_dir = tmp_path / "R042_pdct-pilot_20260811_WL"
    session_dir.mkdir(parents=True)
    (session_dir / "session_metadata.json").write_text("{}", encoding="utf-8")
    (session_dir / "trials.csv").write_text("#schema_version=1\n", encoding="utf-8")
    (session_dir / "t001.mp4").write_bytes(b"fake-video-bytes" * 100)
    return session_dir


def test_stage_session_copies_and_verifies_checksums(tmp_path):
    session_dir = _make_session(tmp_path / "sessions")
    staging_root = tmp_path / "staging"
    staging_root.mkdir()

    result = stage_session(session_dir, staging_root)

    assert isinstance(result, StagingResult)
    assert result.verified is True
    assert result.staged_dir == staging_root / session_dir.name
    assert (result.staged_dir / "t001.mp4").read_bytes() == (session_dir / "t001.mp4").read_bytes()

    expected_hash = hashlib.sha256((session_dir / "t001.mp4").read_bytes()).hexdigest()
    assert result.checksums["t001.mp4"] == expected_hash


def test_stage_session_refuses_to_overwrite_existing_staged_copy(tmp_path):
    session_dir = _make_session(tmp_path / "sessions")
    staging_root = tmp_path / "staging"
    staging_root.mkdir()

    stage_session(session_dir, staging_root)
    with pytest.raises(FileExistsError):
        stage_session(session_dir, staging_root)


def test_purge_session_requires_explicit_confirmation(tmp_path):
    session_dir = _make_session(tmp_path / "sessions")

    with pytest.raises(ValueError):
        purge_session(session_dir, confirm=False)
    assert session_dir.exists()

    purge_session(session_dir, confirm=True)
    assert not session_dir.exists()


def test_purge_after_verified_transfer_flow(tmp_path):
    session_dir = _make_session(tmp_path / "sessions")
    staging_root = tmp_path / "staging"
    staging_root.mkdir()

    result = stage_session(session_dir, staging_root)
    assert result.verified is True

    purge_session(session_dir, confirm=True)
    assert not session_dir.exists()
    assert result.staged_dir.exists()  # staged copy survives the purge

"""Checkpoint B5: stage 9 report -- aggregation and table generation from
trial_summary.parquet and kinematics_long.parquet only."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import pytest

from pipeline.contracts import KinematicsLongRow, TrialSummaryRow
from pipeline.provenance import Provenance
from pipeline.stages.report import (
    aggregate_by_keypoint,
    aggregate_overall,
    aggregate_velocity_by_height,
    write_report,
)


def _summary_df(rows: list[TrialSummaryRow]) -> pd.DataFrame:
    return pd.DataFrame([asdict(r) for r in rows])


def _long_df(rows: list[KinematicsLongRow]) -> pd.DataFrame:
    return pd.DataFrame([asdict(r) for r in rows])


def _summary_row(**overrides) -> TrialSummaryRow:
    defaults = dict(
        trial_uid="uid", primary_keypoint="mid_back", descent_onset_frame=10,
        descent_offset_frame=70, descent_duration_s=2.0, mean_velocity_mm_s=500.0,
        occlusion_fraction=0.05, pole_landmark_drift_flagged=False,
    )
    defaults.update(overrides)
    return TrialSummaryRow(**defaults)


def test_aggregate_overall_basic_stats():
    rows = [
        _summary_row(trial_uid="a", descent_duration_s=2.0, mean_velocity_mm_s=500.0),
        _summary_row(trial_uid="b", descent_duration_s=4.0, mean_velocity_mm_s=300.0),
    ]
    stats = aggregate_overall(_summary_df(rows))

    assert stats["n_trials"] == 2
    assert stats["n_descent_detected"] == 2
    assert stats["fraction_descent_detected"] == pytest.approx(1.0)
    assert stats["mean_descent_duration_s"] == pytest.approx(3.0)
    assert stats["median_descent_duration_s"] == pytest.approx(3.0)
    assert stats["mean_velocity_mm_s"] == pytest.approx(400.0)
    assert stats["n_drift_flagged"] == 0


def test_aggregate_overall_handles_undetected_descent():
    rows = [
        _summary_row(trial_uid="a", descent_duration_s=2.0),
        _summary_row(
            trial_uid="b", descent_onset_frame=None, descent_offset_frame=None,
            descent_duration_s=None, mean_velocity_mm_s=None,
        ),
    ]
    stats = aggregate_overall(_summary_df(rows))

    assert stats["n_trials"] == 2
    assert stats["n_descent_detected"] == 1
    assert stats["fraction_descent_detected"] == pytest.approx(0.5)
    assert stats["mean_descent_duration_s"] == pytest.approx(2.0)


def test_aggregate_overall_counts_drift_flagged_trials():
    rows = [
        _summary_row(trial_uid="a", pole_landmark_drift_flagged=True),
        _summary_row(trial_uid="b", pole_landmark_drift_flagged=False),
        _summary_row(trial_uid="c", pole_landmark_drift_flagged=True),
    ]
    stats = aggregate_overall(_summary_df(rows))
    assert stats["n_drift_flagged"] == 2


def test_aggregate_by_keypoint_groups_correctly():
    rows = [
        _summary_row(trial_uid="a", primary_keypoint="mid_back", descent_duration_s=2.0),
        _summary_row(trial_uid="b", primary_keypoint="mid_back", descent_duration_s=4.0),
        _summary_row(trial_uid="c", primary_keypoint="snout", descent_duration_s=1.0),
    ]
    df = aggregate_by_keypoint(_summary_df(rows))

    assert set(df["primary_keypoint"]) == {"mid_back", "snout"}
    mid_back = df[df["primary_keypoint"] == "mid_back"].iloc[0]
    snout = df[df["primary_keypoint"] == "snout"].iloc[0]
    assert mid_back["n_trials"] == 2
    assert mid_back["mean_descent_duration_s"] == pytest.approx(3.0)
    assert snout["n_trials"] == 1


def _long_row(**overrides) -> KinematicsLongRow:
    defaults = dict(
        trial_uid="uid", view="lateral_L", keypoint="mid_back", frame_index=0,
        x_mm=0.0, y_mm=500.0, height_fraction=0.5, velocity_mm_s=-500.0,
        likelihood=0.9, is_interpolated=False,
    )
    defaults.update(overrides)
    return KinematicsLongRow(**defaults)


def test_aggregate_velocity_by_height_bins_across_trials():
    rows = [
        _long_row(trial_uid="a", frame_index=0, height_fraction=0.05, velocity_mm_s=-10.0),
        _long_row(trial_uid="b", frame_index=0, height_fraction=0.06, velocity_mm_s=-20.0),
        _long_row(trial_uid="a", frame_index=1, height_fraction=0.95, velocity_mm_s=-100.0),
    ]
    df = aggregate_velocity_by_height(_long_df(rows), n_bins=10)

    assert len(df) == 10
    first_bin = df.iloc[0]
    assert first_bin["n_samples"] == 2
    assert first_bin["mean_velocity_mm_s"] == pytest.approx(-15.0)
    last_bin = df.iloc[-1]
    assert last_bin["n_samples"] == 1
    assert last_bin["mean_velocity_mm_s"] == pytest.approx(-100.0)


def test_aggregate_velocity_by_height_excludes_nan_rows():
    rows = [
        _long_row(trial_uid="a", frame_index=0, height_fraction=float("nan"), velocity_mm_s=-10.0),
        _long_row(trial_uid="a", frame_index=1, height_fraction=0.5, velocity_mm_s=-20.0),
    ]
    df = aggregate_velocity_by_height(_long_df(rows), n_bins=10)
    assert sum(df["n_samples"]) == 1


def test_write_report_produces_parquet_tables_and_provenance(tmp_path):
    summary_rows = [
        _summary_row(trial_uid="a", primary_keypoint="mid_back"),
        _summary_row(trial_uid="b", primary_keypoint="snout", descent_duration_s=3.0),
    ]
    long_rows = [_long_row(trial_uid="a"), _long_row(trial_uid="b", height_fraction=0.2)]

    trial_summary_path = tmp_path / "trial_summary.parquet"
    kinematics_long_path = tmp_path / "kinematics_long.parquet"
    _summary_df(summary_rows).to_parquet(trial_summary_path, index=False)
    _long_df(long_rows).to_parquet(kinematics_long_path, index=False)

    output_dir = tmp_path / "report"
    prov = write_report(trial_summary_path, kinematics_long_path, output_dir, config_hash="cfg123")

    assert (output_dir / "summary_overall.parquet").exists()
    assert (output_dir / "summary_by_keypoint.parquet").exists()
    assert (output_dir / "velocity_by_height.parquet").exists()

    overall = pd.read_parquet(output_dir / "summary_overall.parquet")
    assert overall.iloc[0]["n_trials"] == 2

    prov_path = tmp_path / "report" / "summary_overall.parquet.provenance.json"
    reloaded = Provenance.read_json(prov_path)
    assert reloaded == prov
    assert reloaded.stage_name == "report"

"""Checkpoint B3: stage 1 qc_gate -- each rule independently, never drops rows."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.config import QCConfig
from pipeline.contracts import ManifestRow
from pipeline.provenance import Provenance
from pipeline.stages.manifest import manifest_rows_to_dataframe
from pipeline.stages.qc_gate import evaluate_trial, qc_gate, write_qc_gate

CONFIG = QCConfig(
    nominal_fps=30.0, max_dropped_frame_rate=0.02, min_duration_s=5.0,
    max_duration_s=600.0, max_fps_deviation=2.0,
)


def _row(**overrides) -> ManifestRow:
    defaults = dict(
        trial_uid="uid", animal_id="R042", project_name="pdct-pilot", date="20260811",
        initials="WL", view="lateral_L", trial_number=1, video_path="v.mp4",
        timestamps_path="t.csv", duration_s=42.5, n_frames=1275, dropped_frames=0,
        achieved_fps=30.0, flags=frozenset(), auto_flags=frozenset(),
    )
    defaults.update(overrides)
    return ManifestRow(**defaults)


def test_clean_trial_is_included():
    included, reason = evaluate_trial(_row(), CONFIG)
    assert included is True
    assert reason == ""


def test_experimenter_flags_exclude():
    included, reason = evaluate_trial(_row(flags=frozenset({"fall"})), CONFIG)
    assert included is False
    assert "experimenter flags" in reason
    assert "fall" in reason


def test_auto_flags_alone_do_not_exclude():
    # suspiciously_short is informational (acquisition/CLAUDE.md), not itself
    # a QC exclusion rule -- only the four explicit rules below exclude.
    included, reason = evaluate_trial(_row(auto_flags=frozenset({"suspiciously_short"})), CONFIG)
    assert included is True
    assert reason == ""


def test_dropped_frame_rate_above_threshold_excludes():
    # 30 dropped / 1000 total = 3% > 2% threshold
    included, reason = evaluate_trial(_row(n_frames=1000, dropped_frames=30), CONFIG)
    assert included is False
    assert "dropped_frame_rate" in reason


def test_dropped_frame_rate_at_threshold_is_included():
    # exactly 2% == threshold, not > threshold
    included, reason = evaluate_trial(_row(n_frames=1000, dropped_frames=20), CONFIG)
    assert included is True


def test_zero_frames_counts_as_full_drop_rate():
    included, reason = evaluate_trial(_row(n_frames=0, dropped_frames=0), CONFIG)
    assert included is False
    assert "dropped_frame_rate" in reason


def test_duration_below_min_excludes():
    included, reason = evaluate_trial(_row(duration_s=2.0), CONFIG)
    assert included is False
    assert "duration_s" in reason


def test_duration_above_max_excludes():
    included, reason = evaluate_trial(_row(duration_s=700.0), CONFIG)
    assert included is False
    assert "duration_s" in reason


def test_duration_within_range_is_included():
    included, reason = evaluate_trial(_row(duration_s=45.0), CONFIG)
    assert included is True


def test_fps_deviation_above_threshold_excludes():
    included, reason = evaluate_trial(_row(achieved_fps=25.0), CONFIG)  # |25-30|=5 > 2
    assert included is False
    assert "achieved_fps" in reason


def test_fps_within_deviation_threshold_is_included():
    included, reason = evaluate_trial(_row(achieved_fps=28.5), CONFIG)  # |28.5-30|=1.5 <= 2
    assert included is True


def test_multiple_failing_rules_all_appear_in_exclusion_reason():
    included, reason = evaluate_trial(
        _row(flags=frozenset({"fall"}), duration_s=1.0, achieved_fps=10.0), CONFIG
    )
    assert included is False
    assert "experimenter flags" in reason
    assert "duration_s" in reason
    assert "achieved_fps" in reason


def test_qc_gate_never_drops_rows():
    rows = [_row(trial_uid="clean"), _row(trial_uid="dirty", flags=frozenset({"fall"}))]
    manifest_df = manifest_rows_to_dataframe(rows)

    qc_df = qc_gate(manifest_df, CONFIG)

    assert len(qc_df) == len(manifest_df) == 2
    assert set(qc_df["trial_uid"]) == {"clean", "dirty"}
    included_by_uid = dict(zip(qc_df["trial_uid"], qc_df["included"]))
    assert included_by_uid["clean"] is True
    assert included_by_uid["dirty"] is False


def test_write_qc_gate_produces_parquet_and_provenance(tmp_path):
    rows = [_row(trial_uid="a"), _row(trial_uid="b", flags=frozenset({"freeze"}))]
    manifest_path = tmp_path / "manifest.parquet"
    manifest_rows_to_dataframe(rows).to_parquet(manifest_path, index=False)

    output_path = tmp_path / "manifest_qc.parquet"
    prov = write_qc_gate(manifest_path, output_path, CONFIG, config_hash="cfg123")

    assert output_path.exists()
    qc_df = pd.read_parquet(output_path)
    assert len(qc_df) == 2
    assert set(qc_df["included"]) == {True, False}

    prov_path = tmp_path / "manifest_qc.parquet.provenance.json"
    reloaded = Provenance.read_json(prov_path)
    assert reloaded == prov
    assert reloaded.stage_name == "qc_gate"

"""Checkpoint B7 (not buildable unattended): resumability/caching logic for
stages 3/5/6/7 is real and tested; the DLC calls themselves are thin
NotImplementedError wrappers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from pipeline.contracts import FrameManifestRow, PoseIndexRow
from pipeline.stages.evaluate import build_evaluation_report, evaluate, passes_gate
from pipeline.stages.extract import (
    dataframe_to_frame_manifest_rows,
    extract_frames_for_trial,
    frame_manifest_rows_to_dataframe,
    trials_needing_extraction,
)
from pipeline.stages.infer import (
    dataframe_to_pose_index_rows,
    infer_trial,
    pose_index_rows_to_dataframe,
    trials_needing_inference,
)
from pipeline.stages.train import has_matching_training_run, train, write_training_log
from pipeline.contracts import TrainingLog


def _manifest_qc_df(rows: list[tuple[str, bool]]) -> pd.DataFrame:
    return pd.DataFrame({"trial_uid": [uid for uid, _ in rows], "included": [inc for _, inc in rows]})


# -- stage 3: extract --

def test_trials_needing_extraction_all_when_nothing_done():
    manifest_qc = _manifest_qc_df([("a", True), ("b", True), ("c", False)])
    needed = trials_needing_extraction(manifest_qc, existing_frames_df=None)
    assert set(needed) == {"a", "b"}  # excluded trial "c" never appears


def test_trials_needing_extraction_skips_already_done():
    manifest_qc = _manifest_qc_df([("a", True), ("b", True)])
    existing = pd.DataFrame({"trial_uid": ["a"]})
    needed = trials_needing_extraction(manifest_qc, existing)
    assert needed == ["b"]


def test_extract_frames_for_trial_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        extract_frames_for_trial("uid", Path("v.mp4"), round_number=1)


def test_frame_manifest_dataframe_round_trip():
    rows = [FrameManifestRow(trial_uid="a", frame_index=3, extraction_method="kmeans", extraction_round=1, image_path="f.png")]
    df = frame_manifest_rows_to_dataframe(rows)
    assert dataframe_to_frame_manifest_rows(df) == rows


# -- stage 5: train --

def test_has_matching_training_run_false_when_missing(tmp_path):
    assert has_matching_training_run(tmp_path / "training_log.json", "cfg123") is False


def test_has_matching_training_run_true_when_config_hash_matches(tmp_path):
    path = tmp_path / "training_log.json"
    write_training_log(path, TrainingLog(config_hash="cfg123", seed=42, train_fraction=0.8, snapshot_id="s1", superanimal_init="SuperAnimal-Quadruped"))
    assert has_matching_training_run(path, "cfg123") is True


def test_has_matching_training_run_false_when_config_hash_differs(tmp_path):
    path = tmp_path / "training_log.json"
    write_training_log(path, TrainingLog(config_hash="cfg123", seed=42, train_fraction=0.8, snapshot_id="s1", superanimal_init="SuperAnimal-Quadruped"))
    assert has_matching_training_run(path, "cfg_different") is False


def test_train_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        train(Path("dlc_project"), "SuperAnimal-Quadruped", "cfg123")


# -- stage 6: evaluate --

def test_passes_gate_true_within_threshold():
    assert passes_gate(overall_pixel_error=3.0, max_pixel_error=10.0) is True


def test_passes_gate_false_above_threshold():
    assert passes_gate(overall_pixel_error=15.0, max_pixel_error=10.0) is False


def test_passes_gate_true_exactly_at_threshold():
    assert passes_gate(overall_pixel_error=10.0, max_pixel_error=10.0) is True


def test_build_evaluation_report_sets_gate_correctly():
    report = build_evaluation_report(
        overall_pixel_error=3.0, per_keypoint_pixel_error={"snout": 2.0}, pcutoff_sweep={0.6: 3.0},
        max_pixel_error=10.0,
    )
    assert report.passes_gate is True

    failing = build_evaluation_report(
        overall_pixel_error=20.0, per_keypoint_pixel_error={"snout": 20.0}, pcutoff_sweep={0.6: 20.0},
        max_pixel_error=10.0,
    )
    assert failing.passes_gate is False


def test_evaluate_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        evaluate(Path("dlc_project"), snapshot_id="s1")


# -- stage 7: infer --

def test_trials_needing_inference_all_when_no_pose_index():
    manifest_qc = _manifest_qc_df([("a", True), ("b", True), ("c", False)])
    needed = trials_needing_inference(manifest_qc, None, snapshot_id="s1", config_hash="cfg1")
    assert set(needed) == {"a", "b"}


def test_trials_needing_inference_skips_matching_snapshot_and_config():
    manifest_qc = _manifest_qc_df([("a", True), ("b", True)])
    existing = pose_index_rows_to_dataframe(
        [PoseIndexRow(trial_uid="a", pose_path="a.h5", snapshot_id="s1", config_hash="cfg1")]
    )
    needed = trials_needing_inference(manifest_qc, existing, snapshot_id="s1", config_hash="cfg1")
    assert needed == ["b"]


def test_trials_needing_inference_reruns_when_snapshot_differs():
    manifest_qc = _manifest_qc_df([("a", True)])
    existing = pose_index_rows_to_dataframe(
        [PoseIndexRow(trial_uid="a", pose_path="a.h5", snapshot_id="OLD_SNAPSHOT", config_hash="cfg1")]
    )
    needed = trials_needing_inference(manifest_qc, existing, snapshot_id="NEW_SNAPSHOT", config_hash="cfg1")
    assert needed == ["a"]


def test_trials_needing_inference_reruns_when_config_hash_differs():
    manifest_qc = _manifest_qc_df([("a", True)])
    existing = pose_index_rows_to_dataframe(
        [PoseIndexRow(trial_uid="a", pose_path="a.h5", snapshot_id="s1", config_hash="OLD_CFG")]
    )
    needed = trials_needing_inference(manifest_qc, existing, snapshot_id="s1", config_hash="NEW_CFG")
    assert needed == ["a"]


def test_trials_needing_inference_never_includes_excluded_trials():
    manifest_qc = _manifest_qc_df([("a", False)])
    needed = trials_needing_inference(manifest_qc, None, snapshot_id="s1", config_hash="cfg1")
    assert needed == []


def test_pose_index_dataframe_round_trip():
    rows = [PoseIndexRow(trial_uid="a", pose_path="a.h5", snapshot_id="s1", config_hash="cfg1")]
    df = pose_index_rows_to_dataframe(rows)
    assert dataframe_to_pose_index_rows(df) == rows


def test_infer_trial_raises_not_implemented(tmp_path):
    with pytest.raises(NotImplementedError):
        infer_trial("uid", Path("v.mp4"), snapshot_id="s1", local_cache_root=tmp_path)

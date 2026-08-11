"""Checkpoint B1: stage-contract dataclasses are importable and construct
with full type signatures. Behavior tests land with each stage's checkpoint
(B2 manifest, B3 qc_gate, B4 kinematics, ...)."""

from __future__ import annotations

from pipeline.contracts import (
    CalibrationRecord,
    EvaluationReport,
    FrameManifestRow,
    KinematicsLongRow,
    ManifestRow,
    PoseIndexRow,
    QCRow,
    TrainingLog,
    TrialSummaryRow,
)


def test_manifest_row_constructs():
    row = ManifestRow(
        trial_uid="R042_pdct-pilot_20260811_WL_lateral_L_t001",
        animal_id="R042", project_name="pdct-pilot", date="20260811", initials="WL",
        view="lateral_L", trial_number=1, video_path="v.mp4", timestamps_path="t.csv",
        duration_s=42.5, n_frames=1275, dropped_frames=0, achieved_fps=30.0,
        flags=frozenset(), auto_flags=frozenset(),
    )
    assert row.trial_uid.endswith("t001")


def test_qc_row_constructs_and_carries_included_flag():
    row = QCRow(
        trial_uid="uid", animal_id="R042", project_name="pdct-pilot", date="20260811",
        initials="WL", view="lateral_L", trial_number=1, video_path="v.mp4",
        timestamps_path="t.csv", duration_s=1.0, n_frames=30, dropped_frames=0,
        achieved_fps=30.0, flags=frozenset({"fall"}), auto_flags=frozenset(),
        included=False, exclusion_reason="experimenter flag: fall",
    )
    assert row.included is False


def test_calibration_record_constructs():
    record = CalibrationRecord(
        camera_serial="12345678", epoch_id="epoch-2026-01",
        camera_matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        distortion_coefficients=(0.0, 0.0, 0.0, 0.0, 0.0),
    )
    assert record.camera_matrix[2] == (0.0, 0.0, 1.0)


def test_frame_manifest_row_constructs():
    row = FrameManifestRow(
        trial_uid="uid", frame_index=10, extraction_method="kmeans", extraction_round=1,
        image_path="frames/uid_0010.png",
    )
    assert row.extraction_round == 1


def test_training_log_constructs():
    log = TrainingLog(
        config_hash="abc", seed=42, train_fraction=0.8,
        snapshot_id="snapshot-001", superanimal_init="SuperAnimal-Quadruped",
    )
    assert log.train_fraction == 0.8


def test_evaluation_report_constructs_and_gate_is_a_plain_bool():
    report = EvaluationReport(
        overall_pixel_error=3.2,
        per_keypoint_pixel_error={"snout": 2.1, "pole_top": 0.4},
        pcutoff_sweep={0.4: 3.5, 0.6: 3.2, 0.8: 3.0},
        passes_gate=True,
    )
    assert report.passes_gate is True
    assert report.per_keypoint_pixel_error["pole_top"] < report.per_keypoint_pixel_error["snout"]


def test_pose_index_row_constructs():
    row = PoseIndexRow(trial_uid="uid", pose_path="pose/uid.h5", snapshot_id="snap-1", config_hash="abc")
    assert row.pose_path.endswith(".h5")


def test_kinematics_long_row_constructs():
    row = KinematicsLongRow(
        trial_uid="uid", view="lateral_L", keypoint="mid_back", frame_index=5,
        x_mm=12.3, y_mm=456.7, likelihood=0.92, is_interpolated=False,
    )
    assert row.is_interpolated is False


def test_trial_summary_row_allows_none_for_undetected_descent():
    row = TrialSummaryRow(
        trial_uid="uid", primary_keypoint="mid_back",
        descent_onset_frame=None, descent_offset_frame=None, descent_duration_s=None,
        mean_velocity_mm_s=None, occlusion_fraction=1.0, pole_landmark_drift_flagged=False,
    )
    assert row.descent_duration_s is None

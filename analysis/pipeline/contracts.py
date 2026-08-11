"""Stage-contract dataclasses: one row per record, long/tidy and view-tagged
(analysis/CLAUDE.md invariant 10). Each stage module converts a list of
these to/from its parquet/csv artifact -- the dataclass is the contract;
pandas is an implementation detail behind it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ManifestRow:
    """Stage 0 (build_manifest) output: manifest.parquet, one row per trial x view."""

    trial_uid: str
    animal_id: str
    project_name: str
    date: str
    initials: str
    view: str
    trial_number: int
    video_path: str
    timestamps_path: str
    duration_s: float
    n_frames: int
    dropped_frames: int
    achieved_fps: float
    flags: frozenset[str]
    auto_flags: frozenset[str]


@dataclass(frozen=True)
class QCRow:
    """Stage 1 (qc_gate) output: manifest_qc.parquet = ManifestRow +
    included/exclusion_reason. Never drops rows (invariant 3) -- excluded
    trials stay present with included=False."""

    trial_uid: str
    animal_id: str
    project_name: str
    date: str
    initials: str
    view: str
    trial_number: int
    video_path: str
    timestamps_path: str
    duration_s: float
    n_frames: int
    dropped_frames: int
    achieved_fps: float
    flags: frozenset[str]
    auto_flags: frozenset[str]
    included: bool
    exclusion_reason: str  # "" when included


@dataclass(frozen=True)
class CalibrationRecord:
    """Stage 2 (calibration) output data contract. The calibration stage
    itself -- checkerboard corner detection -- is not built; it isn't
    assigned to any B-checkpoint (see QUESTIONS.md). Intrinsics only;
    extrinsics for 3D triangulation are future work."""

    camera_serial: str
    epoch_id: str
    camera_matrix: tuple[
        tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
    ]
    distortion_coefficients: tuple[float, ...]


@dataclass(frozen=True)
class FrameManifestRow:
    """Stage 3 (extract_frames, B7 scaffold) output: frames_manifest.csv."""

    trial_uid: str
    frame_index: int
    extraction_method: str
    extraction_round: int
    image_path: str


@dataclass(frozen=True)
class TrainingLog:
    """Stage 5 (train, B7 scaffold) output: training_log.json."""

    config_hash: str
    seed: int
    train_fraction: float
    snapshot_id: str
    superanimal_init: str


@dataclass(frozen=True)
class EvaluationReport:
    """Stage 6 (evaluate, B7 scaffold) output: evaluation_report.json."""

    overall_pixel_error: float
    per_keypoint_pixel_error: dict[str, float]
    pcutoff_sweep: dict[float, float]  # pcutoff -> resulting pixel error
    passes_gate: bool  # overall_pixel_error <= config evaluation_max_pixel_error


@dataclass(frozen=True)
class PoseIndexRow:
    """Stage 7 (infer, B7 scaffold) output: pose_index.parquet."""

    trial_uid: str
    pose_path: str
    snapshot_id: str
    config_hash: str


@dataclass(frozen=True)
class KinematicsLongRow:
    """Stage 8 (kinematics, B4) output: kinematics_long.parquet -- one row
    per frame x trial x view x keypoint (long/tidy, invariant 10)."""

    trial_uid: str
    view: str
    keypoint: str
    frame_index: int
    x_mm: float
    y_mm: float
    likelihood: float
    is_interpolated: bool


@dataclass(frozen=True)
class TrialSummaryRow:
    """Stage 8 (kinematics, B4) output: trial_summary.parquet -- one row per trial."""

    trial_uid: str
    primary_keypoint: str
    descent_onset_frame: int | None
    descent_offset_frame: int | None
    descent_duration_s: float | None
    mean_velocity_mm_s: float | None
    occlusion_fraction: float
    pole_landmark_drift_flagged: bool

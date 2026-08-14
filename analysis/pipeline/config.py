"""Loads and validates config.toml into typed dataclasses.

Every threshold, path, keypoint scheme, and filter parameter the pipeline
uses comes through :class:`AnalysisConfig`. No magic numbers in code
(analysis/CLAUDE.md invariant 6).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """config.toml is missing a required key or holds an invalid value."""


@dataclass(frozen=True)
class PathsConfig:
    archive_root: str
    local_cache_root: str
    derived_root: str
    dlc_project_path: str


@dataclass(frozen=True)
class KeypointsConfig:
    scheme: tuple[str, ...]
    pole_landmarks: tuple[str, ...]
    primary_keypoint: str


@dataclass(frozen=True)
class QCConfig:
    nominal_fps: float
    max_dropped_frame_rate: float
    min_duration_s: float
    max_duration_s: float
    max_fps_deviation: float


@dataclass(frozen=True)
class KinematicsConfig:
    likelihood_cutoff: float
    max_gap_frames: int
    smoothing_method: str
    smoothing_window: int
    descent_rule_name: str
    descent_rule_onset_height_fraction: float
    descent_rule_offset_height_fraction: float
    pole_landmark_drift_threshold_mm: float


@dataclass(frozen=True)
class CalibrationEpoch:
    camera_serial: str
    epoch_id: str
    start_date: str
    end_date: str
    calibration_path: str


@dataclass(frozen=True)
class AnalysisConfig:
    paths: PathsConfig
    views: tuple[str, ...]
    keypoints: KeypointsConfig
    superanimal_init: dict[str, str]  # view -> SuperAnimal model name
    qc: QCConfig
    pole_length_mm: float
    kinematics: KinematicsConfig
    evaluation_max_pixel_error: float
    analysis_fps: int
    inference_batch_size: int
    calibration_epochs: tuple[CalibrationEpoch, ...]


_REQUIRED_TOP_LEVEL = (
    "paths", "views", "keypoints", "superanimal_init", "qc", "pole",
    "kinematics", "evaluation", "analysis", "inference", "calibration_epochs",
)


def load_config(path: str | Path) -> AnalysisConfig:
    path = Path(path)
    raw = tomllib.loads(path.read_text(encoding="utf-8"))

    missing = [k for k in _REQUIRED_TOP_LEVEL if k not in raw]
    if missing:
        raise ConfigError(f"{path}: missing top-level keys: {missing}")

    if not raw["views"]["list"]:
        raise ConfigError(f"{path}: views.list must be non-empty")
    if not raw["calibration_epochs"]:
        raise ConfigError(f"{path}: [[calibration_epochs]] must list at least one epoch")

    primary_keypoint = raw["keypoints"]["primary_keypoint"]
    if primary_keypoint not in raw["keypoints"]["scheme"]:
        raise ConfigError(
            f"{path}: primary_keypoint {primary_keypoint!r} is not in keypoints.scheme"
        )

    return AnalysisConfig(
        paths=PathsConfig(**raw["paths"]),
        views=tuple(raw["views"]["list"]),
        keypoints=KeypointsConfig(
            scheme=tuple(raw["keypoints"]["scheme"]),
            pole_landmarks=tuple(raw["keypoints"]["pole_landmarks"]),
            primary_keypoint=primary_keypoint,
        ),
        superanimal_init=dict(raw["superanimal_init"]),
        qc=QCConfig(**raw["qc"]),
        pole_length_mm=raw["pole"]["length_mm"],
        kinematics=KinematicsConfig(**raw["kinematics"]),
        evaluation_max_pixel_error=raw["evaluation"]["max_pixel_error"],
        analysis_fps=raw["analysis"]["fps"],
        inference_batch_size=raw["inference"]["batch_size"],
        calibration_epochs=tuple(
            CalibrationEpoch(**epoch) for epoch in raw["calibration_epochs"]
        ),
    )

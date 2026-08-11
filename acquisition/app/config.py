"""Loads and validates config.toml into typed dataclasses.

Every threshold, path, keybinding, and encoder setting the app uses comes
through :class:`AppConfig`. Nothing downstream should read config.toml
directly -- see acquisition/CLAUDE.md invariant 9 ("Config over literals").
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """config.toml is missing a required key or holds an invalid value."""


@dataclass(frozen=True)
class CameraConfig:
    serial: str
    name: str
    user_set: str


@dataclass(frozen=True)
class CaptureConfig:
    fps: int
    queue_maxsize: int
    preview_fps: int
    preroll_buffer_s: float


@dataclass(frozen=True)
class EncoderConfig:
    codec: str
    fallback_codec: str
    crf: int
    pixel_format: str


@dataclass(frozen=True)
class TrialTimingConfig:
    min_trial_duration_s: float
    suspicious_duration_s: float
    max_trial_duration_s: float


@dataclass(frozen=True)
class MetadataConfig:
    projects: tuple[str, ...]
    experimenter_initials: tuple[str, ...]
    animal_id_regex: str


@dataclass(frozen=True)
class StorageConfig:
    session_root: str
    min_free_gb: float
    filename_include_view_token: bool


@dataclass(frozen=True)
class StagingConfig:
    target_path: str
    checksum_algorithm: str


@dataclass(frozen=True)
class AppConfig:
    version: str
    rig_id: str
    cameras: tuple[CameraConfig, ...]
    capture: CaptureConfig
    encoder: EncoderConfig
    active_paradigm: str
    trial_timing: TrialTimingConfig
    keymap: dict[str, str]  # key -> reason_code
    reason_code_labels: dict[str, str]  # reason_code -> human label
    metadata: MetadataConfig
    storage: StorageConfig
    staging: StagingConfig
    log_level: str


_REQUIRED_TOP_LEVEL = (
    "app",
    "cameras",
    "capture",
    "encoder",
    "paradigm",
    "trial_timing",
    "keymap",
    "reason_code_labels",
    "metadata",
    "storage",
    "staging",
    "logging",
)


def load_config(path: str | Path) -> AppConfig:
    """Parses and validates config.toml. Raises ConfigError on any missing key.

    Deliberately fails loudly rather than falling back to a hardcoded
    default for a *missing table* -- defaults belong in config.toml itself,
    not in this loader, so every threshold stays editable in one place.
    """
    path = Path(path)
    raw = tomllib.loads(path.read_text(encoding="utf-8"))

    missing = [k for k in _REQUIRED_TOP_LEVEL if k not in raw]
    if missing:
        raise ConfigError(f"{path}: missing top-level keys: {missing}")

    if not raw["cameras"]:
        raise ConfigError(f"{path}: [[cameras]] must list at least one camera")

    cameras = tuple(
        CameraConfig(serial=c["serial"], name=c["name"], user_set=c["user_set"])
        for c in raw["cameras"]
    )

    return AppConfig(
        version=raw["app"]["version"],
        rig_id=raw["app"]["rig_id"],
        cameras=cameras,
        capture=CaptureConfig(**raw["capture"]),
        encoder=EncoderConfig(**raw["encoder"]),
        active_paradigm=raw["paradigm"]["active"],
        trial_timing=TrialTimingConfig(**raw["trial_timing"]),
        keymap=dict(raw["keymap"]),
        reason_code_labels=dict(raw["reason_code_labels"]),
        metadata=MetadataConfig(
            projects=tuple(raw["metadata"]["projects"]),
            experimenter_initials=tuple(raw["metadata"]["experimenter_initials"]),
            animal_id_regex=raw["metadata"]["animal_id_regex"],
        ),
        storage=StorageConfig(**raw["storage"]),
        staging=StagingConfig(**raw["staging"]),
        log_level=raw["logging"]["level"],
    )

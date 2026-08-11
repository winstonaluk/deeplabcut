"""Free-space indicator and remaining-recording-time estimate.

"GB free is not actionable mid-session; '47 min remaining' is."
(acquisition/CLAUDE.md "Storage"). Bitrate is measured from this session's
own completed trial video files, not assumed from a config constant --
codec, content, and CRF all affect real throughput.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiskStatus:
    free_gb: float
    below_threshold: bool
    estimated_remaining_minutes: float | None  # None until a bitrate is known


def existing_ancestor(path: Path) -> Path:
    """Walks up from ``path`` to the nearest ancestor that actually exists --
    a session directory may not be created yet when this is checked."""
    path = Path(path)
    while not path.exists():
        parent = path.parent
        if parent == path:
            raise FileNotFoundError(f"no existing ancestor for {path}")
        path = parent
    return path


def free_space_gb(path: Path) -> float:
    return shutil.disk_usage(existing_ancestor(Path(path))).free / 1e9


def measure_bitrate_mb_per_min(video_paths: list[Path], total_duration_s: float) -> float | None:
    """Measured throughput from this session's own completed trial videos.
    Returns None until there's at least one completed trial to measure from.
    """
    if total_duration_s <= 0:
        return None
    total_bytes = sum(p.stat().st_size for p in video_paths if p.exists())
    total_mb = total_bytes / 1e6
    return total_mb / (total_duration_s / 60)


def estimate_remaining_minutes(free_gb: float, bitrate_mb_per_min: float | None) -> float | None:
    if not bitrate_mb_per_min or bitrate_mb_per_min <= 0:
        return None
    return (free_gb * 1000) / bitrate_mb_per_min


def check_disk_status(
    path: Path, min_free_gb: float, bitrate_mb_per_min: float | None = None
) -> DiskStatus:
    free_gb = free_space_gb(path)
    return DiskStatus(
        free_gb=free_gb,
        below_threshold=free_gb < min_free_gb,
        estimated_remaining_minutes=estimate_remaining_minutes(free_gb, bitrate_mb_per_min),
    )

"""Preflight checks: camera detected, UserSet loaded+verified, FFmpeg
available, free disk above threshold. Pure logic, no Qt -- the session setup
screen (A5) calls this and renders the result; it never re-implements the
checks itself.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from acquisition.camera_backend import CameraBackend, CameraError
from storage.disk import free_space_gb


@dataclass(frozen=True)
class PreflightResult:
    passed: bool
    failures: tuple[str, ...]


def run_preflight_checks(
    camera: CameraBackend,
    user_set_name: str,
    session_root: Path,
    min_free_gb: float,
) -> PreflightResult:
    failures: list[str] = []

    camera_opened = False
    try:
        camera.open()
        camera_opened = True
    except CameraError as exc:
        failures.append(f"Camera not detected: {exc}")

    if camera_opened:
        if not camera.load_user_set(user_set_name):
            failures.append(f"UserSet {user_set_name!r} failed to load or verify")

    if shutil.which("ffmpeg") is None:
        failures.append("FFmpeg not found on PATH")

    free_gb = free_space_gb(Path(session_root))
    if free_gb < min_free_gb:
        failures.append(
            f"Free disk space ({free_gb:.1f} GB) is below the {min_free_gb} GB threshold"
        )

    passed = not failures
    if not passed and camera_opened:
        camera.close()  # session isn't starting; don't hold the camera open

    return PreflightResult(passed=passed, failures=tuple(failures))

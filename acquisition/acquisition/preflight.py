"""Preflight checks: camera detected, UserSet loaded, camera settings verified
against config, geometry and frame rate matching config, FFmpeg available,
free disk above threshold. Pure logic, no Qt -- the session setup screen (A5)
calls this and renders the result; it never re-implements the checks itself.

The camera checks exist because config.toml describes what we *intend* the
hardware to be doing, and the hardware is the only authority on what it is
actually doing. Every check here compares one against the other and blocks
the session when they disagree, rather than recording something silently
wrong. See acquisition/acquisition/HARDWARE.md for what motivated each.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from acquisition.camera_backend import CameraBackend, CameraError

from storage.disk import free_space_gb


@dataclass(frozen=True)
class PreflightCheck:
    """One named check and its outcome.

    Passing checks are retained, not just failures: the setup screen shows the
    experimenter what was confirmed (camera serial, verified exposure mode,
    free space) and not merely what went wrong.
    """

    name: str
    passed: bool
    detail: str = ""

    def describe(self) -> str:
        return f"{self.name}: {self.detail}" if self.detail else self.name


@dataclass(frozen=True)
class PreflightResult:
    passed: bool
    failures: tuple[str, ...]
    checks: tuple[PreflightCheck, ...] = field(default=())

    @property
    def passed_checks(self) -> tuple[PreflightCheck, ...]:
        return tuple(c for c in self.checks if c.passed)


def run_preflight_checks(
    camera: CameraBackend,
    user_set_name: str,
    session_root: Path,
    min_free_gb: float,
    *,
    expected_resolution: tuple[int, int] | None = None,
    expected_fps: float | None = None,
    fps_tolerance: float = 0.5,
    expected_nodes: Mapping[str, str] | None = None,
) -> PreflightResult:
    """Runs every check and returns all outcomes.

    Deliberately does not short-circuit on the first failure: an experimenter
    with an animal in hand should see everything that needs fixing in one
    pass, not discover the next problem after fixing this one. The camera
    checks are skipped only when the camera itself failed to open, since
    there is nothing to interrogate in that case.
    """
    checks: list[PreflightCheck] = []

    camera_opened = False
    try:
        camera.open()
        camera_opened = True
        checks.append(
            PreflightCheck("Camera detected", True, f"serial {camera.serial}")
        )
    except CameraError as exc:
        checks.append(PreflightCheck("Camera detected", False, str(exc)))

    if camera_opened:
        checks.extend(
            _camera_checks(
                camera,
                user_set_name,
                expected_resolution=expected_resolution,
                expected_fps=expected_fps,
                fps_tolerance=fps_tolerance,
                expected_nodes=expected_nodes,
            )
        )

    ffmpeg_path = shutil.which("ffmpeg")
    checks.append(
        PreflightCheck("FFmpeg available", ffmpeg_path is not None, ffmpeg_path or "not found on PATH")
    )

    free_gb = free_space_gb(Path(session_root))
    checks.append(
        PreflightCheck(
            "Free disk space",
            free_gb >= min_free_gb,
            f"{free_gb:.1f} GB free, {min_free_gb} GB required",
        )
    )

    failures = tuple(c.describe() for c in checks if not c.passed)
    passed = not failures
    if not passed and camera_opened:
        camera.close()  # session isn't starting; don't hold the camera open

    return PreflightResult(passed=passed, failures=failures, checks=tuple(checks))


def _camera_checks(
    camera: CameraBackend,
    user_set_name: str,
    *,
    expected_resolution: tuple[int, int] | None,
    expected_fps: float | None,
    fps_tolerance: float,
    expected_nodes: Mapping[str, str] | None,
) -> list[PreflightCheck]:
    checks: list[PreflightCheck] = []

    user_set_loaded = camera.load_user_set(user_set_name)
    # Backends may explain *why* a load failed. The common real cause is another
    # Spinnaker session holding the camera's parameters latched, which is
    # trivially fixable once named and baffling when reported as "load failed".
    reason = getattr(camera, "last_user_set_error", None) or "load failed"
    checks.append(
        PreflightCheck(
            f"UserSet {user_set_name!r} loaded",
            user_set_loaded,
            "" if user_set_loaded else reason,
        )
    )

    # Settings verification only means anything against the values the UserSet
    # was supposed to install, so skip it when the load itself failed rather
    # than reporting a cascade of mismatches with one root cause.
    if user_set_loaded and expected_nodes:
        for node_check in camera.verify_settings(expected_nodes):
            checks.append(
                PreflightCheck(
                    f"Camera setting {node_check.node}",
                    node_check.passed,
                    node_check.describe(),
                )
            )

    if expected_resolution is not None:
        actual = camera.resolution
        checks.append(
            PreflightCheck(
                "Camera resolution matches config",
                actual == expected_resolution,
                f"camera {actual[0]}x{actual[1]}, "
                f"config {expected_resolution[0]}x{expected_resolution[1]}",
            )
        )

    if expected_fps is not None:
        actual_fps = camera.frame_rate
        checks.append(
            PreflightCheck(
                "Camera frame rate matches config",
                abs(actual_fps - expected_fps) <= fps_tolerance,
                f"camera {actual_fps:.2f} fps, config {expected_fps:.2f} fps "
                f"(tolerance {fps_tolerance})",
            )
        )

    return checks

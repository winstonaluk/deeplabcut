"""Maps a camera's config ``type`` to a concrete :class:`CameraBackend`.

One dict, resolved once at composition time. Adding a backend is a new entry
here plus a ``type = "..."`` in config.toml -- no source change at the call
site (acquisition/CLAUDE.md invariant 9).

Both factories are imported lazily inside their function. ``SpinnakerCamera``
already tolerates a machine with no SDK, but keeping PySpin out of this
module's import graph means ``--mock`` never reaches it at all.
"""

from __future__ import annotations

from acquisition.camera_backend import CameraBackend
from app.config import CameraConfig, CaptureConfig, ConfigError


def _mock(camera: CameraConfig, capture: CaptureConfig) -> CameraBackend:
    from acquisition.mock_camera import MockCamera

    return MockCamera(
        serial=camera.serial,
        width=capture.width,
        height=capture.height,
        fps=float(capture.fps),
        pixel_format=capture.source_pixel_format,
    )


def _spinnaker(camera: CameraConfig, capture: CaptureConfig) -> CameraBackend:
    from acquisition.spinnaker_camera import SpinnakerCamera

    return SpinnakerCamera(
        serial=camera.serial,
        pixel_format=capture.source_pixel_format,
        stream_buffer_count=capture.stream_buffer_count,
    )


CAMERA_BACKENDS = {
    "mock": _mock,
    "spinnaker": _spinnaker,
}


def build_camera(camera: CameraConfig, capture: CaptureConfig) -> CameraBackend:
    """Constructs the backend named by ``camera.type``.

    Geometry, pixel format and buffer depth come from ``[capture]`` rather than
    per camera: preflight asserts the camera agrees, and the backend reports
    what it is *actually* doing regardless of what was asked for.
    """
    try:
        factory = CAMERA_BACKENDS[camera.type]
    except KeyError:
        raise ConfigError(
            f"camera {camera.serial!r}: unknown type {camera.type!r}, "
            f"expected one of {sorted(CAMERA_BACKENDS)}"
        ) from None
    return factory(camera, capture)

"""Real hardware backend via Teledyne FLIR Spinnaker/PySpin.

**Not buildable unattended (checkpoint A9)** -- requires the Spinnaker SDK,
a matching PySpin wheel, and a physically connected camera, none of which
exist in this environment. This is a scaffold: method signatures matching
CameraBackend with NotImplementedError bodies. See SPINNAKER_PLAN.md in
this directory for the implementation plan, referenced against the
Spinnaker SDK's Python example scripts (Acquisition.py, ImageEvents.py,
UserSets.py).

PySpin is vendor-distributed, not on PyPI -- see acquisition/requirements.txt.
"""

from __future__ import annotations

from typing import Any

from acquisition.camera_backend import CameraBackend, FrameCallback


class SpinnakerCamera(CameraBackend):
    def __init__(self, serial: str) -> None:
        self._serial = serial
        self._is_streaming = False
        # Placeholders for PySpin.System / PySpin.CameraPtr -- see
        # SPINNAKER_PLAN.md "System / CameraList lifetime" for why the
        # System instance must be shared across all SpinnakerCamera
        # instances (N-camera by construction) rather than owned here.
        self._system: Any = None
        self._camera: Any = None

    def open(self) -> None:
        raise NotImplementedError(
            "requires the Spinnaker SDK + PySpin + physical hardware -- see SPINNAKER_PLAN.md"
        )

    def close(self) -> None:
        raise NotImplementedError("requires PySpin + hardware -- see SPINNAKER_PLAN.md")

    def load_user_set(self, user_set_name: str) -> bool:
        raise NotImplementedError("requires PySpin + hardware -- see SPINNAKER_PLAN.md")

    def start_streaming(self, on_frame: FrameCallback) -> None:
        raise NotImplementedError("requires PySpin + hardware -- see SPINNAKER_PLAN.md")

    def stop_streaming(self) -> None:
        raise NotImplementedError("requires PySpin + hardware -- see SPINNAKER_PLAN.md")

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def is_streaming(self) -> bool:
        return self._is_streaming

"""Real hardware backend via Teledyne FLIR Spinnaker/PySpin.

**Scaffold: satisfies the CameraBackend contract, does not yet drive hardware.**
The interface, the node names, and the constants below are settled and were
verified against the rig's actual camera (see ``HARDWARE.md`` in this
directory). What remains is filling in the five lifecycle bodies, which is
checkpoint A10 and needs a camera on the bench to test -- ``SPINNAKER_PLAN.md``
is the step-by-step for that, rewritten against the real device rather than
against generic SDK examples.

PySpin is vendor-distributed, not on PyPI -- see acquisition/requirements.txt.
It is imported lazily inside methods, never at module scope, so that this
module remains importable (and the whole app remains runnable under
``--mock``) on a machine with no Spinnaker SDK installed (invariant 2).
"""

from __future__ import annotations

from typing import Any, Mapping

from acquisition.camera_backend import CameraBackend, FrameCallback, NodeCheck
from acquisition.frame import PixelFormat

# --- Node names, verified present on the rig camera (BFS-U3-04S2C, fw 1707.1.6.0).
# Named here rather than inline so the A10 implementation and the preflight
# config (config.toml [camera_verify]) refer to one spelling of each node.

NODE_USER_SET_SELECTOR = "UserSetSelector"
NODE_USER_SET_LOAD = "UserSetLoad"
NODE_PIXEL_FORMAT = "PixelFormat"
NODE_WIDTH = "Width"
NODE_HEIGHT = "Height"
NODE_CHUNK_MODE_ACTIVE = "ChunkModeActive"
NODE_CHUNK_SELECTOR = "ChunkSelector"
NODE_CHUNK_ENABLE = "ChunkEnable"
NODE_TIMESTAMP_INCREMENT = "TimestampIncrement"
NODE_ACQUISITION_MODE = "AcquisitionMode"

# Transport-layer stream nodes. NOT covered by user sets -- the app owns these
# and must set them itself; there is no invariant 7 tension here.
NODE_STREAM_BUFFER_HANDLING_MODE = "StreamBufferHandlingMode"
NODE_STREAM_BUFFER_COUNT_MODE = "StreamBufferCountMode"
NODE_STREAM_BUFFER_COUNT_MANUAL = "StreamBufferCountManual"

# Chunks required to satisfy invariant 6 (hardware timestamps only). Both read
# False on the rig camera as shipped, so the backend must enable them.
REQUIRED_CHUNKS = ("FrameID", "Timestamp")

# OldestFirst back-pressures rather than discarding. NewestOnly silently drops
# frames -- correct for a live viewer (the SDK's own AcquireAndDisplay.py uses
# it), wrong for a recorder.
STREAM_BUFFER_HANDLING_MODE = "OldestFirst"


class SpinnakerCamera(CameraBackend):
    def __init__(
        self,
        serial: str,
        pixel_format: PixelFormat = PixelFormat.MONO8,
        stream_buffer_count: int = 64,
    ) -> None:
        self._serial = serial
        self._target_pixel_format = pixel_format
        self._stream_buffer_count = stream_buffer_count
        self._is_open = False
        self._is_streaming = False
        self._incomplete_frame_count = 0
        self._resolution: tuple[int, int] | None = None
        self._frame_rate: float | None = None
        # Placeholders for PySpin.System / PySpin.CameraPtr. The System
        # instance is process-wide and must be shared across all
        # SpinnakerCamera instances (N-camera by construction, invariant 1)
        # via the reference-counted module helper described in
        # SPINNAKER_PLAN.md -- never one GetInstance() per camera.
        self._system: Any = None
        self._camera: Any = None
        self._handler: Any = None  # must stay referenced or PySpin stops firing it

    def open(self) -> None:
        """Acquire the shared System, find the camera by serial, Init() it,
        enable chunk data, and configure stream buffers. Idempotent.

        See SPINNAKER_PLAN.md "open()". Chunk enablement happens here because
        invariant 6 is unsatisfiable without it: the rig camera ships with
        ChunkModeActive False and both required chunks disabled.
        """
        raise NotImplementedError(
            "checkpoint A10: requires a connected camera to test -- see SPINNAKER_PLAN.md"
        )

    def close(self) -> None:
        """DeInit, drop the camera reference, then release the shared System
        only when the last camera closes. Idempotent."""
        raise NotImplementedError(
            "checkpoint A10: requires a connected camera to test -- see SPINNAKER_PLAN.md"
        )

    def load_user_set(self, user_set_name: str) -> bool:
        """Select ``user_set_name`` on UserSetSelector, execute UserSetLoad.

        Known blocker: UserSetLoad reports GenICam access mode RO on the rig
        camera and raises AccessException on Execute(). See HARDWARE.md
        "Open hardware blocker" -- this must be cleared before A10 can be
        verified end to end.
        """
        raise NotImplementedError(
            "checkpoint A10: requires a connected camera to test -- see SPINNAKER_PLAN.md"
        )

    def verify_settings(self, expected: Mapping[str, str]) -> tuple[NodeCheck, ...]:
        """Read each named node back and compare, as strings. Never writes."""
        raise NotImplementedError(
            "checkpoint A10: requires a connected camera to test -- see SPINNAKER_PLAN.md"
        )

    def start_streaming(self, on_frame: FrameCallback) -> None:
        """Register a PySpin.ImageEventHandler, then BeginAcquisition().

        The handler must, on every frame: skip and count incomplete images,
        pull chunk timestamp and frame ID, convert to the target pixel
        format, **copy** the ndarray before releasing the image, and
        Release() on every path including errors. See SPINNAKER_PLAN.md
        "start_streaming()" -- the copy and the release are the two details
        that silently corrupt data or exhaust the buffer pool if missed.
        """
        raise NotImplementedError(
            "checkpoint A10: requires a connected camera to test -- see SPINNAKER_PLAN.md"
        )

    def stop_streaming(self) -> None:
        """EndAcquisition(), then UnregisterEventHandler(). Order matters."""
        raise NotImplementedError(
            "checkpoint A10: requires a connected camera to test -- see SPINNAKER_PLAN.md"
        )

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def is_streaming(self) -> bool:
        return self._is_streaming

    @property
    def resolution(self) -> tuple[int, int]:
        """Read from the camera's Width/Height nodes at open(), not from config."""
        if self._resolution is None:
            raise NotImplementedError(
                "checkpoint A10: resolution is read from the camera at open() -- "
                "see SPINNAKER_PLAN.md"
            )
        return self._resolution

    @property
    def pixel_format(self) -> PixelFormat:
        """The format frames are delivered in after conversion in the handler."""
        return self._target_pixel_format

    @property
    def frame_rate(self) -> float:
        """Read from AcquisitionResultingFrameRate at open() -- the rate the
        camera will actually deliver, which is not AcquisitionFrameRate when
        exposure time is the binding constraint."""
        if self._frame_rate is None:
            raise NotImplementedError(
                "checkpoint A10: frame rate is read from the camera at open() -- "
                "see SPINNAKER_PLAN.md"
            )
        return self._frame_rate

    @property
    def incomplete_frame_count(self) -> int:
        return self._incomplete_frame_count

"""Real hardware backend via Teledyne FLIR Spinnaker/PySpin.

Implemented and verified against the rig's camera (Blackfly S BFS-U3-04S2C,
serial 22514545, Spinnaker 4.3.0.190) -- see ``HARDWARE.md`` in this directory
for what that camera measurably is, and ``SPINNAKER_PLAN.md`` for why each step
below is shaped the way it is.

PySpin is vendor-distributed, not on PyPI -- see acquisition/requirements.txt.
It is imported lazily inside methods, never at module scope, so this module
remains importable (and the whole app remains runnable under ``--mock``) on a
machine with no Spinnaker SDK installed (invariant 2).
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Mapping

import numpy as np

from acquisition.camera_backend import CameraBackend, CameraError, FrameCallback, NodeCheck
from acquisition.frame import Frame, PixelFormat

logger = logging.getLogger(__name__)

# --- Node names, verified present on the rig camera (BFS-U3-04S2C, fw 1707.1.6.0).
# Named here rather than inline so the implementation and the preflight config
# (config.toml [camera_verify]) refer to one spelling of each node.

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
NODE_RESULTING_FRAME_RATE = "AcquisitionResultingFrameRate"

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

_LOCKED_PARAMS_HINT = (
    "camera parameters are locked -- another application (e.g. SpinView) may be "
    "streaming from this camera, or a previous run exited without closing it"
)


# --------------------------------------------------------------------------
# Shared System instance
# --------------------------------------------------------------------------
# PySpin.System.GetInstance() is process-wide, not per-camera. The app is
# N-camera by construction (invariant 1), so instances share one System with a
# reference count, released only when the last camera closes. Releasing while
# another camera is still open is a classic PySpin crash.

_system: Any = None
_system_refcount = 0
_system_lock = threading.Lock()


def _acquire_system() -> Any:
    global _system, _system_refcount
    import PySpin

    with _system_lock:
        if _system is None:
            _system = PySpin.System.GetInstance()
            version = _system.GetLibraryVersion()
            logger.info(
                "Spinnaker library %d.%d.%d.%d",
                version.major, version.minor, version.type, version.build,
            )
        _system_refcount += 1
        return _system


def _release_system() -> None:
    global _system, _system_refcount

    with _system_lock:
        _system_refcount -= 1
        if _system_refcount <= 0:
            if _system is not None:
                _system.ReleaseInstance()
            _system = None
            _system_refcount = 0


# --------------------------------------------------------------------------
# Node helpers
# --------------------------------------------------------------------------


def _node_value_str(nodemap: Any, name: str) -> str:
    """Reads a node as a string, whatever its type. "<unreadable>" on failure.

    GenICam nodes are a mix of enumerations, booleans, integers, floats and
    strings, and their only common loggable form is the symbolic/string one --
    which is also what config.toml's [camera_verify] table holds.
    """
    import PySpin

    node = nodemap.GetNode(name)
    if node is None:
        return "<absent>"
    for ptr in (PySpin.CEnumerationPtr, PySpin.CBooleanPtr, PySpin.CIntegerPtr,
                PySpin.CFloatPtr, PySpin.CStringPtr):
        try:
            typed = ptr(node)
            if not PySpin.IsReadable(typed):
                continue
            if ptr is PySpin.CEnumerationPtr:
                return str(typed.GetCurrentEntry().GetSymbolic())
            return str(typed.GetValue())
        except PySpin.SpinnakerException:
            continue
        except Exception:  # noqa: BLE001 -- a wrong cast raises plain TypeError
            continue
    return "<unreadable>"


def _set_enum(nodemap: Any, node_name: str, entry_name: str) -> None:
    import PySpin

    node = PySpin.CEnumerationPtr(nodemap.GetNode(node_name))
    if not PySpin.IsReadable(node) or not PySpin.IsWritable(node):
        raise CameraError(f"{node_name} is not writable -- {_LOCKED_PARAMS_HINT}")
    entry = node.GetEntryByName(entry_name)
    if entry is None or not PySpin.IsReadable(PySpin.CEnumEntryPtr(entry)):
        raise CameraError(f"{node_name} has no entry {entry_name!r}")
    node.SetIntValue(PySpin.CEnumEntryPtr(entry).GetValue())


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
        self._incomplete_frames = 0
        self._resolution: tuple[int, int] | None = None
        self._frame_rate: float | None = None
        self._camera: Any = None
        self._camera_list: Any = None
        self._handler: Any = None  # must stay referenced or PySpin stops firing it
        self._last_user_set_error: str | None = None

    # -- lifecycle ---------------------------------------------------------

    def open(self) -> None:
        if self._is_open:
            return  # preflight opens and holds; CaptureController opens again

        import PySpin

        system = _acquire_system()
        try:
            self._camera_list = system.GetCameras()
            self._camera = self._find_by_serial(self._camera_list)
            self._camera.Init()
            self._is_open = True

            nodemap = self._camera.GetNodeMap()
            self._resolution = (
                int(PySpin.CIntegerPtr(nodemap.GetNode(NODE_WIDTH)).GetValue()),
                int(PySpin.CIntegerPtr(nodemap.GetNode(NODE_HEIGHT)).GetValue()),
            )
            # The rate the camera will actually deliver, which is not
            # AcquisitionFrameRate when exposure time is the binding
            # constraint -- they read 66.12 and 199.93 on this camera.
            self._frame_rate = float(
                PySpin.CFloatPtr(nodemap.GetNode(NODE_RESULTING_FRAME_RATE)).GetValue()
            )

            self._configure_chunk_data(nodemap)
            self._configure_stream_buffers(self._camera.GetTLStreamNodeMap())
            _set_enum(nodemap, NODE_ACQUISITION_MODE, "Continuous")

            logger.info(
                "camera %s opened: %dx%d, %.2f fps, %s",
                self._serial, self._resolution[0], self._resolution[1],
                self._frame_rate, self._target_pixel_format.value,
            )
        except PySpin.SpinnakerException as exc:
            self._teardown()
            raise CameraError(f"failed to open camera {self._serial}: {exc}") from exc
        except Exception:
            self._teardown()
            raise

    def close(self) -> None:
        if not self._is_open:
            return
        try:
            if self._is_streaming:
                self.stop_streaming()
        finally:
            # Always tear down, even if stopping the stream failed. Leaving the
            # camera initialised is what latches its parameters read-only for
            # whoever opens it next.
            self._teardown()

    def _teardown(self) -> None:
        import PySpin

        try:
            if self._camera is not None:
                try:
                    if self._camera.IsInitialized():
                        self._camera.DeInit()
                except PySpin.SpinnakerException as exc:
                    logger.warning("DeInit failed for camera %s: %s", self._serial, exc)
                # PySpin needs the Python reference dropped before the list is
                # cleared and the System released; scope exit is not enough.
                del self._camera
                self._camera = None
            if self._camera_list is not None:
                self._camera_list.Clear()
                self._camera_list = None
        finally:
            self._handler = None
            self._is_streaming = False
            if self._is_open:
                self._is_open = False
                _release_system()

    def _find_by_serial(self, camera_list: Any) -> Any:
        import PySpin

        for camera in camera_list:
            node = PySpin.CStringPtr(
                camera.GetTLDeviceNodeMap().GetNode("DeviceSerialNumber")
            )
            if PySpin.IsReadable(node) and str(node.GetValue()).strip() == self._serial:
                return camera
        found = [
            str(PySpin.CStringPtr(c.GetTLDeviceNodeMap().GetNode("DeviceSerialNumber")).GetValue())
            for c in camera_list
        ]
        raise CameraError(
            f"no camera with serial {self._serial!r} (found: {found or 'none'})"
        )

    # -- one-time configuration -------------------------------------------

    def _configure_chunk_data(self, nodemap: Any) -> None:
        """Enables the chunks invariant 6 depends on.

        The camera ships with ChunkModeActive False and both required chunks
        disabled, so hardware timestamps do not exist until something turns
        them on. This is the documented carve-out from invariant 7 (see
        acquisition/CLAUDE.md): chunk data is a data-integrity requirement of
        this app, not an image-formation parameter.
        """
        import PySpin

        selector = PySpin.CEnumerationPtr(nodemap.GetNode(NODE_CHUNK_SELECTOR))
        enable = PySpin.CBooleanPtr(nodemap.GetNode(NODE_CHUNK_ENABLE))
        if not PySpin.IsReadable(selector) or not PySpin.IsWritable(selector):
            raise CameraError(f"{NODE_CHUNK_SELECTOR} not writable -- {_LOCKED_PARAMS_HINT}")

        for chunk_name in REQUIRED_CHUNKS:
            entry = selector.GetEntryByName(chunk_name)
            if entry is None or not PySpin.IsReadable(PySpin.CEnumEntryPtr(entry)):
                raise CameraError(f"camera has no {chunk_name!r} chunk (required by invariant 6)")
            selector.SetIntValue(PySpin.CEnumEntryPtr(entry).GetValue())
            if not PySpin.IsWritable(enable):
                raise CameraError(f"{NODE_CHUNK_ENABLE} not writable for {chunk_name}")
            enable.SetValue(True)

        mode_active = PySpin.CBooleanPtr(nodemap.GetNode(NODE_CHUNK_MODE_ACTIVE))
        if not PySpin.IsWritable(mode_active):
            raise CameraError(f"{NODE_CHUNK_MODE_ACTIVE} not writable -- {_LOCKED_PARAMS_HINT}")
        mode_active.SetValue(True)

        # 1000 on this camera: the counter ticks at 1 us but is expressed in
        # nanoseconds, so Frame.hardware_timestamp_ns needs no scaling. Logged
        # rather than assumed, because it is a per-model property.
        increment = _node_value_str(nodemap, NODE_TIMESTAMP_INCREMENT)
        logger.info(
            "chunk data enabled for %s (TimestampIncrement=%s ns)",
            ", ".join(REQUIRED_CHUNKS), increment,
        )

    def _configure_stream_buffers(self, stream_nodemap: Any) -> None:
        """Sets buffer handling and depth. Not covered by user sets."""
        import PySpin

        _set_enum(stream_nodemap, NODE_STREAM_BUFFER_HANDLING_MODE, STREAM_BUFFER_HANDLING_MODE)
        _set_enum(stream_nodemap, NODE_STREAM_BUFFER_COUNT_MODE, "Manual")

        count = PySpin.CIntegerPtr(stream_nodemap.GetNode(NODE_STREAM_BUFFER_COUNT_MANUAL))
        if not PySpin.IsWritable(count):
            raise CameraError(f"{NODE_STREAM_BUFFER_COUNT_MANUAL} not writable")
        # The node clamps to its own range, so log what we actually got rather
        # than what we asked for.
        count.SetValue(max(count.GetMin(), min(self._stream_buffer_count, count.GetMax())))
        logger.info(
            "stream buffers: %s, count=%d", STREAM_BUFFER_HANDLING_MODE, count.GetValue()
        )

    # -- user set ----------------------------------------------------------

    def load_user_set(self, user_set_name: str) -> bool:
        import PySpin

        self._last_user_set_error = None
        if not self._is_open:
            self._last_user_set_error = "camera is not open"
            return False
        try:
            nodemap = self._camera.GetNodeMap()
            _set_enum(nodemap, NODE_USER_SET_SELECTOR, user_set_name)

            command = PySpin.CCommandPtr(nodemap.GetNode(NODE_USER_SET_LOAD))
            if not PySpin.IsWritable(command):
                # The live failure mode: a leftover or concurrent Spinnaker
                # session makes UserSetLoad/Save and the image-format nodes RO
                # as a group. Reported, not raised as an AccessException.
                self._last_user_set_error = _LOCKED_PARAMS_HINT
                logger.warning("UserSetLoad(%s) unavailable: %s", user_set_name, _LOCKED_PARAMS_HINT)
                return False

            command.Execute()
            logger.info("loaded %s on camera %s", user_set_name, self._serial)
        except (PySpin.SpinnakerException, CameraError) as exc:
            self._last_user_set_error = str(exc)
            logger.warning("UserSetLoad(%s) failed: %s", user_set_name, exc)
            return False

        # A user set can carry Width/Height/PixelFormat, so what the backend
        # reports must be re-read rather than left at the pre-load values.
        self._refresh_reported_state()
        return True

    @property
    def last_user_set_error(self) -> str | None:
        """Why the most recent load_user_set() returned False, if it did.

        Lets preflight say "another application may be streaming from this
        camera" instead of a bare "load failed", which is the difference
        between a fixable message and a mystery at the rig.
        """
        return self._last_user_set_error

    def _refresh_reported_state(self) -> None:
        import PySpin

        nodemap = self._camera.GetNodeMap()
        try:
            self._resolution = (
                int(PySpin.CIntegerPtr(nodemap.GetNode(NODE_WIDTH)).GetValue()),
                int(PySpin.CIntegerPtr(nodemap.GetNode(NODE_HEIGHT)).GetValue()),
            )
            self._frame_rate = float(
                PySpin.CFloatPtr(nodemap.GetNode(NODE_RESULTING_FRAME_RATE)).GetValue()
            )
        except PySpin.SpinnakerException as exc:
            raise CameraError(f"could not re-read camera geometry: {exc}") from exc

    def verify_settings(self, expected: Mapping[str, str]) -> tuple[NodeCheck, ...]:
        if not self._is_open:
            raise CameraError("camera must be open to verify settings")
        nodemap = self._camera.GetNodeMap()
        checks: list[NodeCheck] = []
        for node_name, expected_value in expected.items():
            actual = _node_value_str(nodemap, node_name)
            checks.append(
                NodeCheck(
                    node=node_name,
                    expected=str(expected_value),
                    actual=actual,
                    passed=_values_match(actual, str(expected_value)),
                )
            )
        return tuple(checks)

    # -- streaming ---------------------------------------------------------

    def start_streaming(self, on_frame: FrameCallback) -> None:
        import PySpin

        if self._is_streaming:
            return
        if not self._is_open:
            raise CameraError("camera must be open before streaming")

        handler = _make_frame_event_handler(on_frame, self._target_pixel_format)
        try:
            self._camera.RegisterEventHandler(handler)
            self._handler = handler  # PySpin does not keep it alive; GC = silent stall
            self._camera.BeginAcquisition()
            self._is_streaming = True
        except PySpin.SpinnakerException as exc:
            self._handler = None
            raise CameraError(f"could not start streaming on {self._serial}: {exc}") from exc

    def stop_streaming(self) -> None:
        import PySpin

        if not self._is_streaming:
            return
        try:
            # Order matters: unregistering before ending acquisition has
            # crashed past Spinnaker versions.
            self._camera.EndAcquisition()
            if self._handler is not None:
                self._camera.UnregisterEventHandler(self._handler)
        except PySpin.SpinnakerException as exc:
            raise CameraError(f"could not stop streaming on {self._serial}: {exc}") from exc
        finally:
            # Preserve the count past the handler's lifetime -- callers read it
            # after stopping, when totalling up a trial.
            if self._handler is not None:
                self._incomplete_frames = self._handler.incomplete_count
            self._handler = None
            self._is_streaming = False

    # -- reported state ----------------------------------------------------

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def is_streaming(self) -> bool:
        return self._is_streaming

    @property
    def resolution(self) -> tuple[int, int]:
        if self._resolution is None:
            raise CameraError("camera must be open to report its resolution")
        return self._resolution

    @property
    def pixel_format(self) -> PixelFormat:
        return self._target_pixel_format

    @property
    def frame_rate(self) -> float:
        """Read live, not cached.

        While ExposureAuto is on, the resulting rate tracks exposure and so
        drifts with scene brightness -- measured at 199.87 fps at open() and
        67.5 fps three seconds later on this camera. A value cached at open()
        would let preflight pass against a number the camera had already
        stopped honouring. Once the user set fixes exposure this is stable,
        but preflight must not depend on that being true.
        """
        import PySpin

        if not self._is_open:
            raise CameraError("camera must be open to report its frame rate")
        try:
            nodemap = self._camera.GetNodeMap()
            self._frame_rate = float(
                PySpin.CFloatPtr(nodemap.GetNode(NODE_RESULTING_FRAME_RATE)).GetValue()
            )
        except PySpin.SpinnakerException as exc:
            if self._frame_rate is None:
                raise CameraError(f"could not read frame rate: {exc}") from exc
            logger.warning("live frame-rate read failed, using last known: %s", exc)
        return self._frame_rate

    @property
    def incomplete_frame_count(self) -> int:
        if self._handler is not None:
            return int(self._handler.incomplete_count)
        return self._incomplete_frames


def _values_match(actual: str, expected: str) -> bool:
    """Compares a node reading to its expected value, tolerantly.

    Camera booleans read back as "True"/"False" while TOML writes `true`, and
    numeric nodes read back with float noise ("30.000000123"). Neither should
    be a preflight failure.
    """
    if actual.strip().lower() == expected.strip().lower():
        return True
    try:
        return abs(float(actual) - float(expected)) < 1e-6
    except ValueError:
        return False


_handler_class: Any = None


def _make_frame_event_handler(on_frame: FrameCallback, pixel_format: PixelFormat) -> Any:
    """Builds the image event handler that feeds ``on_frame``.

    The class derives from PySpin.ImageEventHandler, so it can only be defined
    once the SDK is imported -- hence a factory rather than a module-level
    class. That is what keeps this module importable with no SDK installed
    (invariant 2). The class is built once and cached.
    """
    global _handler_class

    import PySpin

    if _handler_class is None:
        _handler_class = _build_handler_class(PySpin)
    return _handler_class(on_frame, pixel_format)


def _build_handler_class(PySpin: Any) -> Any:
    class _Handler(PySpin.ImageEventHandler):  # type: ignore[misc, name-defined]
        def __init__(self, on_frame: FrameCallback, pixel_format: PixelFormat) -> None:
            super().__init__()
            self._on_frame = on_frame
            self._pixel_format = pixel_format
            self._target = (
                PySpin.PixelFormat_Mono8
                if pixel_format is PixelFormat.MONO8
                else PySpin.PixelFormat_BGR8
            )
            self._processor = PySpin.ImageProcessor()  # once, not per frame
            self.incomplete_count = 0

        def OnImageEvent(self, image: Any) -> None:  # noqa: N802 -- PySpin's signature
            try:
                if image.IsIncomplete():
                    self.incomplete_count += 1
                    logger.warning(
                        "incomplete image, status %s (total %d)",
                        image.GetImageStatus(), self.incomplete_count,
                    )
                    return

                chunk = image.GetChunkData()
                timestamp_ns = int(chunk.GetTimestamp())
                frame_id = int(chunk.GetFrameID())

                converted = self._processor.Convert(image, self._target)
                # COPY: GetNDArray() views a buffer the SDK recycles at
                # Release(), and frames outlive this callback in the pre-roll
                # deque and the writer queue. A view would alias overwritten
                # data -- corruption that scales with queue depth and looks
                # like a compression artifact.
                array = np.array(converted.GetNDArray(), copy=True)

                self._on_frame(
                    Frame(
                        image=array,
                        hardware_timestamp_ns=timestamp_ns,
                        frame_id=frame_id,
                        pixel_format=self._pixel_format,
                    )
                )
            except Exception:  # noqa: BLE001 -- must never escape into the SDK thread
                logger.exception("image event handler failed; frame dropped")
            finally:
                # Every path, always. Omitting this exhausts the camera's
                # buffer pool and acquisition stalls.
                try:
                    image.Release()
                except Exception:  # noqa: BLE001
                    logger.exception("image.Release() failed")

    return _Handler

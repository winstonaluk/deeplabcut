"""Camera abstraction. SpinnakerCamera and MockCamera both implement this.

Every acquisition invariant that mentions "the app must run with zero
hardware attached" (acquisition/CLAUDE.md invariant 2) depends on this ABC
having no assumptions specific to either implementation: no single-camera
assumptions (invariant 1), no polling (invariant 3 -- streaming is
event/callback driven), no exposed configuration surface (invariant 7 --
UserSet is loaded and verified, never edited here).

**The backend reports, the caller asserts.** ``resolution``, ``pixel_format``
and ``verify_settings`` exist because config.toml is not ground truth about
the hardware -- it is what we *intend* the hardware to be doing. Preflight
compares the two and blocks the session when they disagree. A 1280x720
literal meeting a 720x540 sensor produced no error at all before these
existed, just silently sheared video; see HARDWARE.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Mapping

from acquisition.frame import Frame, PixelFormat

FrameCallback = Callable[[Frame], None]


@dataclass(frozen=True)
class NodeCheck:
    """One camera setting read back and compared against its expected value.

    Values are compared and reported as strings deliberately: the expected
    side originates in config.toml's ``[camera_verify]`` table (invariant 9 --
    config over literals), and camera nodes are a mix of enumerations,
    booleans, integers and floats whose only common, loggable representation
    is their symbolic/string form.
    """

    node: str
    expected: str
    actual: str
    passed: bool

    def describe(self) -> str:
        if self.passed:
            return f"{self.node}: {self.actual}"
        return f"{self.node}: expected {self.expected!r}, got {self.actual!r}"


class CameraBackend(ABC):
    """One physical (or simulated) camera.

    Lifecycle: ``open()`` -> ``load_user_set()`` -> ``verify_settings()`` ->
    ``start_streaming()`` -> ... -> ``stop_streaming()`` -> ``close()``.
    Streaming delivers frames by invoking the caller's callback from the
    backend's own capture thread / SDK event handler -- callers must not poll.

    ``open()`` and ``close()`` are idempotent. Preflight opens the camera and,
    on success, leaves it open for the session; ``CaptureController.start()``
    then opens it again. Both paths are legitimate, so a second ``open()`` is
    a no-op rather than an error.
    """

    @abstractmethod
    def open(self) -> None:
        """Connects to the camera. Idempotent. Raises CameraError on failure."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Releases the camera. Safe to call if never opened or already closed."""
        ...

    @abstractmethod
    def load_user_set(self, user_set_name: str) -> bool:
        """Loads an onboard settings profile (e.g. "UserSet1").

        Never exposes exposure/gain/ROI/gamma/trigger as editable controls --
        those are set in SpinView and only loaded here (invariant 7).

        Returns True if the load itself succeeded, False otherwise. Never
        raises for a load failure; callers decide whether that blocks
        preflight. Whether the loaded values are *correct* is a separate
        question, answered by :meth:`verify_settings`.
        """
        ...

    @abstractmethod
    def verify_settings(self, expected: Mapping[str, str]) -> tuple[NodeCheck, ...]:
        """Reads back each named camera node and compares it to ``expected``.

        Read-only by construction: this reports what the camera says, and
        never writes a node to make a check pass. That is what keeps
        invariant 7 intact while still refusing to record against a camera
        whose exposure or frame rate is wrong.

        Returns one :class:`NodeCheck` per entry in ``expected``, in the same
        order. A node that cannot be read is a failed check, not an exception.
        """
        ...

    @abstractmethod
    def start_streaming(self, on_frame: FrameCallback) -> None:
        """Begins delivering frames to ``on_frame`` from the backend's own thread.

        Must not block the caller. Must not be polling-based (invariant 3).
        """
        ...

    @abstractmethod
    def stop_streaming(self) -> None:
        """Stops frame delivery. Idempotent if not currently streaming."""
        ...

    @property
    @abstractmethod
    def serial(self) -> str:
        """The camera's serial number (or a synthetic one for MockCamera)."""
        ...

    @property
    @abstractmethod
    def is_streaming(self) -> bool:
        ...

    @property
    @abstractmethod
    def resolution(self) -> tuple[int, int]:
        """``(width, height)`` actually being delivered, read from the camera.

        Not the configured resolution -- the real one. Preflight compares the
        two and blocks on a mismatch rather than trusting config.
        """
        ...

    @property
    @abstractmethod
    def pixel_format(self) -> PixelFormat:
        """The format frames are delivered in, after any backend conversion."""
        ...

    @property
    @abstractmethod
    def frame_rate(self) -> float:
        """The acquisition frame rate the camera reports, in frames per second.

        Compared numerically against ``capture.fps`` by preflight, within
        ``capture.fps_tolerance``. A camera left free-running delivers frames
        far faster than the rate stamped on the video file, which makes trial
        duration -- the primary dependent variable -- wrong when read off the
        video. So this is a blocking check, not an advisory one.
        """
        ...

    @property
    @abstractmethod
    def incomplete_frame_count(self) -> int:
        """Frames the camera delivered incomplete, and the backend discarded.

        Counted separately from the writer queue's dropped frames: a full
        queue means the encoder can't keep up, an incomplete frame means the
        camera-to-host link dropped data. Different causes, different fixes,
        so they never share a counter.
        """
        ...


class CameraError(RuntimeError):
    """A camera failed to open, load its UserSet, or stream."""

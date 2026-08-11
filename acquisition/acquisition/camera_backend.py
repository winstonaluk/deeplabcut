"""Camera abstraction. SpinnakerCamera and MockCamera both implement this.

Every acquisition invariant that mentions "the app must run with zero
hardware attached" (acquisition/CLAUDE.md invariant 2) depends on this ABC
having no assumptions specific to either implementation: no single-camera
assumptions (invariant 1), no polling (invariant 3 -- streaming is
event/callback driven), no exposed configuration surface (invariant 7 --
UserSet is loaded and verified, never edited here).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from acquisition.frame import Frame

FrameCallback = Callable[[Frame], None]


class CameraBackend(ABC):
    """One physical (or simulated) camera.

    Lifecycle: ``open()`` -> ``load_user_set()`` -> ``start_streaming()`` ->
    ... -> ``stop_streaming()`` -> ``close()``. Streaming delivers frames by
    invoking the caller's callback from the backend's own capture thread /
    SDK event handler -- callers must not poll.
    """

    @abstractmethod
    def open(self) -> None:
        """Connects to the camera. Raises CameraError on failure."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Releases the camera. Safe to call if never opened or already closed."""
        ...

    @abstractmethod
    def load_user_set(self, user_set_name: str) -> bool:
        """Loads an onboard settings profile (e.g. "UserSet1") and verifies it applied.

        Never exposes exposure/gain/ROI/gamma/trigger as editable controls --
        those are set in SpinView and only loaded here (invariant 7).

        Returns True if the load was verified, False otherwise. Never raises
        for a verification failure; callers decide whether that blocks
        preflight.
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


class CameraError(RuntimeError):
    """A camera failed to open, load its UserSet, or stream."""

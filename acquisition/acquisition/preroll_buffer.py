"""Rolling in-RAM buffer of the most recent N seconds, per camera.

Runs whenever streaming, not just during trials, so descent onset is never
clipped by the experimenter's reaction time to the spacebar. Backed by a
``deque(maxlen=...)`` so memory is naturally bounded regardless of how long
the camera has been streaming (invariant 10).
"""

from __future__ import annotations

import threading
from collections import deque

from acquisition.frame import Frame


class PreRollBuffer:
    def __init__(self, duration_s: float, fps: float) -> None:
        maxlen = max(1, round(duration_s * fps))
        self._buffer: deque[Frame] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def push(self, frame: Frame) -> None:
        with self._lock:
            self._buffer.append(frame)

    def snapshot(self) -> list[Frame]:
        """Frames in chronological order. Does not clear the buffer -- preroll
        keeps running regardless of trial state."""
        with self._lock:
            return list(self._buffer)

    @property
    def maxlen(self) -> int:
        return self._buffer.maxlen  # type: ignore[return-value]

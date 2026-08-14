"""Bounded, drop-on-full frame queue between capture and the writer thread.

Capture must never block (invariant 3). A full queue means the writer can't
keep up; the correct response is to drop the newest frame and count it, log
it, and keep going -- never grow unbounded and never block the capture
callback.
"""

from __future__ import annotations

import logging
import queue
import threading

from acquisition.frame import Frame

logger = logging.getLogger(__name__)


class BoundedFrameQueue:
    def __init__(self, maxsize: int) -> None:
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        self._queue: queue.Queue[Frame] = queue.Queue(maxsize=maxsize)
        self._dropped_count = 0
        self._lock = threading.Lock()

    def put_or_drop(self, frame: Frame) -> bool:
        """Enqueues ``frame``. Never blocks. Returns False and increments the
        drop counter if the queue is full."""
        try:
            self._queue.put_nowait(frame)
            return True
        except queue.Full:
            with self._lock:
                self._dropped_count += 1
            logger.warning(
                "frame queue full, dropping frame_id=%s (total dropped=%d)",
                frame.frame_id,
                self._dropped_count,
            )
            return False

    def get(self, timeout: float | None = None) -> Frame:
        """Blocks up to ``timeout`` seconds. Raises queue.Empty on timeout."""
        return self._queue.get(timeout=timeout)

    @property
    def dropped_count(self) -> int:
        with self._lock:
            return self._dropped_count

    @property
    def maxsize(self) -> int:
        return self._queue.maxsize

    def qsize(self) -> int:
        return self._queue.qsize()

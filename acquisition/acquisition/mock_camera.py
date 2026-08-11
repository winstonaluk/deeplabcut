"""Synthetic camera backend. The whole app must run against this with zero
hardware attached (acquisition/CLAUDE.md invariant 2).

Frames are Mono8 (single-channel uint8), matching the real camera's pixel
format. A moving diagonal gradient makes frame order/identity visually and
numerically verifiable in tests without needing real video content.
"""

from __future__ import annotations

import threading
import time

import numpy as np

from acquisition.camera_backend import CameraBackend, FrameCallback
from acquisition.frame import Frame


class MockCamera(CameraBackend):
    def __init__(
        self,
        serial: str,
        width: int,
        height: int,
        fps: float,
    ) -> None:
        self._serial = serial
        self._width = width
        self._height = height
        self._fps = fps
        self._is_open = False
        self._is_streaming = False
        self._user_set_loaded: str | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._next_frame_id = 0

    def open(self) -> None:
        self._is_open = True

    def close(self) -> None:
        if self._is_streaming:
            self.stop_streaming()
        self._is_open = False

    def load_user_set(self, user_set_name: str) -> bool:
        self._user_set_loaded = user_set_name
        return True  # MockCamera has nothing to actually verify against

    def start_streaming(self, on_frame: FrameCallback) -> None:
        if self._is_streaming:
            return
        self._stop_event.clear()
        self._is_streaming = True
        self._thread = threading.Thread(
            target=self._run,
            args=(on_frame,),
            name=f"MockCamera-{self._serial}",
            daemon=True,
        )
        self._thread.start()

    def stop_streaming(self) -> None:
        if not self._is_streaming:
            return
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        self._is_streaming = False

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def is_streaming(self) -> bool:
        return self._is_streaming

    def _run(self, on_frame: FrameCallback) -> None:
        period_s = 1.0 / self._fps
        next_tick = time.monotonic()
        while not self._stop_event.is_set():
            frame = self._make_frame()
            on_frame(frame)
            next_tick += period_s
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                self._stop_event.wait(sleep_for)
            else:
                # Fell behind (e.g. slow callback); resync rather than spin.
                next_tick = time.monotonic()

    def _make_frame(self) -> Frame:
        frame_id = self._next_frame_id
        self._next_frame_id += 1
        x = np.arange(self._width, dtype=np.int64)
        row = ((x + frame_id) % 256).astype(np.uint8)
        image = np.tile(row, (self._height, 1))
        return Frame(
            image=image,
            hardware_timestamp_ns=time.perf_counter_ns(),
            frame_id=frame_id,
        )

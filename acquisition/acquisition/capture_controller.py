"""Wires one CameraBackend's frame callback to the pre-roll buffer, a
latest-frame slot for preview, and (while a trial is recording) the writer's
bounded queue.

Recording integrity is independent of everything else (invariant 4): this
class has no dependency on the GUI or trial state machine. Something else
(A3's TrialStateMachine, wired at A5/A6) calls ``attach_sink`` /
``detach_sink`` around a trial's lifetime.
"""

from __future__ import annotations

import threading

from acquisition.camera_backend import CameraBackend
from acquisition.frame import Frame, PixelFormat
from acquisition.frame_queue import BoundedFrameQueue
from acquisition.preroll_buffer import PreRollBuffer


class CaptureController:
    def __init__(
        self,
        camera: CameraBackend,
        preroll_duration_s: float,
        fps: float,
    ) -> None:
        self._camera = camera
        self.preroll = PreRollBuffer(duration_s=preroll_duration_s, fps=fps)
        self._latest_frame_lock = threading.Lock()
        self._latest_frame: Frame | None = None
        self._sink_lock = threading.Lock()
        self._sink: BoundedFrameQueue | None = None

    def start(self) -> None:
        self._camera.open()
        self._camera.start_streaming(self._on_frame)

    def stop(self) -> None:
        self._camera.stop_streaming()
        self._camera.close()

    def attach_sink(self, sink: BoundedFrameQueue) -> None:
        """Begins forwarding frames to ``sink`` (a trial's writer queue)."""
        with self._sink_lock:
            self._sink = sink

    def detach_sink(self) -> None:
        with self._sink_lock:
            self._sink = None

    @property
    def resolution(self) -> tuple[int, int]:
        """What the camera is actually delivering -- the writer sizes its
        FFmpeg pipe from this, not from config (preflight has already
        confirmed the two agree)."""
        return self._camera.resolution

    @property
    def pixel_format(self) -> PixelFormat:
        return self._camera.pixel_format

    @property
    def incomplete_frame_count(self) -> int:
        return self._camera.incomplete_frame_count

    @property
    def latest_frame(self) -> Frame | None:
        """For preview only (invariant 5) -- reads the latest frame rather
        than consuming the write queue."""
        with self._latest_frame_lock:
            return self._latest_frame

    def _on_frame(self, frame: Frame) -> None:
        with self._latest_frame_lock:
            self._latest_frame = frame
        self.preroll.push(frame)
        with self._sink_lock:
            sink = self._sink
        if sink is not None:
            sink.put_or_drop(frame)

"""Wires one CameraBackend's frame callback to the pre-roll buffer, a
latest-frame slot for preview, and (while a trial is recording) the writer's
bounded queue.

Recording integrity is independent of everything else (invariant 4): this
class has no dependency on the GUI or trial state machine.
RecordingSessionController calls ``begin_trial`` / ``detach_sink`` around a
trial's lifetime.
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
        # Guards the pre-roll/sink handoff. _on_frame pushes to the pre-roll
        # and forwards to the sink under this one lock, and begin_trial
        # snapshots and attaches under it too, so each frame lands in exactly
        # one of "the snapshot" or "the queue": never neither (a frame-ID gap
        # at the pre-roll boundary) and never both (a duplicated frame).
        # Holding it in the capture callback does not block capture
        # (invariant 3): everything inside is non-blocking, and begin_trial
        # holds it only long enough to copy the pre-roll's frame references.
        self._sink_lock = threading.Lock()
        self._sink: BoundedFrameQueue | None = None

    def start(self) -> None:
        self._camera.open()
        self._camera.start_streaming(self._on_frame)

    def stop(self) -> None:
        self._camera.stop_streaming()
        self._camera.close()

    def begin_trial(self, sink: BoundedFrameQueue) -> list[Frame]:
        """Attaches ``sink`` and returns the pre-roll to prepend, atomically.

        The returned frames and the frames subsequently delivered to ``sink``
        are contiguous -- none missing between them, none in both. Calling
        ``preroll.snapshot()`` and ``attach_sink()`` separately does not
        guarantee that: a frame arriving between the two calls is lost or
        duplicated.
        """
        with self._sink_lock:
            frames = self.preroll.snapshot()
            self._sink = sink
        return frames

    def attach_sink(self, sink: BoundedFrameQueue) -> None:
        """Begins forwarding frames to ``sink`` with no pre-roll handoff.
        A trial with a pre-roll uses :meth:`begin_trial` instead."""
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
        with self._sink_lock:
            self.preroll.push(frame)
            if self._sink is not None:
                self._sink.put_or_drop(frame)

"""Consumes frames from a bounded queue and pipes them to FFmpeg as raw video.

Runs on its own thread so a slow encoder never blocks capture (invariant 3 --
the queue between them is what absorbs the mismatch, dropping on overflow).
Emits ``TimestampRow`` per written frame using the camera's own hardware
timestamp and frame ID, never host arrival time (invariant 6), using the
shared schema type directly rather than redefining it locally.
"""

from __future__ import annotations

import logging
import queue
import subprocess
import threading
from pathlib import Path

from acquisition.frame import Frame
from acquisition.frame_queue import BoundedFrameQueue
from schema.timestamps import TimestampRow

logger = logging.getLogger(__name__)


class WriterError(RuntimeError):
    """FFmpeg exited non-zero. Carries its stderr tail for diagnostics."""


class WriterThread(threading.Thread):
    def __init__(
        self,
        frame_queue: BoundedFrameQueue,
        output_path: Path,
        width: int,
        height: int,
        fps: float,
        codec: str,
        crf: int,
        pixel_format: str,
        preroll_frames: list[Frame] | None = None,
        poll_timeout_s: float = 0.5,
    ) -> None:
        super().__init__(name=f"Writer-{Path(output_path).name}", daemon=True)
        self._queue = frame_queue
        self._output_path = Path(output_path)
        self._width = width
        self._height = height
        self._fps = fps
        self._codec = codec
        self._crf = crf
        self._pixel_format = pixel_format
        self._preroll_frames = list(preroll_frames or [])
        self._poll_timeout_s = poll_timeout_s

        self._stop_requested = threading.Event()
        self._timestamp_rows: list[TimestampRow] = []
        self._process: subprocess.Popen | None = None
        self._returncode: int | None = None
        self._stderr_tail: str = ""
        self._run_error: Exception | None = None

    def stop(self) -> None:
        """Requests a clean shutdown: drain whatever is already queued, then
        close FFmpeg's stdin and wait for it to finish encoding."""
        self._stop_requested.set()

    @property
    def frames_written(self) -> int:
        return len(self._timestamp_rows)

    @property
    def timestamp_rows(self) -> list[TimestampRow]:
        return list(self._timestamp_rows)

    @property
    def returncode(self) -> int | None:
        return self._returncode

    @property
    def stderr_tail(self) -> str:
        return self._stderr_tail

    def raise_if_failed(self) -> None:
        if self._run_error is not None:
            raise self._run_error
        if self._returncode not in (None, 0):
            raise WriterError(
                f"ffmpeg exited {self._returncode} writing {self._output_path}: {self._stderr_tail}"
            )

    def run(self) -> None:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        # QSV encoders don't accept -crf (that's a libx264-family option) and
        # use a different quality knob; reusing the same config value keeps
        # config.toml's single "crf" key meaningful for either codec.
        quality_flag = "-global_quality" if self._codec.endswith("_qsv") else "-crf"
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo",
            "-pixel_format", "gray8",
            "-video_size", f"{self._width}x{self._height}",
            "-framerate", str(self._fps),
            "-i", "-",
            "-c:v", self._codec,
            quality_flag, str(self._crf),
            "-pix_fmt", self._pixel_format,
            str(self._output_path),
        ]
        try:
            self._process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            assert self._process.stdin is not None
            for frame in self._preroll_frames:
                self._write_frame(frame)
            while True:
                try:
                    frame = self._queue.get(timeout=self._poll_timeout_s)
                except queue.Empty:
                    if self._stop_requested.is_set():
                        break
                    continue
                self._write_frame(frame)
        except Exception as exc:  # noqa: BLE001 -- surfaced via raise_if_failed()
            self._run_error = exc
            logger.exception("writer thread failed for %s", self._output_path)
        finally:
            self._shutdown_process()

    def _write_frame(self, frame: Frame) -> None:
        index = len(self._timestamp_rows)
        self._process.stdin.write(frame.image.tobytes())  # type: ignore[union-attr]
        self._timestamp_rows.append(
            TimestampRow(
                frame_index=index,
                hardware_timestamp_ns=frame.hardware_timestamp_ns,
                frame_id=frame.frame_id,
            )
        )

    def _shutdown_process(self) -> None:
        if self._process is None:
            return
        if self._process.stdin is not None:
            try:
                self._process.stdin.close()
            except OSError:
                pass  # stdin already broken (e.g. ffmpeg exited early) -- communicate() below still reaps it
        try:
            _, stderr = self._process.communicate(timeout=30)
            self._returncode = self._process.returncode
            self._stderr_tail = (stderr or b"").decode("utf-8", errors="replace")[-2000:]
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._returncode = self._process.wait()
            self._stderr_tail = "ffmpeg did not exit within timeout; killed"

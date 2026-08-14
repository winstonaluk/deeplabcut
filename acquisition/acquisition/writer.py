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

from acquisition.frame import Frame, PixelFormat
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
        source_pixel_format: PixelFormat = PixelFormat.MONO8,
        quality_flag: str | None = None,
        preset: str | None = None,
        gop: int | None = None,
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
        self._source_pixel_format = source_pixel_format
        self._quality_flag = quality_flag
        self._preset = preset
        self._gop = gop
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

    def build_command(self) -> list[str]:
        """The FFmpeg invocation for this trial.

        Separated from :meth:`run` so it is assertable in tests without
        spawning a process -- the flags here decide both recording quality and
        file size, and getting one of them silently wrong (a QSV encoder handed
        an x264 quality scale, say) is not visible until you compare footage.
        """
        # QSV takes -global_quality, the x264 family takes -crf, and the two
        # scales are not interchangeable. The caller normally supplies the
        # right flag from EncoderConfig.quality_for(); this derivation is the
        # fallback for callers that don't.
        quality_flag = self._quality_flag or (
            "-global_quality" if self._codec.endswith("_qsv") else "-crf"
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo",
            # Derived from what the backend actually delivers, never assumed:
            # the rig's camera is a colour sensor, and a hardcoded gray8 here
            # would misread every byte it produced.
            "-pixel_format", self._source_pixel_format.ffmpeg_pixel_format,
            "-video_size", f"{self._width}x{self._height}",
            "-framerate", str(self._fps),
            "-i", "-",
            "-c:v", self._codec,
            quality_flag, str(self._crf),
        ]
        if self._preset:
            cmd += ["-preset", self._preset]
        if self._gop:
            cmd += ["-g", str(self._gop)]
        cmd += ["-pix_fmt", self._pixel_format, str(self._output_path)]
        return cmd

    def run(self) -> None:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = self.build_command()
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
        if index == 0:
            self._assert_frame_matches_pipe(frame)
        self._process.stdin.write(frame.image.tobytes())  # type: ignore[union-attr]
        self._timestamp_rows.append(
            TimestampRow(
                frame_index=index,
                hardware_timestamp_ns=frame.hardware_timestamp_ns,
                frame_id=frame.frame_id,
            )
        )

    def _assert_frame_matches_pipe(self, frame: Frame) -> None:
        """Fails loudly on the first frame if its geometry doesn't match what
        FFmpeg was told to expect.

        FFmpeg does not error on a size mismatch -- rawvideo has no framing, so
        it just re-slices the byte stream and produces sheared video that looks
        like a codec problem. A 1280x720 config value meeting a 720x540 sensor
        did exactly that, undetected; this is the guard for it.
        """
        expected_shape = self._source_pixel_format.expected_shape(self._width, self._height)
        if frame.pixel_format is not self._source_pixel_format:
            raise WriterError(
                f"{self._output_path}: writer configured for "
                f"{self._source_pixel_format.value} but frames arrived as "
                f"{frame.pixel_format.value}"
            )
        if frame.image.shape != expected_shape:
            raise WriterError(
                f"{self._output_path}: FFmpeg expects {expected_shape} frames "
                f"({self._width}x{self._height} {self._source_pixel_format.value}) "
                f"but the camera delivered {frame.image.shape}. Check capture.width "
                f"and capture.height in config.toml against the camera's actual sensor."
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

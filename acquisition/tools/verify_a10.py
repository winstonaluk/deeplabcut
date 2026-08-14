"""Checkpoint A10 verification: record from the real camera and check the result.

    python tools/verify_a10.py                 # 60 s, per config.toml
    python tools/verify_a10.py --seconds 10    # shorter shakedown
    python tools/verify_a10.py --keep          # don't delete the recording

Drives the real pipeline end to end -- SpinnakerCamera -> preflight ->
CaptureController -> BoundedFrameQueue -> WriterThread -> FFmpeg -- then checks
A10's done-criteria:

  * preflight passes against config, including every [camera_verify] node
  * frames written matches the configured rate over the recording window
  * hardware timestamps strictly increasing
  * frame IDs contiguous -- no gaps
  * zero incomplete frames and zero queue drops
  * the file is playable and ffprobe reports the configured geometry and rate

This is a standalone tool rather than a test because it needs the camera, and
standalone rather than `python -m app` because the application has no
composition root yet -- nothing outside tests currently assembles a camera and
a controller. See the "Flagged" note in the A10 plan.

Every check runs even if an earlier one fails, so one run tells you everything
that is wrong. Exit code is 0 only if all of them pass.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

# Make the acquisition package importable when run as `python tools/verify_a10.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from acquisition.camera_backend import CameraError  # noqa: E402
from acquisition.capture_controller import CaptureController  # noqa: E402
from acquisition.encoder import resolve_encoder  # noqa: E402
from acquisition.frame_queue import BoundedFrameQueue  # noqa: E402
from acquisition.preflight import run_preflight_checks  # noqa: E402
from acquisition.spinnaker_camera import SpinnakerCamera  # noqa: E402
from acquisition.writer import WriterThread  # noqa: E402
from app.config import load_config  # noqa: E402

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


class Report:
    """Collects pass/fail lines so one run reports every problem at once."""

    def __init__(self) -> None:
        self.rows: list[tuple[bool, str, str]] = []

    def check(self, passed: bool, name: str, detail: str = "") -> bool:
        self.rows.append((bool(passed), name, detail))
        return bool(passed)

    @property
    def ok(self) -> bool:
        return all(passed for passed, _, _ in self.rows)

    def render(self) -> str:
        width = max((len(name) for _, name, _ in self.rows), default=0)
        lines = []
        for passed, name, detail in self.rows:
            mark = "PASS" if passed else "FAIL"
            lines.append(f"  [{mark}] {name:<{width}}  {detail}")
        return "\n".join(lines)


def ffprobe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-hide_banner", "-loglevel", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_frames,pix_fmt",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "replace")[-400:])
    return json.loads(result.stdout.decode("utf-8", "replace"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Checkpoint A10 hardware verification")
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--out", type=Path, default=None, help="output path (default: temp)")
    parser.add_argument("--keep", action="store_true", help="keep the recording")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    config = load_config(args.config)
    camera_config = config.cameras[0]
    capture = config.capture
    report = Report()

    output = args.out or Path(__file__).resolve().parent.parent / "verify_a10_output.mp4"

    camera = SpinnakerCamera(
        serial=camera_config.serial,
        pixel_format=capture.source_pixel_format,
        stream_buffer_count=capture.stream_buffer_count,
    )

    print(f"\n=== A10 verification: {args.seconds:g}s from camera {camera_config.serial} ===\n")

    # -- preflight ---------------------------------------------------------
    preflight = run_preflight_checks(
        camera,
        camera_config.user_set,
        output.parent,
        config.storage.min_free_gb,
        expected_resolution=capture.resolution,
        expected_fps=float(capture.fps),
        fps_tolerance=capture.fps_tolerance,
        expected_nodes=config.camera_verify,
    )
    for check in preflight.checks:
        report.check(check.passed, check.name, check.detail)

    # run_preflight_checks() closes the camera on any failure, so re-open before
    # recording. open() is idempotent, so this is a no-op when preflight passed.
    # Recording still proceeds after a preflight failure on purpose: today's
    # expected failure is an unconfigured UserSet1, and everything downstream of
    # it is still worth measuring in the same run. The overall result stays FAIL.
    try:
        camera.open()
    except CameraError as exc:
        print(report.render())
        print(f"\nCamera could not be opened: {exc}")
        return 1

    # -- record ------------------------------------------------------------
    codec = resolve_encoder(config.encoder.codec, config.encoder.fallback_codec)
    quality_flag, quality_value = config.encoder.quality_for(codec)
    width, height = camera.resolution

    controller = CaptureController(
        camera, preroll_duration_s=capture.preroll_buffer_s, fps=capture.fps
    )
    queue = BoundedFrameQueue(maxsize=capture.queue_maxsize)
    writer = WriterThread(
        frame_queue=queue,
        output_path=output,
        width=width,
        height=height,
        fps=capture.fps,
        codec=codec,
        crf=quality_value,
        pixel_format=config.encoder.pixel_format,
        source_pixel_format=camera.pixel_format,
        quality_flag=quality_flag,
        preset=config.encoder.preset_for(codec),
        gop=max(1, round(config.encoder.keyframe_interval_s * capture.fps)),
    )

    print(f"\nrecording {args.seconds:g}s with {codec} {quality_flag}={quality_value} ...\n")
    controller.start()
    time.sleep(capture.preroll_buffer_s)  # let the pre-roll fill, as a trial would
    writer.start()
    controller.attach_sink(queue)
    started = time.monotonic()
    time.sleep(args.seconds)
    elapsed = time.monotonic() - started
    controller.detach_sink()
    writer.stop()
    writer.join(timeout=60)
    incomplete = camera.incomplete_frame_count
    controller.stop()

    # -- checks ------------------------------------------------------------
    try:
        writer.raise_if_failed()
        report.check(True, "FFmpeg exited cleanly", f"returncode {writer.returncode}")
    except Exception as exc:  # noqa: BLE001 -- reported, not raised
        report.check(False, "FFmpeg exited cleanly", str(exc))

    rows = writer.timestamp_rows
    report.check(len(rows) > 0, "Frames written", f"{len(rows)} frames in {elapsed:.1f}s")

    expected_frames = capture.fps * elapsed
    if rows:
        ratio = len(rows) / expected_frames if expected_frames else 0.0
        report.check(
            0.95 <= ratio <= 1.05,
            "Frame count matches configured rate",
            f"{len(rows)} written vs {expected_frames:.0f} expected ({ratio:.2f}x)",
        )

        timestamps = [r.hardware_timestamp_ns for r in rows]
        non_monotonic = sum(1 for a, b in zip(timestamps, timestamps[1:]) if b <= a)
        report.check(
            non_monotonic == 0,
            "Hardware timestamps strictly increasing",
            f"{non_monotonic} non-increasing steps",
        )

        ids = [r.frame_id for r in rows]
        gaps = [(a, b) for a, b in zip(ids, ids[1:]) if b - a != 1]
        report.check(
            not gaps,
            "Frame IDs contiguous",
            "no gaps" if not gaps else f"{len(gaps)} gaps, first {gaps[0]}",
        )

        span_s = (timestamps[-1] - timestamps[0]) / 1e9
        measured = (len(rows) - 1) / span_s if span_s > 0 else 0.0
        report.check(
            abs(measured - capture.fps) <= capture.fps_tolerance,
            "Rate from hardware timestamps",
            f"{measured:.2f} fps vs {capture.fps} configured",
        )

    report.check(incomplete == 0, "No incomplete frames", f"{incomplete} incomplete")
    report.check(
        queue.dropped_count == 0, "No dropped frames", f"{queue.dropped_count} dropped"
    )

    # -- the file itself ---------------------------------------------------
    if output.is_file() and output.stat().st_size > 0:
        size_mb = output.stat().st_size / 1e6
        rate_mb_min = size_mb / (elapsed / 60) if elapsed else 0.0
        report.check(True, "Output file written", f"{size_mb:.1f} MB ({rate_mb_min:.1f} MB/min)")
        try:
            probe = ffprobe(output)
            stream = probe["streams"][0]
            report.check(
                (stream["width"], stream["height"]) == (width, height),
                "ffprobe geometry",
                f"{stream['width']}x{stream['height']}",
            )
            duration = float(probe["format"]["duration"])
            report.check(
                abs(duration - elapsed) / elapsed < 0.1 if elapsed else False,
                "ffprobe duration matches wall clock",
                f"{duration:.1f}s file vs {elapsed:.1f}s recorded",
            )
        except (RuntimeError, KeyError, IndexError, ValueError) as exc:
            report.check(False, "ffprobe readable", str(exc))
    else:
        report.check(False, "Output file written", "missing or empty")

    print("\n=== results ===")
    print(report.render())

    if not args.keep and output.is_file():
        output.unlink()
        print(f"\n(removed {output.name}; pass --keep to retain it)")
    elif output.is_file():
        print(f"\nrecording kept at {output}")

    print("\nA10: " + ("PASS" if report.ok else "FAIL"))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())

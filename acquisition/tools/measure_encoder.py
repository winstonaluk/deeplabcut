"""Sweep encoder settings over real footage and report size against quality.

    python tools/measure_encoder.py REFERENCE.mp4

`config.toml`'s `crf` / `qsv_global_quality` / `preset` values are starting
points, not measurements. This script produces the measurements: it re-encodes
one reference clip across a grid of codec x quality x preset and prints file
size and SSIM against the source, so the quality/size trade-off can be chosen
from data instead of from a guess about what "CRF 20" looks like on a
720x540 grayscale rat.

Use a reference clip that is representative: one real trial, with an animal
actually descending. A static clip compresses far better than real footage and
will flatter every setting equally.

**Not yet run against anything** -- FFmpeg is not installed on the acquisition
PC as of 2026-08-14, which is also why it lives in tools/ rather than in the
test suite. Treat the first run as a shakedown of this script as well as of the
encoders.

Reading the output: pick the largest quality number (smallest file) whose SSIM
is still above what DLC needs. SSIM is a proxy, not the answer -- confirm the
winner by actually labelling a few frames from it, since keypoint accuracy is
what matters here and no full-frame metric measures that directly.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Kept small on purpose: a full sweep of a multi-minute clip takes a while, and
# these bracket the useful range for grayscale 720x540.
QUALITIES = (18, 20, 22, 24, 26)
X264_PRESETS = ("medium", "slow", "veryslow")
QSV_PRESETS = ("medium", "slower")


def ssim_and_size(reference: Path, codec: str, quality: int, preset: str) -> tuple[float, int, float]:
    """Encodes once and returns (ssim, bytes, encode_seconds)."""
    flag = "-global_quality" if codec.endswith("_qsv") else "-crf"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "encoded.mp4"
        import time

        start = time.monotonic()
        encode = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(reference),
             "-c:v", codec, flag, str(quality), "-preset", preset,
             "-g", "120", "-pix_fmt", "yuv420p", str(out)],
            capture_output=True,
        )
        elapsed = time.monotonic() - start
        if encode.returncode != 0:
            raise RuntimeError(encode.stderr.decode("utf-8", "replace")[-500:])

        size = out.stat().st_size
        measure = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(out), "-i", str(reference),
             "-lavfi", "ssim", "-f", "null", "-"],
            capture_output=True,
        )
        text = measure.stderr.decode("utf-8", "replace")
        match = re.search(r"All:\s*([0-9.]+)", text)
        if match is None:
            raise RuntimeError(f"could not parse SSIM from:\n{text[-500:]}")
        return float(match.group(1)), size, elapsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="a representative real trial recording")
    parser.add_argument("--codecs", nargs="+", default=["libx264", "h264_qsv"])
    args = parser.parse_args(argv)

    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found on PATH -- install it first (needs h264_qsv support).")
        return 2
    if not args.reference.is_file():
        print(f"no such file: {args.reference}")
        return 2

    source_size = args.reference.stat().st_size
    duration_hint = ""
    print(f"reference: {args.reference}  ({source_size / 1e6:.1f} MB){duration_hint}\n")
    print(f"{'codec':<10} {'preset':<10} {'quality':>7} {'MB':>8} {'MB/min':>8} {'SSIM':>7} {'enc s':>7}")
    print("-" * 62)

    for codec in args.codecs:
        presets = QSV_PRESETS if codec.endswith("_qsv") else X264_PRESETS
        for preset in presets:
            for quality in QUALITIES:
                try:
                    ssim, size, elapsed = ssim_and_size(args.reference, codec, quality, preset)
                except RuntimeError as exc:
                    print(f"{codec:<10} {preset:<10} {quality:>7}   failed: {exc}")
                    continue
                # MB/min needs the clip duration; approximate from encode input
                # rather than probing separately -- the ratio to the reference
                # is what actually matters for choosing.
                ratio = size / source_size if source_size else 0.0
                print(
                    f"{codec:<10} {preset:<10} {quality:>7} {size / 1e6:>8.1f} "
                    f"{ratio:>8.2f}x {ssim:>7.4f} {elapsed:>7.1f}"
                )
    print("\n'MB/min' column is size relative to the reference file, not absolute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

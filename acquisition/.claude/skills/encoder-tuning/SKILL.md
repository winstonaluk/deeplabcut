---
name: encoder-tuning
description: How to tune the acquisition encoder for smallest files that still support accurate DeepLabCut keypoints — which levers matter and in what order (exposure, resolution, quality, preset, codec), and how to measure rather than guess with tools/measure_encoder.py. Use when changing codec, crf/qsv_global_quality, preset, resolution, fps, or exposure, or when video files are too large or keypoint accuracy is degrading.
---

# Encoder tuning

Goal: smallest files that still support accurate DLC keypoints. The levers, in
descending order of how much they actually matter:

1. **Exposure time — not a codec setting at all.** Auto-exposure is on, so the
   value floats: it read 15 ms on one probe and 1 ms on another with nothing
   changed but ambient light. A rat descending a pole moves visibly within
   15 ms, and that motion blur destroys keypoint precision in a way no encoder
   setting recovers and no bitrate compensates for. **Fix the exposure, make it
   short (single-digit ms), and pay for it with light and gain rather than with
   CRF.** Blur also makes frames *harder* to compress, so this is the rare
   change that improves quality and size together. SpinView, saved to
   `UserSet1`.
2. **Resolution.** 720 × 540 is already the full sensor; there is nothing to
   give back here without cropping to an ROI. If the animal occupies a
   predictable part of the frame, an ROI in `UserSet1` is the single largest
   size saving available — and it raises the achievable frame rate too.
3. **Quality (`crf` / `qsv_global_quality`).** The obvious knob and the one to
   tune last, from measurement.
4. **Preset.** Slower presets are strictly better bytes-per-quality, paid in
   CPU. Free quality if the writer keeps up.
5. **Codec choice.** `h264_qsv` is fixed-function: fast, near-zero CPU, and
   less efficient per bit than `libx264` at a slow preset. At 720 × 540 / 30 fps
   the software encoder may well keep up on the i7-7700 and produce smaller
   files — worth measuring before assuming Quick Sync is the right default.
   Whichever wins, the writer must sustain throughput with no dropped frames.

**Measure, don't guess:** `python tools/measure_encoder.py REFERENCE.mp4` sweeps
codec × quality × preset over one real trial and reports size and SSIM. Use real
footage with an animal moving; a static clip flatters every setting equally.
SSIM is a proxy — confirm the winner by labelling a few frames from it, since
keypoint accuracy is the actual criterion and no full-frame metric measures it.

30 fps is ample for PDCT descent kinematics. Raising it costs size linearly and
buys nothing for this paradigm; it is a config value if a future one needs it.

Quality is configured **per codec** — `-crf` and `-global_quality` are different
scales and a shared number gives two different qualities depending on which
encoder resolved. Every setting reaches code via `config.toml` (invariant 9).

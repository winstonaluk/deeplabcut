---
name: encoder-tuning
description: How to tune the acquisition encoder for smallest files that still support accurate DeepLabCut keypoints — which levers matter and in what order (exposure, resolution, quality, preset, codec), and how to measure rather than guess with tools/measure_encoder.py. Use when changing codec, crf, preset, resolution, fps, or exposure; when video files are too large or keypoint accuracy is degrading; when adding a camera; or when encoding competes with DLC-Live inference for CPU.
---

# Encoder tuning

Goal: smallest files that still support accurate DLC keypoints.

**Read this first: there is no hardware video encoder on the target machine.**
The Jetson Orin Nano omits the NVENC silicon — it is a cost-reduced derivative
of the Orin SoC, `nvv4l2h264enc` is not registered in GStreamer, and reflashing
cannot add it. Every H.264 frame is encoded by **`libx264` on 6 Cortex-A78AE
cores**, and those are the same cores running DLC-Live inference and the capture
callback. Do not reach for `h264_nvenc` (absent) or `h264_qsv` (Intel Quick
Sync, belonged to the retired i7-7700 host). `resolve_encoder()` probes and
falls back, so a stale config resolves to `libx264` rather than failing — which
means a wrong codec setting is silent, not loud.

The levers, in descending order of how much they actually matter:

1. **Exposure time — not a codec setting at all.** Auto-exposure is on, so the
   value floats: it read 15 ms on one probe and 1 ms on another with nothing
   changed but ambient light. A rat descending a pole moves visibly within
   15 ms, and that motion blur destroys keypoint precision in a way no encoder
   setting recovers and no bitrate compensates for. **Fix the exposure, make it
   short (single-digit ms), and pay for it with light and gain rather than with
   CRF.** Blur also makes frames *harder* to compress, so this is the rare
   change that improves quality and size together. SpinView, saved to
   `UserSet1`.
2. **Camera count.** Each camera is a full independent `libx264` process. N
   cameras multiply encode cost on a fixed 6 cores, and this is the lever most
   likely to be the binding constraint now — it can outrank everything below it.
   Measure encode headroom before adding a camera, not after.
3. **Resolution.** `UserSet1` holds a **680 × 460 ROI** inside the sensor's
   720 × 540 (configured 2026-09-10). Further cropping is the single largest
   size saving still available, and it raises the achievable frame rate too.
4. **Preset.** This used to be free quality. **It is not any more.** On the old
   host, Quick Sync did the work in fixed-function silicon and a slow preset
   cost nothing that mattered. On the Jetson, preset is the main CPU cost of
   encoding, and it trades directly against DLC-Live inference headroom on the
   same cores. A slower preset can starve a latency-critical stop predicate or a
   stimulation trigger. Treat preset as a *latency* decision, not just a
   size/CPU one.
5. **Quality (`crf`).** The obvious knob and still the one to tune last, from
   measurement.

Pin CPU affinity so encoding cannot starve the closed loop: give the FFmpeg
processes a fixed subset of cores and leave the rest to inference and capture.
An unpinned encode burst shows up as jitter in inference latency.

**Measure, don't guess:** `python tools/measure_encoder.py REFERENCE.mp4` sweeps
quality × preset over one real trial and reports size and SSIM. Use real footage
with an animal moving; a static clip flatters every setting equally. SSIM is a
proxy — confirm the winner by labelling a few frames from it, since keypoint
accuracy is the actual criterion and no full-frame metric measures it.

**Run it on the Jetson, under simultaneous inference load.** A throughput number
measured on an idle board, or on any x86 machine, says nothing about the
configuration that has to survive a real session. This tool has never been run.

If `libx264` cannot sustain N cameras at acceptable quality, the fallback is to
record a fast intermediate (`-preset ultrafast`, higher bitrate) and transcode
during staging on the analysis machine — `storage/staging.py` already exists.

30 fps is ample for PDCT descent kinematics. Raising it costs size linearly and
buys nothing for this paradigm; it is a config value if a future one needs it.

Quality is still configured **per codec** in `config.toml`: `-crf` and
`-global_quality` are different scales, and a shared number gives two different
qualities depending on which encoder resolved. The `qsv_global_quality` key is
now dead on this hardware but the per-codec *structure* stays — it is what
stopped one number from silently meaning two things. Every setting reaches code
via `config.toml` (invariant 9).

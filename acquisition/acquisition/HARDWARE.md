# The rig camera, as measured

Everything in this file was read off the camera on **2026-08-14** with the
probe scripts in `acquisition/tools/`. It exists because these readings cannot
be reproduced anywhere except the acquisition PC with the camera attached, and
several of them contradict what `acquisition/CLAUDE.md` and `config.toml` said
before this pass. **When this file and a design document disagree, this file
wins** — it is the measurement, not the intention.

Re-run `python tools/probe_camera.py` after any firmware change, camera swap,
or SpinView reconfiguration, and update this file with what it prints.

## Identity

| | |
|---|---|
| Model | Blackfly S **BFS-U3-04S2C** (Sony IMX287, 0.4 MP) |
| Serial | `22514545` |
| Interface | **USB3Vision**, SuperSpeed |
| Device version | `1707.1.6.0` |
| SDK / bindings | Spinnaker **4.3.0.190**, `spinnaker_python` cp310 wheel |
| Host Python | 3.10.0 (conda env `acquire`), numpy 1.26.4 |

The trailing `C` in the model number is **colour**. The `cp310` wheel is why
the acquisition PC is pinned to Python 3.10 — PySpin wheels are built per
Python version, and the SDK we have ships no 3.11 build.

## Sensor and format

| Node | Value |
|---|---|
| `SensorWidth` × `SensorHeight` | **720 × 540** |
| `WidthMax` × `HeightMax` | 720 × 540 |
| `PixelFormat` (as found) | `BayerRG8` |
| `PixelColorFilter` | `BayerRG` |
| `AdcBitDepth` | `Bit8` |
| `SensorShutterMode` | `Global` |
| `Binning` H/V | 1 / 1 |

`PixelFormat` offers `Mono8`, `Mono16`, `BayerRG8/16`, `RGB8Packed`, `BGR8`,
`BGRa8`, the `YCbCr`/`YUV` family, and packed variants.

**The sensor is 720 × 540, not 1280 × 720.** The "720p60" line in the hardware
notes appears to have been a misreading of "720 × 540". Consequences that
followed from the old number, now corrected:

- Raw rate at 30 fps Mono8 is **11.7 MB/s**, not the ~25 MB/s implied by 720p.
- The 2 s pre-roll is **~23 MB per camera**, not the ~55 MB documented.
- Encoded storage per trial is correspondingly smaller than the ~37 MB/min
  estimate, which was computed for 1280 × 720.

Because the sensor is colour, `Mono8` output is **luma derived from the Bayer
mosaic**, not a native monochrome readout — slightly softer than a true mono
sensor at the same pixel count. Fine for DLC; worth knowing when comparing
against literature that used mono cameras.

## Acquisition state as found

These are the values the camera powers up with, because `UserSetDefault` is
`Default` — it does **not** boot into `UserSet1`.

| Node | As found | Wanted | Why it matters |
|---|---|---|---|
| `AcquisitionFrameRateEnable` | `False` | `True` | Unlatched rate means the file's stamped fps is fiction |
| `AcquisitionResultingFrameRate` | **66.12** | 30 | Free-running, exposure-limited |
| `AcquisitionFrameRate` | 199.93 | 30 | Ceiling, not the achieved rate |
| `ExposureAuto` | `Continuous` | `Off` | Appearance tracks the animal's position on the pole |
| `ExposureTime` | 14999 µs | fixed | 15 ms exposure is what caps the rate at 66 fps |
| `GainAuto` | `Continuous` | `Off` | Same covariance problem as auto-exposure |
| `Gain` | 10.80 dB | fixed | |
| `GammaEnable` / `Gamma` | `True` / 0.80 | `False` | Nonlinearity between sensor and training data |
| `BlackLevel` | 0.0 | — | |
| `TriggerMode` | `Off` | `Off` | Free-running is correct for us |
| `AcquisitionMode` | `Continuous` | `Continuous` | Correct |

Auto-exposure and auto-gain are the scientifically load-bearing ones: they
re-tune continuously as the rat descends, so image appearance covaries with
the very thing DLC is being trained to locate.

## Chunk data — off as shipped, enabled by the app at open()

| Chunk | Enabled |
|---|---|
| `Image` | True |
| `CRC` | True |
| **`FrameID`** | **False** |
| **`Timestamp`** | **False** |
| everything else | False |

`ChunkModeActive` is `False`.

Invariant 6 ("hardware timestamps only") is **unsatisfiable in this state** —
`GetChunkData().GetTimestamp()` and `GetFrameID()` have nothing behind them
until chunk mode and both chunks are enabled. `ChunkModeActive` is writable, so
the backend can and must enable them; see `SPINNAKER_PLAN.md` and the invariant
7 note in `acquisition/CLAUDE.md`.

`TimestampIncrement` reads **1000**, i.e. the counter has 1 µs resolution but is
expressed in nanoseconds — so `Frame.hardware_timestamp_ns` needs no scaling on
this camera. Read the node at open() rather than hardcoding that, since it is a
per-model property.

## Stream buffers (transport layer)

| Node | As found | Wanted |
|---|---|---|
| `StreamBufferHandlingMode` | `OldestFirst` | `OldestFirst` |
| `StreamBufferCountMode` | `Manual` | `Manual` |
| `StreamBufferCountManual` | 10 | 64 (`capture.stream_buffer_count`) |
| range | 1 – 11466 | |

Available handling modes: `OldestFirst`, `OldestFirstOverwrite`, `NewestOnly`,
`NewestFirst`.

**These live in the transport-layer stream nodemap, which user sets do not
cover.** The app must set them itself, so there is no invariant 7 tension here
at all. `OldestFirst` back-pressures rather than discarding and is what a
recorder wants; `NewestOnly` silently drops frames and is what the SDK's own
`AcquireAndDisplay.py` uses, correctly, for a live viewer.

Ten buffers is ~0.33 s of slack at 30 fps. 64 gives ~2 s.

## Link budget

| Node | Value |
|---|---|
| `DeviceLinkThroughputLimit` | 380 MB/s |
| `DeviceLinkCurrentThroughput` | 25.7 MB/s |
| `DeviceMaxThroughput` | 77.8 MB/s |

We need ~11.7 MB/s at 720 × 540 Mono8 30 fps. Enormous headroom.

This is a **USB3 camera**, so the GigE-specific guidance that used to be in
`SPINNAKER_PLAN.md` (jumbo frames, MTU, packet size, firewall exceptions) does
not apply and has been removed.

## Resolved: the "read-only nodes" symptom is a parameter lock

**Symptom.** `UserSetLoad`, `UserSetSave`, `PixelFormat`, `Width` and `Height`
all report GenICam access mode **RO (3)** together, and `Execute()` raises:

```
GenICam::AccessException= Node is not writable. :
AccessException thrown in node 'UserSetLoad' while calling 'UserSetLoad.Execute()'
```

**Cause: another Spinnaker session has the camera's parameters latched** —
SpinView left open, or a script that exited without `EndAcquisition()`/`DeInit()`.
While acquisition is armed, FLIR locks the image-format nodes and the user-set
commands *as a group*. When that session ends, every one of them returns to RW.
Verified 2026-08-14: RO while a stream was live, RW afterwards, nothing else
changed.

**This was originally misdiagnosed here** as a camera fault, on the strength of
`DeviceAccessStatus == OpenReadWrite`, `StreamIsGrabbing == False` and
`TLParamsLocked == 0`. Those three are **host-side state for the probing
process** — none of them can see a *different* process holding the camera. Do
not repeat that inference. The reliable test is simply whether the whole cluster
of nodes is RO at once, which is what `tools/probe_camera.py`'s ACCESS MODES
section reports.

**It will recur**, so the app handles it: `SpinnakerCamera.load_user_set()`
checks `IsWritable` before executing and surfaces "camera parameters are locked
— another application (e.g. SpinView) may be streaming from this camera" through
preflight, instead of letting an `AccessException` escape. `close()` always
tears down, including on error paths, so this app does not become the thing that
leaves the camera latched for the next run.

**Close SpinView before running anything that talks to the camera.**

## `UserSet1` as configured (2026-09-10)

Set in SpinView, saved to `UserSet1`, and made the power-on default. Read back
after `UserSetLoad` on 2026-09-10; `tools/verify_a10.py` passes every
`[camera_verify]` check against it.

| Node | Value | Note |
|---|---|---|
| `UserSetDefault` | `UserSet1` | The camera now boots into the configured set |
| `Width` × `Height` | **680 × 460** | ROI at offset (0, 0) inside the 720 × 540 sensor; may become square later |
| `PixelFormat` | `Mono8` | |
| `ExposureAuto` / `ExposureTime` | `Off` / **8.94 ms** | Fixed and single-digit ms, as "Encoder tuning" asks |
| `GainAuto` / `Gain` | `Off` / **34.7 dB** | Fixed, but high -- see below |
| `GammaEnable` | `False` | |
| `BlackLevel` | 10.0 | 0.0 at factory |
| `AcquisitionFrameRateEnable` / rate | `True` / **29.996** | Latched; the resulting rate matches |
| `SensorShutterMode` / `TriggerMode` | `Global` / `Off` | |

SpinView displays the set as **"User Set 1"**; the node's symbolic name is
`UserSet1`. `config.toml` accepts either -- `SpinnakerCamera` matches enum
entries by symbolic or display name, ignoring case and spacing.

**Gain is the open item.** 34.7 dB is roughly 54× amplification. Recordings
now run at **~55–60 MB/min at 30 fps**, about ten times the 5.6 MB/min
measured at factory settings (10.8 dB gain, 66 fps), so a 5-minute trial is
~300 MB. Sensor noise does not compress, and gain is the most likely cause.
More light and less gain is the lever: it cuts file size and the noise in the
DLC training data together. Re-measure after changing it.

## History: `UserSet1` held factory defaults until 2026-09-10

Read 2026-08-14 with `tools/probe_camera.py --dump-user-sets`. `Default`,
`UserSet0` and `UserSet1` are **identical, and all three are factory defaults**:
`BayerRG8`, `ExposureAuto` and `GainAuto` `Continuous`, `GammaEnable` True at
0.80, `AcquisitionFrameRateEnable` False, `ChunkModeActive` False.

So `config.toml`'s `user_set = "UserSet1"` currently loads factory settings, and
preflight correctly fails every `[camera_verify]` check that matters. Configuring
it in SpinView is real outstanding work, not a formality — see the checklist in
`acquisition/CLAUDE.md` under "Encoder tuning" and the A10 plan.

**Exposure floats, which is the point.** It read 14999 µs on one probe and
1002 µs on another, with nothing changed but ambient light and time. That is
auto-exposure doing its job, and it is exactly the covariance that makes frame
appearance track the animal's position on the pole. The problem is not that
15 ms is long; it is that the value is not under anyone's control.

## What has been done to the camera

`tools/probe_camera.py` is read-only apart from stepping `ChunkSelector` to read
chunk state, which it restores. `--dump-user-sets` additionally executes
`UserSetLoad` for each set to report its contents, then reloads `UserSetDefault`
so the camera is left as it boots.

`tools/verify_a10.py` and `SpinnakerCamera.open()` **do** write to the camera:
they enable `ChunkModeActive` and the `FrameID`/`Timestamp` chunks, set the
stream buffer mode and depth, and set `AcquisitionMode` to `Continuous`. Chunk
and acquisition-mode settings are device-nodemap state that a `UserSetLoad` or a
power cycle resets; the stream buffer settings are transport-layer and are not
persisted at all.

**No tool in this repo executes `UserSetSave`.** `UserSet1` was written by hand
in SpinView on 2026-09-10; `Default` and `UserSet0` still hold factory
defaults. `DeviceReset` has not been run.

## Measured under load (2026-09-10, configured `UserSet1`)

`python tools/verify_a10.py --seconds 60` -- **A10: PASS**, every check:

| | |
|---|---|
| Preflight | all 13 checks pass: every `[camera_verify]` node, 680 × 460, 30.00 fps |
| Frames written | **1801** in 60.0 s vs 1800 expected |
| Rate from hardware timestamps | **30.00 fps** |
| Dropped / incomplete / frame-ID gaps | **0 / 0 / 0** |
| Encoder | `h264_qsv` at `-global_quality 22`, fragmented MP4 |
| Output | **55.5 MB/min** |

Also run through `RecordingSessionController` -- the layer the GUI drives --
after preflight, for two trials (35 s and 8 s, one flagged mid-trial). The 2 s
pre-roll was prepended with frame IDs contiguous across the boundary;
hardware-clock rate 29.996 fps with inter-frame s.d. under 1 µs (max 33.34 ms);
`achieved_fps` 29.996 on both; every frame decodable and file duration matching
the hardware-timestamp span.

## Measured under load (2026-08-14, factory settings)

A 60-second recording through the real pipeline —
`SpinnakerCamera` → `CaptureController` → `BoundedFrameQueue` → `WriterThread` →
FFmpeg — via `python tools/verify_a10.py --seconds 60`:

| | |
|---|---|
| Frames written | **3960** in 60.0 s (**66.0 fps**, free-running) |
| Dropped frames (queue full) | **0** |
| Incomplete frames | **0** |
| Frame-ID gaps | **0** |
| Hardware timestamps | strictly increasing throughout |
| Encoder | `h264_qsv` at `-global_quality 22`, exited 0 |
| Output | 5.6 MB — **5.6 MB/min at 66 fps** |

The pipeline sustained **more than double** the configured 30 fps with zero
loss, which is the real evidence for invariants 3 and 10. Encoded size is far
below the ~37 MB/min that the old 1280×720 estimate implied; at 30 fps expect
roughly half of the 5.6 MB/min above, so a 5-minute trial lands in the low tens
of megabytes.

FFmpeg 8.1.1 is installed and **`h264_qsv` genuinely encodes on the HD 630** —
confirmed with a real one-frame probe, not just its presence in `-encoders`.
`hevc_qsv` and `libx264` work too.

## Still unmeasured

Rate and jitter at a latched 30 fps are now measured (above). Still open:

- Whether frame IDs stay contiguous over a full 5-minute trial (60 s is clean).
- Encoder quality/size trade-off on real footage — `tools/measure_encoder.py`,
  which has still never been run against an actual trial.

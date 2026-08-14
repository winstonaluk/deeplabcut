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

## Chunk data — off as shipped

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

## Open hardware blocker — `UserSetLoad` is not executable

`UserSetLoad` and `UserSetSave` both report GenICam access mode **RO (3)**, and
`Execute()` raises:

```
GenICam::AccessException= Node is not writable. :
AccessException thrown in node 'UserSetLoad' while calling 'UserSetLoad.Execute()'
```

This is not a transient or contextual lock, as far as could be determined
without touching the hardware:

- `DeviceAccessStatus` is `OpenReadWrite`; no other process holds the camera
  (no SpinView or FLIR process running).
- `StreamIsGrabbing` is `False`, `cam.IsStreaming()` is `False`,
  `TLParamsLocked` is `0`.
- The same result appears in a fresh process on the first node touched after
  `Init()`, so it is not something an earlier probe left latched.
- It is the same for all three sets (`Default`, `UserSet0`, `UserSet1`), so it
  is not an "empty user set" condition.
- `PixelFormat` is read-only in the same way, while neighbours like
  `ExposureAuto`, `ChunkModeActive` and `AcquisitionFrameRateEnable` are freely
  writable. Command nodes in general are fine — `TimestampLatch` and
  `DeviceReset` both report WO and are executable.

**Why it blocks A10:** invariant 7's entire startup path is `UserSetLoad` then
verify. Until this clears, the camera keeps booting into factory defaults with
auto-exposure on, and preflight would hard-fail every session.

Things to try, in order — all require someone at the rig:

1. Power-cycle or replug the camera, then re-run `tools/probe_camera.py` and
   check the access modes. An unclean exit can leave device registers latched.
   (`DeviceReset` is executable and would do this in software.)
2. Open SpinView and see whether user-set load/save is greyed out there too.
   That separates a camera-state problem from a PySpin one.
3. Check Teledyne for firmware newer than `1707.1.6.0` for the BFS-U3-04S2C.
4. Confirm `UserSet1` was ever actually saved. `UserSetSave` is read-only too,
   so it may be an empty slot — in which case `config.toml`'s
   `user_set = "UserSet1"` currently points at nothing.

## What was and was not done to the camera

Probing was read-only by intent. One exception: while testing whether
`UserSetLoad` was executable, `UserSetSelector` was set across `Default`,
`UserSet0` and `UserSet1`. The selector only chooses which set a subsequent
load or save would target, and **every `UserSetLoad` call failed with
`AccessException`, so no user set was loaded and no camera setting changed**.
The selector was returned to `UserSet0`, where it was found. `UserSetSave` is
never called by anything in `tools/`.

`DeviceReset` was not run, the camera was not power-cycled, and acquisition was
never started.

## Still unmeasured

Requires a live acquisition run, which should happen only against the settings
actually intended for recording (i.e. after `UserSet1` is fixed):

- Delivered frame rate and jitter under the real 30 fps configuration.
- That chunk timestamps increase monotonically and frame IDs have no gaps.
- Incomplete-frame rate over a multi-minute trial.
- Whether `h264_qsv` is actually available — **FFmpeg is not installed on the
  acquisition PC at all** as of this writing (`ffmpeg` is not on PATH), which
  the app already treats as a blocking preflight failure.

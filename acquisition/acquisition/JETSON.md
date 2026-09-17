# The acquisition board, as measured

Standing companion to `HARDWARE.md`, which records the *camera*. This file
records the *host*. Same rule: **when this file and a design document disagree,
this file wins** — it is the measurement, not the intention.

> **NOTHING HERE IS MEASURED YET.** The board has not been set up. Every table
> below is a list of questions with the answer left blank on purpose. Do not
> fill a cell with an estimate, a vendor spec, or a number carried over from the
> retired Windows host — an unmeasured figure that looks measured is worse than
> an empty one, because the next reader cannot tell which is which. Populating
> this file is checkpoint A11.

Intended target: **NVIDIA Jetson Orin Nano Super 8 GB**, JetPack 6.x
(Ubuntu 22.04), Linux aarch64.

## Why this file exists

The retired host was an i7-7700 with Intel HD Graphics 630: no usable GPU
compute, but Quick Sync fixed-function H.264 encode. The Jetson inverts both
properties, and that inversion is the whole architecture change:

- **It has CUDA and TensorRT**, so on-device DLC-Live inference is possible.
- **It has no hardware video encoder at all.** NVIDIA omitted the NVENC (and
  NVDEC) silicon from the Orin Nano specifically; it is a cost-reduced derivative
  of the Orin SoC. `nvv4l2h264enc` is not registered in GStreamer and reflashing
  cannot add it. All H.264 encoding is `libx264` on 6 Cortex-A78AE cores — the
  same cores running inference and the capture callbacks.

So the two headline workloads compete for one fixed CPU budget, and 8 GB is
shared between CPU and GPU. Almost every open question below is some form of
"how much of that budget is left".

## Identity

| | Measured |
|---|---|
| Module / variant | |
| JetPack version | |
| L4T / kernel | |
| Python (system) | |
| Power mode (`nvpmodel -q`) | |
| Storage (device, size, free) | |
| CUDA / TensorRT versions | |

## The dependency stack (highest-risk item in the plan)

These five must coexist in one Python 3.10 environment. The failure mode is not
subtle — either `import PySpin` works or the whole app is dead — but it is the
most likely thing in the plan to fail outright.

| | Measured | Notes |
|---|---|---|
| Spinnaker SDK (ARM64) | | **Separate vendor download** from x86-64, own version matrix |
| PySpin wheel | | **Does a `cp310` aarch64 wheel exist?** This is the load-bearing unknown. If not, the 3.10 pin breaks and `app/config.py`'s `tomli` fallback may become unnecessary — or a newer Python becomes mandatory |
| numpy | | Must be **>= 1.20, < 2**. Ceiling: PySpin rejects 2.x. Floor: ARM-specific — `docs/PySpinReadMe.md` §4.3 records 1.19.5 raising "Illegal instruction" on `import PySpin` on Linux ARM64 |
| PyTorch | | From **NVIDIA's Jetson wheel index, not PyPI**. Check it tolerates numpy 1.x |
| TensorRT | | Bundled with JetPack |
| `dlclive` | | Check its own numpy/torch constraints against the above |
| FFmpeg + libx264 | | Confirm `libx264` present; confirm `h264_qsv` and `h264_nvenc` are **absent**, so a stale config fails visibly rather than resolving silently |

## Camera streaming

| | Measured |
|---|---|
| `usbfs_memory_mb` (default 16, must be raised) | |
| Made persistent how | |
| 60 s single-camera stream: frames / drops / incomplete / frame-ID gaps | |
| Hardware timestamps monotonic | |
| USB host-controller topology (do ports share a controller?) | |
| Max cameras before bandwidth or buffer loss | |

## Encoding

Measure with `tools/measure_encoder.py` on real footage. **Run it under
simultaneous inference load** — an idle-board number says nothing about the
configuration that has to survive a session. It has never been run at all.

| | Measured |
|---|---|
| Highest `libx264` preset sustaining 30 fps, 1 camera, idle | |
| Same, with inference running | |
| Same, N cameras | |
| Output MB/min per camera at chosen settings | |
| CPU affinity chosen for FFmpeg | |
| Whether a fast-intermediate + offline transcode is needed | |

For reference, the retired host measured **~55–60 MB/min** with `h264_qsv` at
the configured `UserSet1` (gain 34.7 dB — sensor noise does not compress). That
is a Quick Sync number and is **not a forecast** for `libx264` on ARM.

## Inference and closed-loop latency

Stimulation output implies a sub-50 ms end-to-end budget. Break it down and
measure each stage rather than the total, so a regression is attributable.

| Stage | Measured |
|---|---|
| Exposure + USB3 transfer to callback | |
| Preprocess | |
| Inference (dummy TensorRT engine) | |
| Inference (real model, once trained) | |
| Predicate evaluation | |
| GPIO write (userspace, non-RT kernel) | |
| **End-to-end p50 / p99** | |

## Thermal and sustained load

| | Measured |
|---|---|
| Cooling (passive / active) | |
| Steady-state temperature under encode + inference | |
| Any observed clock throttling | |
| Behaviour over a full 5-minute trial | |

## GPIO

| | Measured |
|---|---|
| Pin chosen for trial bracket / stim marker | |
| Library (`Jetson.GPIO`) and permissions setup | |
| Observed edge latency and jitter on a scope | |

## Still unmeasured

Everything. See the banner.

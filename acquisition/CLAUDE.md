# CLAUDE.md

Project context for the behavioral acquisition backend and its web UI. This file
is auto-loaded each session — treat everything here as standing rules unless I
say otherwise in chat.

---

## What this is

A multi-camera behavioral video acquisition application for a rodent
neuroscience lab. Replaces vendor capture tooling (SpinView) which requires
manual start/stop and post-hoc association of video files with animal metadata.
This app binds metadata at write time and reduces per-trial interaction to a
single button press.

Current paradigm: **PDCT**. The architecture must accommodate future paradigms
(maze task) without a rewrite.

**Architecture change in progress (2026-09).** The app is moving from a
single-camera PySide6 desktop GUI on a Windows/x86 PC to a **FastAPI backend
with a React frontend, running on an NVIDIA Jetson Orin Nano**, with **N
cameras** and **DLC-Live** real-time pose inference driving closed-loop trial
stop and stimulation output. Checkpoints A13–A21 below carry that work.
Documents dated before 2026-09-15 describing a Qt GUI or a single camera are
superseded by this file.

## Glossary

| Term | Meaning |
|---|---|
| **PDCT** | Pole Descent Cognitive Test. Rat placed atop a vertical pole, descends. |
| **Trial** | One descent, start to finish. Currently 1–5 minutes for our rats. |
| **Session** | All trials for one animal on one day. |
| **DeepLabCut / DLC** | Markerless pose-estimation framework. Consumes our video offline. |
| **DLC-Live** | Real-time DLC inference, on-device. In scope — see "Pose pipeline". No model trained yet, so the pipeline is built against a stub provider. |
| **Spinnaker / PySpin** | Teledyne FLIR camera SDK and its Python bindings. |
| **UserSet** | Camera-onboard settings profile. We use `UserSet1`, configured in SpinView. |
| **Chunk data** | Per-frame metadata (hardware timestamp, frame ID) embedded by the camera. |
| **View** | One camera's position, e.g. `top_down`. Part of the filename and the shared schema. |

## Domain context

These facts drive design decisions — don't optimize against them.

- Subjects are **rats**. Trials run **~1–5 minutes**, long relative to typical
  mouse PDCT. May shorten as training improves, so **every duration threshold is
  a config value, never a literal**.
- The experimenter stands and observes throughout a trial. Mid-trial annotation
  is cheap and is the preferred annotation point — via on-screen buttons.
- Failure modes seen in-trial: animal **falls**, **freezes** partway, or **never
  descends**.
- **Trial duration is the primary dependent variable.** Falls and freezes don't
  make a trial noisy — they make it meaningless. Exclusion metadata is
  scientifically load-bearing.
- Video becomes DLC training data. Compression artifacts degrade keypoint
  accuracy. **Minimise file size subject to keypoint accuracy, in that order** —
  quality is the constraint, size is the thing being optimised, and neither is
  free. See "Encoder tuning" below; do not guess at the trade-off, measure it.

## Hardware

**Acquisition board (runs this app):** NVIDIA **Jetson Orin Nano Super 8 GB**,
JetPack 6.x (Ubuntu 22.04), Linux **aarch64**, NVMe storage.

- **No hardware video encoder.** NVIDIA omitted the NVENC (and NVDEC) silicon
  from the Orin Nano specifically; it is a cost-reduced derivative of the Orin
  SoC, `nvv4l2h264enc` is not registered in GStreamer, and reflashing cannot add
  it. All H.264 encoding is `libx264` on 6 Cortex-A78AE cores. Never propose
  `h264_nvenc` (absent) or `h264_qsv` (Intel Quick Sync, belonged to the retired
  host).
- **CUDA and TensorRT are available**, and GPU inference is now the point — the
  old rule "never propose GPU inference here" applied to the retired i7-7700's
  Intel HD 630 and is **revoked**.
- **8 GB is shared between CPU and GPU.** Camera buffers, N FFmpeg processes, a
  2 s pre-roll ring per camera and a loaded TensorRT engine all come out of the
  same pool. Keep the browser off the board — Chromium costs ~500 MB–1 GB.
- Encode and inference contend for the same 6 cores. Pin FFmpeg's CPU affinity so
  a burst of encoding cannot starve a latency-critical stop predicate.
- Disk management is a feature, not an afterthought. Size the NVMe for N cameras
  before assuming headroom.

**Cameras:** Teledyne FLIR **Blackfly S BFS-U3-04S2C**, USB3, global shutter, via
Spinnaker/PySpin. The rig's first camera is serial `22514545`, mounted **above
the apparatus looking down** (`top_down`).

- Sensor is **720 × 540** (Sony IMX287, 0.4 MP) — *not* 1280 × 720. The old
  "720p60" note was a misread of "720 × 540"; every figure derived from it was
  wrong-high.
- `UserSet1` records a **680 × 460 ROI** within it (saved 2026-09-10), and
  `config.toml` matches. The ROI may become square later.
- It is a **colour** sensor (`BayerRG8`). We record Mono8, which on this camera
  is luma derived from the Bayer mosaic rather than a native mono readout.
- **The next camera added should be lateral, not a second overhead view.** The
  top-down camera looks down the pole axis, so height is not observable, and
  every height-based metric in the analysis pipeline's stage 8 was built for a
  lateral view. A lateral camera resolves that conflict and is also the view a
  descent-completion stop predicate needs.
- USB3 is ~9.4 MB/s per camera at the 680 × 460 Mono8 ROI. Verify the Orin's USB
  controller topology before assuming three cameras share bandwidth cleanly.
- Linux requires raising `/sys/module/usbcore/parameters/usbfs_memory_mb`; the
  16 MB default is far too small for USB3 machine vision. This is a preflight
  check, not a footnote.

`acquisition/acquisition/HARDWARE.md` records what the camera actually reports,
measured rather than assumed. **When it and a design note disagree, it wins.**
Regenerate it with `python tools/probe_camera.py` after any firmware change,
camera swap, or SpinView reconfiguration. `acquisition/acquisition/JETSON.md`
holds the same standing for the board.

## Stack

Python **3.10 exactly** · PySpin · numpy **>= 1.20, < 2** · FastAPI + uvicorn ·
React + Vite + TypeScript · Pillow (preview JPEG encode) · FFmpeg via subprocess
(`libx264`) · PyTorch + TensorRT + `dlclive` (pose).

Version constraints, each load-bearing for a different reason:

- **3.10** is pinned by the `cp310` PySpin wheel. JetPack 6 ships Ubuntu 22.04,
  whose system Python is 3.10, so the version survives the move — but the
  *reason* changed: it is now the **aarch64** Spinnaker SDK, a separate vendor
  download with its own version and Python matrix. **Re-verify the `cp310`
  assumption against the ARM64 SDK; it has not been checked.** `tomllib` is
  3.11+, so config loading keeps its `tomli` backport fallback.
- **numpy < 2** because PySpin does not support 2.x. **numpy >= 1.20** because
  the vendor readme (`docs/PySpinReadMe.md` §4.3) records that 1.19.5 on Linux
  ARM64 makes `import PySpin` raise "Illegal instruction". The lower bound only
  matters on this architecture.

PySide6 is **gone**. Do not add Qt back.

## Architecture invariants

Do not violate these. If a request seems to require breaking one, stop and ask.

Invariants are referenced **by number** from `HARDWARE.md`, `SPINNAKER_PLAN.md`,
`QUESTIONS.md`, the encoder-tuning skill and inline code comments. When an
invariant changes, replace its text and keep its slot — never renumber.

1. **N cameras, one config list.** The rig has one camera today and will gain
   more; a lateral view is planned. Cameras reach code through the
   `[[cameras]]` config list and a list of rigs, each with its own `view` tag,
   `type`, `sync_role` and `[camera_verify]` table. Nothing may assume a single
   camera. Above one camera the `<view>` filename token is mandatory, not
   optional. *(Revoked 2026-09-15: this invariant previously read "One camera…
   will not gain more" and forbade building for a second. That was the deviation;
   the original design was N-camera.)*
2. **Mock backend is first-class.** `CameraBackend` is abstract with
   `SpinnakerCamera` and `MockCamera` implementations, resolved from config
   `type` via `acquisition/camera_registry.py`. The whole app must run and all
   tests must pass with zero hardware attached. The same rule applies to pose:
   see invariant 12.
3. **Capture never blocks.** One capture thread per camera using Spinnaker's
   image event handler (not polling) → bounded queue → separate writer thread
   piping to FFmpeg. On queue-full: drop frame, increment counter, log. Never block.
4. **Recording integrity is independent of everything else.** No UI client, HTTP
   handler, preview stream, pose provider or trigger backend may affect the
   recording. Every call into those layers is wrapped; a failure sets an
   `auto_flag` and is logged, and never fails a trial. This gets *more*
   load-bearing once a real DLC-Live provider — which can crash, stall, or
   exhaust GPU memory — is in the process.
5. **Preview is throttled** to `capture.preview_fps` regardless of capture rate,
   and reads the latest-frame slot rather than consuming the write queue.
   Delivered as MJPEG over `multipart/x-mixed-replace`, one endpoint per camera,
   encoded from `CaptureController.latest_frame`. A slow or absent client must
   not apply backpressure to capture or to the state feed.
6. **Hardware timestamps only.** Chunk data timestamps + frame IDs to a per-trial
   CSV sidecar. Never substitute host wall-clock arrival time. Requires the app
   to enable chunk data — see the carve-out in invariant 7.
7. **No camera configuration UI.** Exposure/gain/ROI/gamma/trigger are set in
   SpinView and saved to `UserSet1`. App calls `UserSetLoad` at startup, verifies
   against that camera's `[camera_verify]` table in config, and logs the result.
   Never expose these as editable controls, and never write a node to make a
   check pass — the app refuses to record against a wrongly-configured camera, it
   does not silently fix one.

   **Carve-out:** this invariant governs *image-formation* parameters, the ones
   that change what the science looks like. It does not cover settings that are
   data-integrity requirements of this app, which the app sets itself and logs:
   **chunk data** (`ChunkModeActive`, `ChunkEnable` for FrameID and Timestamp —
   invariant 6 is unsatisfiable without them, and the camera ships with them
   off) and **stream buffers** (`StreamBufferHandlingMode`,
   `StreamBufferCountManual` — these live in the transport-layer nodemap, which
   user sets do not cover at all).
8. **Trial stop is a pluggable predicate.** Currently button-driven; becoming
   pose-driven. Never weld the stop condition into an HTTP handler, a WebSocket
   callback, or any UI event path — it routes through `TrialStopCondition`.
9. **Config over literals.** Durations, thresholds, paths, reason codes, encoder
   settings all live in TOML.
10. **Long-run stability.** Multi-minute trials mean the writer sustains
    continuous throughput with no unbounded memory growth, per camera.
11. **The tick loop is server-side.** `RecordingSessionController.tick()`
    enforces `max_trial_duration_s` and polls the stop predicate (invariant 8).
    `SessionService` owns a daemon thread that drives it, so the
    runaway-recording guard does not depend on a UI being open. Never move
    ticking into a UI — and note that **an HTTP request handler is a UI** for
    this purpose. The corollary is that `RecordingSessionController` is reached
    from several threads, so every mutation goes through `SessionService`'s lock;
    it has none of its own.
12. **Pose is best-effort.** Inference may lag, fail, or be absent entirely.
    Recording integrity never depends on it (invariant 4). The pose worker reads
    the latest-frame slot, never the write queue, and always takes the *newest*
    frame — dropping the rest — so it can never queue up latency. The whole
    pipeline must run and all tests pass with **no model and no GPU**, exactly as
    `MockCamera` makes capture testable with no camera (invariant 2).
13. **The backend is the application; the UI is a view.** Recording survives the
    browser closing. State lives in `SessionService`, not in a client. Control is
    restricted by the `[api] control_allow` CIDR list (default loopback only);
    everything else gets read-only access — `GET`, the state WebSocket, and
    preview streams.

## Out of scope — do not build

- The maze paradigm (define the seam, ship only `PDCTParadigm`)
- Electrophysiology **hardware** integration — no ephys system has been bought.
  The trial-boundary and pose seams exist (`TriggerService`), and stimulation
  output **is** in scope; what is out of scope is integrating with any specific
  ephys vendor's software API. See "Ephys sync" below.
- Camera configuration UI (invariant 7)
- Offline pose analysis — that is the analysis pipeline's job, not this app's
- Keyboard hotkeys (deferred, not rejected — see "Trial annotation")

## UI style

**Deliberately plain.** Stock HTML elements, standard layout, no UI framework,
no theming or icon packs. Three screens: session setup, recording,
end-of-session review.

One exception: on the recording screen, **trial counter, current state, elapsed
time, active flags, dropped-frame count and pose latency render in a large
font**, readable from several feet away with an animal in hand. This is a UX
requirement, not a style preference, and it survives every framework change.

The pose overlay is drawn **client-side**: the backend sends keypoint JSON over a
WebSocket and the browser draws SVG over the preview `<img>`. Never composite an
overlay server-side — on a memory- and CPU-bound board that is a second encode
pass for no benefit.

## Metadata schema

**Session-level** (entered once, locks on start):

| Field | Type | Notes |
|---|---|---|
| `animal_id` | text | Regex-validated; autocompletes from prior IDs in this project |
| `project_name` | dropdown | From config. Not free text. |
| `date` | auto | ISO `YYYYMMDD` |
| `experimenter_initials` | dropdown | From config |

Labels defined in one place for easy editing.

**Auto-captured:** session start timestamp · per-camera serial, view, loaded
`UserSet1` and verification result · app version / git commit · FFmpeg encoder +
params · rig ID · board and JetPack version · per-trial and per-camera frame
count, dropped-frame count, achieved fps, exact duration.

**Per-trial:** trial number · start time · `flags` (set of experimenter reason
codes; empty = valid) · `auto_flags` (set applied by the app, kept separate) ·
optional note.

## Trial annotation

**Every trial is valid by default. Annotation is subtractive and never blocking** —
the experimenter is never forced into a dialog to reach the next trial.

Reason codes, live **both during a trial and after it ends**, each with a large
on-screen button:

| Code | Meaning |
|---|---|
| `fall` | Fell from the pole |
| `freeze` | Froze partway down |
| `did_not_descend` | Never initiated descent |
| `experimenter_error` | Handling/placement error |
| `other_invalid` | Generic; reason assigned later |

- Each control **toggles** its own flag. Flags are **not mutually exclusive** —
  freeze then fall records both.
- **Target trial** = currently recording trial if active, else most recently
  completed trial. Annotating a few seconds late must work.
- The codes and their labels come from the `[keymap]` and
  `[reason_code_labels]` tables in TOML, served to the frontend via the API.
  New paradigms define different codes without source changes.
- Visual feedback: large labelled chips for active flags, trial counter changes
  colour when flagged, brief confirmation on toggle.

**Keyboard hotkeys are deferred.** Buttons are the control surface. The
`key → reason_code` mapping stays in config so adding a `keydown` listener later
is one frontend component and no backend change. Until then, the domain note
above about mid-trial annotation being cheap describes buttons, not keys.

## Trial state machine

`IDLE` → `RECORDING` → `IDLE`. A single start/stop control drives both.

| Config key | Default | Behavior |
|---|---|---|
| `min_trial_duration_s` | 5 | Stop requests swallowed entirely within this window; prevents double-tap zero-length trials. Show a countdown so the dead control is explained. |
| `suspicious_duration_s` | 30 | Trials shorter than this get `auto_flags: [suspiciously_short]`. No real descent is this fast. |
| `max_trial_duration_s` | 600 | Auto-stop + `auto_flags: [max_duration_reached]`. An animal may never descend; recording must not run away with the disk. Warn on-screen as the cap nears. Enforced by the server-side tick loop (invariant 11). |

Discard-last removes the last trial (videos + sidecars + metadata) after
confirmation, decrementing the counter.

## Pre-roll buffer

Rolling in-RAM buffer of the most recent **2 s** (config) **per camera**, running
whenever streaming — not just during trials. Prepended on trial start so descent
onset is never clipped by reaction time. **~19 MB** per camera per 2 s at
680 × 460 Mono8 / 30 fps — worth re-checking against the 8 GB shared pool as
cameras are added.

The pre-roll handoff is atomic: `CaptureController.begin_trial()` snapshots the
buffer and attaches the sink under one lock, so each frame lands in exactly one
of the snapshot or the queue — never neither (a frame-ID gap) and never both (a
duplicate).

**Pre-roll frames count toward `achieved_fps` but must not count against trial
*duration*.** Getting this wrong overstated `achieved_fps` by roughly
`preroll_s * fps / duration`. They also mean the sidecar's first row is not the
trial's first frame, so the true trial start is recorded separately.

## Pose pipeline

DLC-Live runs **on this board**, in its own daemon thread, reading one camera's
latest-frame slot. Governed by invariants 4 and 12.

- Woken by an `Event` set in the capture callback rather than polling — polling
  adds up to a frame interval of latency for nothing. `Event.set()` is
  non-blocking, so invariant 3 holds.
- `PoseProvider` is a Protocol with `NullPoseProvider`, a mock provider producing
  scripted keypoints, and `DLCLivePoseProvider`. Selected by `[pose] provider`.
- Four consumers of each `PoseEstimate`: the overlay WebSocket, the
  `PoseStopCondition` predicate (invariant 8), the trigger backend for
  stimulation output, and the per-trial live-pose sidecar.
- **Latency is instrumented, not assumed.** Closed-loop stimulation implies a
  sub-50 ms budget across USB3 transfer, preprocess, inference, predicate and a
  userspace GPIO write. Every `PoseEstimate` carries its source frame's
  `hardware_timestamp_ns` and the monotonic time inference completed; per-frame
  latency goes in the sidecar and rolling p50/p99 to the UI. A closed-loop
  latency you have not measured is one you cannot publish.
- A provider failure sets `auto_flags: [pose_degraded]`; a trigger failure sets
  `[trigger_failed]`. Neither fails a trial.

## Ephys sync

No ephys hardware bought yet, so this is a seam, not an implementation. The
wiring is decided in advance because it constrains nothing else:

Do **not** integrate with any ephys vendor's software API — more than one system
is in use. The common denominator across Open Ephys, SpikeGLX, Intan RHX, TDT
and Plexon is a digital input that records TTL edges on the ephys sample clock.
Emit a signal all of them can record:

- Primary camera's `ExposureActive` strobe (Line2) → ephys digital-in **and**
  every secondary camera's trigger input. Hardware-generated, no host
  involvement; frame-locks all cameras and gives per-frame alignment via the
  existing `frame_id` in the timestamp sidecar.
- A **Jetson 40-pin GPIO** pin for trial brackets and stimulation markers on a
  second ephys channel. Host-driven, so ~1 ms of jitter on a non-RT kernel —
  fine at behavioural timescales. Camera GPIO is the wrong path for host-driven
  output because it adds a USB3 round trip.

A Teensy 4.x as master clock plugs into the same `TriggerBackend` interface if
sub-millisecond determinism is ever needed. Do not buy one pre-emptively.

## Files and naming

```
<session_root>/<animal_id>_<project_name>_<date>_<initials>/
    session_metadata.json
    trials.csv
    trial_cameras.csv
    <animal_id>_<project_name>_<date>_<initials>_<view>_<HHMM>_t001.mp4
    <animal_id>_<project_name>_<date>_<initials>_<view>_<HHMM>_t001_timestamps.csv
    ...
    session.log
```

- `<HHMM>` = trial start time. `t<NNN>` = zero-padded trial number. With N
  cameras, `t<NNN>` alone no longer guarantees uniqueness — the `<view>` token
  does.
- The `<view>` token is config-toggleable but **mandatory above one camera**, and
  config loading enforces that. DLC flattens folder structure on import, so
  filenames must stand alone.
- Never overwrite an existing session directory.
- `trials.csv` exports the trial table so downstream analysis filters the
  training-frame pool on flags without parsing JSON. Valid/invalid must be
  trivially machine-readable. `trial_cameras.csv` carries the per-camera frame
  counts that make desync detectable.
- `session_metadata.json` carries a `schema_version` key.

## Cross-repo contract

`session_metadata.json`, `trials.csv`, `trial_cameras.csv` and the sidecars are
the **interface to the analysis pipeline**, which reads them as the spine of its
manifest.

- Schemas live in `shared/schema/` and are imported here, never redefined locally.
- All carry `schema_version`. Any field change is a version bump.
- Readers **fail loudly** on a version mismatch. `SchemaVersionError` exists for
  this and must never be softened into coercion.

**The analysis pipeline is moving to its own repository** (`pdct-analysis`),
because the two run on different machines with incompatible Python floors —
this app is pinned to 3.10 by PySpin, and analysis needs 3.11+ for `tomllib`.
`shared/` stays here and analysis consumes it as a tagged dependency. The old
"update both in the same commit" rule cannot survive two git histories; it is
replaced by:

1. Change `shared/schema/`, bump `schema_version`, update the writers here, tag
   `schema-vN.0.0`.
2. Update the pin and the stage-0 reader in the analysis repo, in one commit
   there.
3. Neither side merges until both sides' tests pass.

## Storage

Acquisition runs at **30 fps** (fps is a config value; the sensor can go far
faster, but exposure time is the binding constraint). Raw rate is **9.4 MB/s per
camera** at the 680 × 460 Mono8 ROI.

**Historical measurement, retired host:** with the configured `UserSet1`, encoded
output measured **~55–60 MB/min** with `h264_qsv` on the i7-7700 — a 5-minute
trial ~300 MB, ten times the 5.6 MB/min measured at factory settings. The most
likely cause is gain at 34.7 dB: sensor noise does not compress. Bringing gain
down (with more light) is the lever. **These numbers do not forecast the Jetson**
— that is `libx264` on ARM, and the figure must be re-measured per camera before
sizing anything.

- Live free-space indicator **and estimated remaining-recording-time** from
  measured bitrate. GB free is not actionable mid-session; "47 min remaining" is.
  The estimate must scale with camera count.
- Hard block on session start below threshold, surfaced as a clear preflight failure.
- `libx264` only. Quality is still configured **per codec** — `-crf` and
  `-global_quality` are different scales and one shared number silently meant two
  different qualities. The `qsv_global_quality` key is dead on this hardware but
  the per-codec structure stays.
- "Stage for transfer": package completed sessions to a staging dir with checksum
  verification. Remote is a **generic mounted path or rsync target** — never
  hardcode an institution-specific system. (`robocopy` does not exist on Linux.)
- Purge-after-verified-transfer requires explicit confirmation.

## Encoder tuning

See the `encoder-tuning` skill (`.claude/skills/encoder-tuning/SKILL.md`)
before changing codec, quality, preset, resolution, fps, exposure, or camera
count. Short version: exposure time dominates anything a codec setting can do;
preset is **no longer free** because it trades against inference headroom on the
same 6 cores; and `python tools/measure_encoder.py REFERENCE.mp4` is how the
trade-off gets measured instead of guessed — on the Jetson, under inference load.

## Preflight checks

Every camera detected · `UserSet1` loaded per camera · every `[camera_verify]`
node matching · reported resolution matching config · reported frame rate
matching config within `capture.fps_tolerance` · serials and views unique ·
cross-camera frame-rate agreement · FFmpeg available · resolved encoder ·
`usbfs_memory_mb` raised · `nvpmodel` power mode · thermal headroom · free disk
above threshold. Block recording and show a clear message on any failure.

**Config is not ground truth about the hardware** — it is what we intend the
hardware to be doing. The backend reports what it is *actually* doing
(`resolution`, `pixel_format`, `frame_rate`, `verify_settings`) and preflight
compares the two. Never assume they agree: a 1280 × 720 config value meeting a
720 × 540 sensor produced no error at all, just silently sheared video.

Preflight does not short-circuit on the first failure. An experimenter with an
animal in hand should see everything that needs fixing in one pass.

## Project structure

`ls` shows the layout. What it does not show:

- `acquisition/HARDWARE.md` — what the camera measurably is, not what we
  intend it to be. When it and a design note disagree, it wins.
- `acquisition/JETSON.md` — the same, for the board.
- `acquisition/SPINNAKER_PLAN.md` — the `SpinnakerCamera` design rationale.
- `tools/` — hardware probes. Need PySpin; outside the package and the suite.

## Commands

```bash
# record a full session against synthetic frames, no hardware
python -m app --mock --headless

# same, against the real cameras
python -m app --headless

# serve the API and web UI (A14+)
python -m app

# tests (must pass with no hardware attached; hardware tests deselected)
pytest

# the hardware-marked subset, at the rig
pytest -m hardware

# verify the rig end to end: N cameras, drops, timestamp agreement
python tools/verify_rig.py

# read the camera and refresh HARDWARE.md (at the rig; needs PySpin)
python tools/probe_camera.py

# sweep encoder settings over a real trial; needs FFmpeg
python tools/measure_encoder.py REFERENCE.mp4
```

Tests that spawn FFmpeg are marked `requires_ffmpeg` and skip automatically when
it isn't on PATH, so a missing external binary reports as one named skip rather
than eleven identical tracebacks. No test may require PySpin, CUDA, a trained
DLC model, or a network mount.

**Setup is not documented anywhere and needs a README.** The absence is not
cosmetic: `shared/schema/` is linked into the environment by an out-of-band
editable install that nothing declares, and when it silently pointed at a moved
directory the entire test suite stopped running with no indication why.

## Conventions

- Type hints throughout; `Protocol` for interfaces
- Dataclasses for metadata records; frozen dataclasses in `shared/schema/`
  (hand-rolled validation, no pydantic there — pydantic is confined to the API
  layer's HTTP DTOs and never redefines the schema)
- Structured logging to a per-session log file, not bare `print`
- Every threshold, path, reason code, and encoder setting reaches code via config
- Tests cover the state machine (min-duration guard, max-duration auto-stop,
  suspicious-short auto-flag), flag toggling and targeting, schema validation,
  filename generation, and queue-full drop behavior

## Unattended runs

When running headless (`claude -p`) I cannot answer questions. Therefore:

- **Never guess on an ambiguity you would normally ask about.** Append it to
  `QUESTIONS.md` at repo root with the affected file and line, implement the most
  conservative interpretation, mark it `# TODO(QUESTIONS.md): <ref>` in code, and
  continue.
- **A checkpoint is not complete until `pytest` passes.** If tests fail and can't
  be fixed within the checkpoint's scope, commit the work, record the failure in
  `QUESTIONS.md`, and move to the next checkpoint rather than stalling.
- **Commit at every checkpoint** with message `checkpoint A<n>: <name>`. Never
  leave uncommitted work at a checkpoint boundary.
- **Never skip ahead.** Checkpoints are ordered by dependency.
- Do not relax an invariant to make a test pass. Record the conflict instead.

## Open decisions

Live, and blocking specific checkpoints. Both were deferred in `QUESTIONS.md`
when nothing depended on them; A17 makes both actionable.

- **Does `min_trial_duration_s` gate a pose-triggered stop?** Today the guard
  applies uniformly, which was the conservative reading when the predicate was
  inert. CLAUDE.md ties the guard to "double-tap zero-length trials", a
  human-input concern that does not obviously apply to a pose predicate. See
  `# TODO(QUESTIONS.md)` at `acquisition/trial_state_machine.py:160`.
- **What `auto_flag` marks a predicate-driven stop?** A pose-stopped trial is
  scientifically different from a hand-stopped one and analysis should be able to
  tell. Choosing the value is a **schema-contract change** — it crosses into the
  analysis pipeline's stage-1 QC gate, so it follows the version protocol above.

## Checkpoints

`A0` is shared with the analysis pipeline and must exist before anything else.

| ID | Name | Done when |
|---|---|---|
| A0 | Shared schema | `shared/schema/` defines `session_metadata.json`, `trials.csv`, and timestamp-sidecar schemas with `schema_version`. Both repos import it. |
| A1 | Interfaces + skeleton | Package layout exists; `CameraBackend`, `Paradigm`, `PoseProvider`, and the trial state machine are defined with full type signatures and docstrings. **No implementation bodies.** `config.toml` schema complete with every key and default. Tests importable. |
| A2 | Mock capture end-to-end | `MockCamera` → capture thread → bounded queue → writer → playable H.264 file. Dropped-frame counter increments correctly under induced backpressure. Long-run test shows flat memory. |
| A3 | Trial state machine | All guards implemented and tested: min-duration swallow, max-duration auto-stop, suspicious-short auto-flag, discard-last. Stop condition is a pluggable predicate. |
| A4 | Metadata + naming | Filename generation, `session_metadata.json`, `trials.csv`, timestamp sidecars, flag/`auto_flag` sets, schema validation. All against `shared/schema/`. Round-trip tests. |
| A5–A7 | *(void)* | The three PySide6 screens — session setup, recording, review. Built and tested, never wired into an event loop, deleted in A15. Their behavioural requirements carry forward into the React screens; the widgets do not. |
| A8 | Storage + staging | Free-space indicator, remaining-time estimate, hard block below threshold, staging with checksum verification, confirm-gated purge. |
| A9 | `SpinnakerCamera` scaffold | **Done.** Superseded by A9.5, which rewrote the plan against real hardware. |
| A9.5 | Camera backend schema | **Done.** Backend reports `resolution`, `pixel_format`, `frame_rate`, `verify_settings`, `incomplete_frame_count`; preflight asserts config against all of them; writer derives geometry and pixel format from the backend; `[camera_verify]` table in config; `HARDWARE.md` records the measured camera. |
| A10 | `SpinnakerCamera` implementation | **Done, verified 2026-09-10 on the retired Windows host.** `tools/verify_a10.py` passed every check against the configured `UserSet1` (680 × 460 ROI, 30 fps latched): 1801 frames in 60 s, zero drops, incomplete frames or frame-ID gaps, monotonic hardware timestamps, `h264_qsv` fragmented MP4. `pytest -m hardware` 6/6. Must be re-verified on the Jetson (A20). |
| A11 | Jetson environment spike | **Not started.** Needs the board; runs in parallel with A13–A17. PySpin aarch64/cp310 + `numpy>=1.20,<2` + Jetson PyTorch + TensorRT + `dlclive` coexisting in one env; a clean 60 s stream with `usbfs_memory_mb` raised; `libx264` throughput under synthetic inference load; dummy TensorRT latency. Records measured results in `JETSON.md`. |
| A12 | Composition root | **Done 2026-09-15.** `app/session_service.py` constructs cameras from `[[cameras]]` via `acquisition/camera_registry.py`, runs preflight, starts capture, writes `session_metadata.json`, and owns the trial lifecycle plus the server-side tick loop. `python -m app --mock --headless` records a full session. 13 tests in `tests/test_session_service.py`. |
| A13 | Docs + repo split | **In progress.** Every markdown file reflects the Jetson / FastAPI / N-camera / DLC-Live architecture; obsolete historical prompts deleted; `analysis/` split to `pdct-analysis` with `shared/` consumed as a tagged dependency. |
| A14 | FastAPI backend | REST + state WebSocket + MJPEG preview + `control_allow` CIDR policy. A full session runs end to end through `TestClient` with `MockCamera` — no browser, no hardware — and a non-allowlisted client is refused on every mutating route while `GET` and the WebSocket succeed. |
| A15 | React frontend, PySide6 removed | Three screens, buttons only, capability-aware monitoring mode, large-font readouts. `gui/` deleted along with its two test modules, the Qt half of `test_review.py`, and the `qapp`/`QT_QPA_PLATFORM` machinery in `conftest.py`. PySide6 dropped from `requirements.txt` and `pyproject.toml`. |
| A16 | Schema v2 + N cameras | Per-camera `[camera_verify]` tables, `type` and `sync_role`, view token enforced above one camera, N-camera preflight, `camera_desync` auto-flag, `trial_cameras.csv`, `preroll_frames` recorded. Coordinated with the analysis repo via the version protocol. |
| A17 | Pose pipeline against a stub | `PoseWorker`, `frame_ready` Event, mock provider, `latest_pose`, `/api/ws/pose`, SVG overlay, live-pose sidecar, `PoseStopCondition`, end-to-end latency instrumentation, `pose_degraded`. A test drives a closed-loop stop from scripted pose and asserts the trial ended on the predicate, not the timer. Resolves both open decisions above. |
| A18 | Trigger output layer | `TriggerBackend` Protocol + `NullTrigger` + `JetsonGpioTrigger`. Trial-boundary and pose-conditional output, wrapped so a failure only sets `trigger_failed`. GPIO edge observed on a scope against the mock provider; measured output latency recorded in `JETSON.md`. |
| A19 | DLC-Live provider | Needs a trained model. `DLCLivePoseProvider` behind the same Protocol, TensorRT export, warm-up on session start, measured p50/p99 against A11's budget. |
| A20 | Rig verification on the Jetson | `tools/verify_rig.py`: all cameras open and stream, per-camera `UserSet` verified, zero dropped/incomplete frames and no frame-ID gaps over 60 s, monotonic timestamps, cross-camera spans agreeing within tolerance, playable fragmented MP4 per camera — **all while inference runs**. Then `pytest -m hardware`. |
| A21 | Package restructure | Optional, cosmetic: `acquisition/acquisition/` → `acquisition/core/`, backends under `core/devices/`. Deliberately last so it never blocks working software. Drop it if not worth the diff. |

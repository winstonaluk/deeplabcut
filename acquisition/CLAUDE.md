# CLAUDE.md

Project context for the behavioral acquisition GUI. This file is auto-loaded each
session — treat everything here as standing rules unless I say otherwise in chat.

---

## What this is

A multi-camera behavioral video acquisition application for a rodent
neuroscience lab. Replaces vendor capture tooling (SpinView) which requires
manual start/stop and post-hoc association of video files with animal metadata.
This app binds metadata at write time and reduces per-trial interaction to a
single keypress.

Current paradigm: **PDCT**. The architecture must accommodate future paradigms
(maze task) and additional cameras without a rewrite.

## Glossary

| Term | Meaning |
|---|---|
| **PDCT** | Pole Descent Cognitive Test. Rat placed atop a vertical pole, descends. |
| **Trial** | One descent, start to finish. Currently 1–5 minutes for our rats. |
| **Session** | All trials for one animal on one day. |
| **DeepLabCut / DLC** | Markerless pose-estimation framework. Consumes our video offline. |
| **DLC-Live** | Real-time DLC inference. Not implemented yet; interface stubbed only. |
| **Anipose** | Multi-camera 3D triangulation built on DLC. Future downstream consumer. |
| **Spinnaker / PySpin** | Teledyne FLIR camera SDK and its Python bindings. |
| **UserSet** | Camera-onboard settings profile. We use `UserSet1`, configured in SpinView. |
| **Chunk data** | Per-frame metadata (hardware timestamp, frame ID) embedded by the camera. |

## Domain context

These facts drive design decisions — don't optimize against them.

- Subjects are **rats**. Trials run **~1–5 minutes**, long relative to typical
  mouse PDCT. May shorten as training improves, so **every duration threshold is
  a config value, never a literal**.
- The experimenter stands and observes throughout a trial. Mid-trial keypresses
  are cheap and are the preferred annotation point.
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

**Acquisition PC (runs this app):** i7-7700 @ 3.60 GHz · 16 GB RAM · Intel HD
Graphics 630 · 500 GB total · Windows.

- HD 630 has **no CUDA and no usable GPU compute**. Never propose GPU inference here.
- HD 630 **does** have Quick Sync fixed-function H.264/HEVC encode. Use it.
- 500 GB is a real constraint. Disk management is a feature, not an afterthought.

**Camera:** one Teledyne FLIR **Blackfly S BFS-U3-04S2C**, serial `22514545`,
USB3, global shutter, via Spinnaker/PySpin 4.3.0.190. Two more views (lateral,
top-down) come later.

- Sensor is **720 × 540** (Sony IMX287, 0.4 MP) — *not* 1280 × 720. The old
  "720p60" note was a misread of "720 × 540"; every figure derived from it was
  wrong-high.
- It is a **colour** sensor (`BayerRG8`). We record Mono8, which on this camera
  is luma derived from the Bayer mosaic rather than a native mono readout.
- Python is pinned to **3.10** by the `cp310` PySpin wheel; numpy must be **< 2**.

`acquisition/acquisition/HARDWARE.md` records what the camera actually reports,
measured rather than assumed. **When it and a design note disagree, it wins.**
Regenerate it with `python tools/probe_camera.py` after any firmware change,
camera swap, or SpinView reconfiguration.

## Stack

Python **3.10 exactly** (pinned by the `cp310` PySpin wheel — `tomllib` is 3.11+,
so config loading falls back to the `tomli` backport) · PySide6 (LGPL — **not
PyQt5**) · PySpin · numpy **< 2** (PySpin does not support 2.x) · FFmpeg via
subprocess (`h264_qsv`, fallback `libx264`).

## Architecture invariants

Do not violate these. If a request seems to require breaking one, stop and ask.

1. **N-camera by construction.** Cameras come from a config list, currently one
   entry. No single-camera assumptions anywhere.
2. **Mock backend is first-class.** `CameraBackend` is abstract with
   `SpinnakerCamera` and `MockCamera` implementations. The whole app must run and
   all tests must pass with zero hardware attached.
3. **Capture never blocks.** One capture thread per camera using Spinnaker's
   image event handler (not polling) → bounded queue → separate writer thread
   piping to FFmpeg. On queue-full: drop frame, increment counter, log. Never block.
4. **Recording integrity is independent of everything else.** The GUI thread and
   any pose component can fail without affecting the recording.
5. **Preview is throttled** to ~15 fps regardless of 60 fps capture, and reads
   latest-frame rather than consuming the write queue.
6. **Hardware timestamps only.** Chunk data timestamps + frame IDs to a per-trial
   CSV sidecar. Never substitute host wall-clock arrival time. Requires the app
   to enable chunk data — see the carve-out in invariant 7.
7. **No camera configuration UI.** Exposure/gain/ROI/gamma/trigger are set in
   SpinView and saved to `UserSet1`. App calls `UserSetLoad` at startup, verifies
   against the `[camera_verify]` table in config, and logs the result. Never
   expose these as editable controls, and never write a node to make a check
   pass — the app refuses to record against a wrongly-configured camera, it does
   not silently fix one.

   **Carve-out:** this invariant governs *image-formation* parameters, the ones
   that change what the science looks like. It does not cover settings that are
   data-integrity requirements of this app, which the app sets itself and logs:
   **chunk data** (`ChunkModeActive`, `ChunkEnable` for FrameID and Timestamp —
   invariant 6 is unsatisfiable without them, and the camera ships with them
   off) and **stream buffers** (`StreamBufferHandlingMode`,
   `StreamBufferCountManual` — these live in the transport-layer nodemap, which
   user sets do not cover at all).
8. **Trial stop is a pluggable predicate.** Currently keypress-driven; will become
   pose-driven. Never weld the stop condition into a Qt event handler.
9. **Config over literals.** Durations, thresholds, keymaps, paths, encoder
   settings all live in TOML.
10. **Long-run stability.** Multi-minute trials mean the writer sustains
    continuous throughput with no unbounded memory growth.

## Out of scope — do not build

- Any actual pose inference (`NullPoseProvider` only; interface stubbed)
- The maze paradigm (define the seam, ship only `PDCTParadigm`)
- Electrophysiology trigger logic (`TriggerService.on_pose()` is a no-op hook)
- Camera configuration UI (invariant 7)
- Custom stylesheets, theming, icon packs

## GUI style

**Deliberately plain.** Stock Qt widgets, standard layouts, three screens:
session setup, recording, end-of-session review.

One exception: on the recording screen, **trial counter, current state, elapsed
time, active flags, and dropped-frame count render in a large font**, readable
from several feet away with an animal in hand.

## Metadata schema

**Session-level** (entered once, locks on start):

| Field | Type | Notes |
|---|---|---|
| `animal_id` | text | Regex-validated; autocompletes from prior IDs in this project |
| `project_name` | dropdown | From config. Not free text. |
| `date` | auto | ISO `YYYYMMDD` |
| `experimenter_initials` | dropdown | From config |

Labels defined in one place for easy editing.

**Auto-captured:** session start timestamp · camera serials and loaded `UserSet1`
values · app version / git commit · FFmpeg encoder + params · rig ID · per-trial
frame count, dropped-frame count, achieved fps, exact duration.

**Per-trial:** trial number · start time · `flags` (set of experimenter reason
codes; empty = valid) · `auto_flags` (set applied by the app, kept separate) ·
optional note.

## Trial annotation

**Every trial is valid by default. Annotation is subtractive and never blocking** —
the experimenter is never forced into a dialog to reach the next trial.

Reason-code hotkeys, live **both during a trial and after it ends**:

| Key | Code | Meaning |
|---|---|---|
| `F` | `fall` | Fell from the pole |
| `Z` | `freeze` | Froze partway down |
| `D` | `did_not_descend` | Never initiated descent |
| `E` | `experimenter_error` | Handling/placement error |
| `V` | `other_invalid` | Generic; reason assigned later |

- Each key **toggles** its own flag. Flags are **not mutually exclusive** — freeze
  then fall records both.
- **Target trial** = currently recording trial if active, else most recently
  completed trial. Annotating a few seconds late must work.
- The whole keymap is a `key → reason_code` table in TOML. New paradigms define
  different codes without source changes.
- Visual feedback: large labelled chips for active flags, trial counter changes
  colour when flagged, brief confirmation on toggle.

## Trial state machine

`IDLE` → `RECORDING` → `IDLE`. Spacebar starts and stops.

| Config key | Default | Behavior |
|---|---|---|
| `min_trial_duration_s` | 5 | Spacebar swallowed entirely within this window; prevents double-tap zero-length trials. Show a countdown so the dead key is explained. |
| `suspicious_duration_s` | 30 | Trials shorter than this get `auto_flags: [suspiciously_short]`. No real descent is this fast. |
| `max_trial_duration_s` | 600 | Auto-stop + `auto_flags: [max_duration_reached]`. An animal may never descend; recording must not run away with the disk. Warn on-screen as the cap nears. |

`Ctrl+Delete` discards the last trial (video + sidecar + metadata) after
confirmation, decrementing the counter. Every hotkey also has a large on-screen button.

## Pre-roll buffer

Rolling in-RAM buffer of the most recent **2 s** (config) per camera, running
whenever streaming — not just during trials. Prepended on trial start so descent
onset is never clipped by reaction time. **~23 MB** per camera per 2 s at
720 × 540 Mono8 / 30 fps.

## Files and naming

```
<session_root>/<animal_id>_<project_name>_<date>_<initials>/
    session_metadata.json
    trials.csv
    <animal_id>_<project_name>_<date>_<initials>_<HHMM>_t001.mp4
    <animal_id>_<project_name>_<date>_<initials>_<HHMM>_t001_timestamps.csv
    ...
```

- `<HHMM>` = trial start time. `t<NNN>` = zero-padded trial number, which alone
  guarantees uniqueness; HHMM is informational and disambiguates repeat sessions
  on the same animal same day.
- Optional `<view>` token, config-toggleable, **default off**. Enable when more
  cameras are added — DLC flattens folder structure on import, so filenames must
  stand alone.
- Never overwrite an existing session directory.
- `trials.csv` exports the trial table so downstream analysis filters the
  training-frame pool on flags without parsing JSON. Valid/invalid must be
  trivially machine-readable.
- `session_metadata.json` carries a `schema_version` key.

## Cross-repo contract

`session_metadata.json`, `trials.csv`, and the timestamp sidecars are the
**interface to the analysis repo**, which reads them as the spine of its manifest.

- Schemas live in `shared/schema/` and are imported here, never redefined locally.
- Both carry `schema_version`. Any field change is a version bump.
- Never change a field name, type, or meaning without updating `shared/schema/`
  and the analysis repo's manifest stage in the same commit.

## Storage

Acquisition runs at **30 fps** (fps is a config value; the sensor can go far
faster, but exposure time is the binding constraint). Raw rate is **11.7 MB/s**
at 720 × 540 Mono8. Encoded output measured at **5.6 MB/min at 66 fps** with
`h264_qsv`, so expect roughly half that at 30 fps — a 5-minute trial in the low
tens of MB, far below the old ~37 MB/min figure, which was computed for
1280 × 720. Re-measure on real footage (`tools/measure_encoder.py`) once
`UserSet1` is configured, since a static test scene compresses optimistically.
Transfer workflow is still worth having, but disk is not the binding
constraint it was assumed to be.

- Live free-space indicator **and estimated remaining-recording-time** from
  measured bitrate. GB free is not actionable mid-session; "47 min remaining" is.
- Hard block on session start below threshold, surfaced as a clear preflight failure.
- `h264_qsv` primary, fallback `libx264`. Quality is configured **per codec** —
  `-crf` and `-global_quality` are different scales and a shared number gives
  two different qualities depending on which encoder resolved.
- "Stage for transfer": package completed sessions to a staging dir with checksum
  verification. Remote is a **generic mounted path / rsync / robocopy target** —
  never hardcode an institution-specific system.
- Purge-after-verified-transfer requires explicit confirmation.

## Encoder tuning

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

## Preflight checks

Camera detected · `UserSet1` loaded · every `[camera_verify]` node matching ·
reported resolution matching config · reported frame rate matching config
within `capture.fps_tolerance` · FFmpeg available · free disk above threshold.
Block recording and show a clear message on any failure.

**Config is not ground truth about the hardware** — it is what we intend the
hardware to be doing. The backend reports what it is *actually* doing
(`resolution`, `pixel_format`, `frame_rate`, `verify_settings`) and preflight
compares the two. Never assume they agree: a 1280 × 720 config value meeting a
720 × 540 sensor produced no error at all, just silently sheared video.

Preflight does not short-circuit on the first failure. An experimenter with an
animal in hand should see everything that needs fixing in one pass.

## Project structure

```
gui/           PySide6 screens and widgets
acquisition/   CameraBackend, capture threads, ring buffer, writer
               HARDWARE.md      what the camera measurably is
               SPINNAKER_PLAN.md  A10 implementation plan
paradigms/     Paradigm ABC + PDCTParadigm
storage/       Naming, metadata, sidecars, disk mgmt, staging
pose/          PoseProvider protocol, NullPoseProvider, TriggerService stub
tools/         Hardware probes. Need PySpin; outside the package and the suite.
tests/
config.toml
```

## Commands

```bash
# run against synthetic frames, no hardware
python -m app --mock

# run against real camera
python -m app

# tests (must pass with no hardware attached; hardware tests deselected)
pytest

# the hardware-marked subset, at the rig
pytest -m hardware

# record 60 s from the real camera and check A10's done-criteria
python tools/verify_a10.py

# read the camera and refresh HARDWARE.md (acquisition PC only; needs PySpin)
python tools/probe_camera.py

# sweep encoder settings over a real trial; needs FFmpeg
python tools/measure_encoder.py REFERENCE.mp4
```

Tests that spawn FFmpeg are marked `requires_ffmpeg` and skip automatically when
it isn't on PATH, so a missing external binary reports as one named skip rather
than eleven identical tracebacks. **FFmpeg is not currently installed on the
acquisition PC.**

## Conventions

- Type hints throughout; `Protocol` for interfaces
- Dataclasses for metadata records
- Structured logging to a per-session log file, not bare `print`
- Every threshold, path, keybinding, and encoder setting reaches code via config
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

## Checkpoints

`A0` is shared with the analysis repo and must exist before anything else.

| ID | Name | Done when |
|---|---|---|
| A0 | Shared schema | `shared/schema/` defines `session_metadata.json`, `trials.csv`, and timestamp-sidecar schemas with `schema_version`. Both repos import it. |
| A1 | Interfaces + skeleton | Package layout exists; `CameraBackend`, `Paradigm`, `PoseProvider`, and the trial state machine are defined with full type signatures and docstrings. **No implementation bodies.** `config.toml` schema complete with every key and default. Tests importable. |
| A2 | Mock capture end-to-end | `MockCamera` → capture thread → bounded queue → writer → playable H.264 file. Dropped-frame counter increments correctly under induced backpressure. Long-run test shows flat memory. |
| A3 | Trial state machine | All guards implemented and tested: min-duration swallow, max-duration auto-stop, suspicious-short auto-flag, discard-last. Stop condition is a pluggable predicate. |
| A4 | Metadata + naming | Filename generation, `session_metadata.json`, `trials.csv`, timestamp sidecars, flag/`auto_flag` sets, schema validation. All against `shared/schema/`. Round-trip tests. |
| A5 | Session setup screen | Form, dropdowns from config, validation, autocomplete, preflight checks, lock-on-start. |
| A6 | Recording screen | Preview tiles, large-font readouts, spacebar control, reason-code hotkeys from the config keymap, flag targeting (current-if-recording else most-recent), visual flag feedback. |
| A7 | Review screen | Trial table, flag editing, note entry, `other_invalid` reason assignment. Skippable. |
| A8 | Storage + staging | Free-space indicator, remaining-time estimate, hard block below threshold, staging with checksum verification, confirm-gated purge. |
| A9 | `SpinnakerCamera` scaffold | **Done.** Class scaffolded against `CameraBackend`, plan written. Superseded by the A9.5 schema pass below, which rewrote the plan against real hardware. |
| A9.5 | Camera backend schema | **Done.** Backend reports `resolution`, `pixel_format`, `frame_rate`, `verify_settings`, `incomplete_frame_count`; preflight asserts config against all of them; writer derives geometry and pixel format from the backend; `[camera_verify]` table in config; `HARDWARE.md` records the measured camera. |
| A10 | `SpinnakerCamera` implementation | **Code complete, verification blocked on rig config.** All five lifecycle bodies implemented and streaming from the real camera: 60 s / 3960 frames with zero drops, zero incomplete, no frame-ID gaps, monotonic hardware timestamps, `h264_qsv` output. Run `python tools/verify_a10.py`. The remaining failures are all one cause — `UserSet1` still holds factory defaults, so exposure/gain/gamma/pixel-format/frame-rate checks fail. **Needs SpinView at the rig**, then re-run. |
| A11 | Application wiring | **Not started.** Nothing outside tests constructs a camera, `CaptureController`, `CameraRig`, or any screen; `app/__main__.py` raises `NotImplementedError` and `resolve_encoder()` is never called by the app. Every part is built and tested, but `python -m app` does not run. This composition root is what stands between the repo and lab use. |

# Claude Code Prompt — Behavioral Acquisition GUI (v3)

> Paste everything below the line into Claude Code as your opening message.
> Recommended: run `claude` in an empty project directory first.

---

## Project

Build a behavioral video acquisition application for a rodent neuroscience lab.
The immediate paradigm is the **Pole Descent Cognitive Test (PDCT)**: a rat is
placed at the top of a vertical pole and descends; we record descent kinematics.
The architecture must later accommodate additional paradigms (e.g. a maze task)
and additional cameras without a rewrite.

The core problem this solves: recording with the vendor's generic capture tool
(SpinView) requires manual start/stop and post-hoc association of video files
with animal/session metadata. That is error-prone and slow when the experimenter
is physically handling an animal. This app binds metadata at write time and
reduces per-trial interaction to a single keypress.

## Behavioral context (drives several design decisions below)

- Subjects are **rats**. Observed descent duration currently ranges from
  **~1 to ~5 minutes** per trial. This is long relative to typical mouse PDCT and
  may shorten as animal training improves — so all duration-related thresholds
  must be config values, never hardcoded.
- Trials are long enough that the experimenter is standing and observing
  throughout. Mid-trial keypresses are therefore cheap and are the preferred
  interaction point for annotation.
- Common failure modes observed during a trial: the animal **falls**, **freezes**
  partway down, or **never descends at all**. These need to be capturable in the
  moment.
- Trial duration is the **primary dependent variable**. Anything that corrupts it
  (falls, freezes) makes a trial unusable rather than merely noisy, so exclusion
  metadata is scientifically load-bearing, not bookkeeping.

## Hard constraints

**Acquisition PC (the machine this runs on):**
- Intel i7-7700 @ 3.60 GHz, 16 GB RAM
- Intel HD Graphics 630 (no CUDA, no usable GPU compute — but **does** have
  Quick Sync fixed-function H.264/HEVC hardware encode)
- 500 GB total storage — disk management is a first-class feature
- Windows

**Camera:**
- **One** Teledyne FLIR machine vision camera via the **Spinnaker SDK**
  (`PySpin` Python bindings), 720p60, global shutter
- **Important:** the camera layer must be written as an N-camera system driven by
  a list in the config file, currently populated with a single entry. Two
  additional views (lateral and top-down) will be added later and must not
  require refactoring. Do not hardcode single-camera assumptions.

**Language/stack:**
- Python 3.10+
- **PySide6** for the GUI (LGPL — not PyQt5)
- `PySpin` for camera control
- FFmpeg (via subprocess) for H.264 encoding using Quick Sync (`h264_qsv`),
  with a `libx264` software fallback

## Critical architecture requirements

Non-negotiable design decisions. Follow them rather than proposing alternatives.

### 1. Camera abstraction with a mock backend — build this FIRST

Define an abstract `CameraBackend` interface. Provide **two** implementations:

- `SpinnakerCamera` — real hardware via PySpin
- `MockCamera` — synthesizes frames (moving shape on a gradient, burned-in frame
  counter and timestamp) at a configurable fps

The entire application must be fully runnable and testable with zero hardware
attached, selected by a config flag or CLI argument. **Implement and validate the
mock path end-to-end before writing any PySpin code.** I need to develop away
from the rig.

### 2. Threading model — capture, encode, and display are decoupled

- One capture thread per camera. Use Spinnaker's **image event handler** callback
  pattern, not polling.
- Frames go into a **bounded** queue per camera. If the queue fills, drop the
  frame, increment a visible dropped-frame counter, and log it. Never block the
  capture thread.
- A separate writer thread/process pipes frames to FFmpeg via stdin.
- GUI preview is **throttled to ~15 fps** regardless of the 60 fps capture rate,
  and reads the latest available frame rather than consuming the write queue.
- Recording integrity must never depend on the GUI thread or on any pose-inference
  component.
- Trials run for minutes, so the writer must sustain continuous throughput
  indefinitely without unbounded memory growth. Verify with a long-run mock test.

### 3. Pre-roll ring buffer

Continuously maintain a rolling in-RAM buffer of the most recent **2 seconds**
(configurable) of frames per camera, running whenever the camera is streaming —
not just during a trial. When a trial starts, prepend the buffer contents to the
recording so descent onset is never clipped by reaction time.

At 720p Mono8 / 60 fps this is roughly 110 MB per camera per 2 seconds.

### 4. Do NOT build camera configuration UI

Exposure, gain, ROI, gamma, and trigger mode are configured externally in SpinView
and persisted to the camera's onboard `UserSet1`. On startup the app calls
`UserSetSelector`/`UserSetLoad` to load `UserSet1`, then verifies and logs the
resulting settings into session metadata. Do not expose these as editable controls.

### 5. Preserve hardware timestamps

Enable Spinnaker **chunk data** to retrieve per-frame camera timestamps and frame
IDs. Write these to a per-trial CSV sidecar alongside every video. This is
required for future electrophysiology alignment and 3D triangulation. Do not rely
on host-side wall-clock arrival time as the frame timestamp.

### 6. Paradigm plugin seam — but implement only PDCT

Define a `Paradigm` abstraction covering the metadata schema, the trial state
machine, and output naming conventions. Ship exactly one concrete implementation,
`PDCTParadigm`. Do not build a maze paradigm. The seam should make adding one
later a matter of writing a new class, not touching the acquisition core.

### 7. PoseProvider interface — stubbed only

```python
class PoseProvider(Protocol):
    def send_frame(self, frame: np.ndarray, timestamp: float) -> None: ...
    def get_latest_pose(self) -> PoseResult | None: ...   # non-blocking
```

Provide a `NullPoseProvider` that does nothing, and wire the interface into the
capture path so it can be swapped later for network-offload or on-device
(Jetson) inference. **Do not implement any actual inference.** Include a
`TriggerService.on_pose(pose)` no-op hook for future closed-loop use.

Note: trial termination is currently manual (spacebar). It will later become
automatic, driven by pose. Structure the trial state machine so the stop
condition is a **pluggable predicate**, not hardcoded to the keypress handler.

## Metadata schema

### Session-level (entered once, locks on session start)

| Field | Type | Notes |
|---|---|---|
| `animal_id` | text | Regex-validated, autocomplete from previously used IDs in this project |
| `project_name` | **dropdown** | Options read from the config file. Not free text. |
| `date` | auto | Autofilled, forced to ISO `YYYYMMDD` |
| `experimenter_initials` | **dropdown** | Options from config file |

Field labels should be defined in one place so they are trivially editable later.

### Auto-captured (no user interaction)

- Session start timestamp
- Camera serial(s) and the `UserSet1` settings actually loaded
- App version / git commit
- FFmpeg encoder and parameters used
- Rig/apparatus ID (from config)
- Per-trial: frame count, dropped-frame count, achieved fps, exact duration

### Per-trial

- Trial number (auto-incrementing)
- Trial start time
- `flags`: a **set** of reason codes (see below). Empty set means a valid trial.
- `auto_flags`: a separate set applied by the application itself, distinguishable
  from experimenter-applied flags
- Optional short free-text note

## Trial annotation — hotkey-driven flagging

**Design principle: every trial is valid by default. Annotation is subtractive,
never a required step.** The experimenter must never be forced into a dialog or a
decision in order to proceed to the next trial.

### Reason-code hotkeys

Provide dedicated toggle hotkeys, one per reason code. All of them are live
**both during a trial and after it ends**:

| Key | Reason code | Meaning |
|---|---|---|
| `F` | `fall` | Animal fell from the pole |
| `Z` | `freeze` | Animal froze partway down |
| `D` | `did_not_descend` | Animal never initiated descent |
| `E` | `experimenter_error` | Handling/placement error |
| `V` | `other_invalid` | Generic invalid, reason assigned later |

Behavior:
- Each key **toggles** its own flag on the target trial. Pressing it again removes
  that flag.
- Flags are **not mutually exclusive** — an animal can freeze and then fall, and
  both should be recordable.
- **Target trial** = the currently recording trial if one is active, otherwise the
  most recently completed trial. This lets the experimenter annotate in the moment
  or a few seconds later, whichever fits.
- The **entire keymap must live in the config file** as a `key -> reason_code`
  table so codes and bindings can be edited without touching source. New paradigms
  will need different codes.

### Visual feedback

Flag state must be unmistakable at a glance from across the rig:
- Active flags on the target trial shown as large labelled chips (e.g. `FALL`,
  `FREEZE`) in a high-contrast colour
- The trial counter changes colour when the target trial carries any flag
- A brief on-screen confirmation when a flag toggles, so the experimenter knows
  the keypress registered without looking away from the animal

### End-of-session review screen

After the session ends, show a simple table of all trials: number, start time,
duration, flags, notes. Allow editing flags and adding notes here, and assigning a
reason to any trial flagged only as `other_invalid`. This is where unhurried
cleanup happens — it must be optional and skippable.

## Trial state machine

States: `IDLE` → `RECORDING` → `IDLE`

- **Spacebar** starts a trial. Spacebar again stops it.
- **Minimum trial duration** (`min_trial_duration_s`, default 5). Spacebar presses
  within this window are swallowed entirely — no stop, no glitch. Prevents
  accidental double-taps creating zero-length trials. Show a small countdown so
  it's obvious why the key isn't responding. Legitimate trials run 1–5 minutes, so
  this guard is far below any real trial length; keep it trivially editable.
- **Suspiciously-short auto-flag** (`suspicious_duration_s`, default 30). Any trial
  ending below this is automatically given an `auto_flags` entry of
  `suspiciously_short` and highlighted in the review screen. No real descent is
  this fast, so it almost certainly indicates a mis-press.
- **Maximum trial duration auto-stop** (`max_trial_duration_s`, default 600).
  Because an animal may simply never descend, a trial must not be able to record
  indefinitely and consume the disk. On hitting the cap, auto-stop the trial and
  apply `auto_flags: [max_duration_reached]`. Warn on-screen as the cap approaches.
- **Discard last trial** (`Ctrl+Delete`) — deletes the most recent trial's video,
  sidecar, and metadata record after a confirm dialog, and decrements the counter.
- Also expose large on-screen buttons for every hotkey action.

## File naming and output structure

```
<session_root>/<animal_id>_<project_name>_<date>_<initials>/
    session_metadata.json
    <animal_id>_<project_name>_<date>_<initials>_<HHMM>_t001.mp4
    <animal_id>_<project_name>_<date>_<initials>_<HHMM>_t001_timestamps.csv
    <animal_id>_<project_name>_<date>_<initials>_<HHMM>_t002.mp4
    ...
```

- `<HHMM>` is the **trial** start time; `t<NNN>` is the zero-padded trial number.
  Trial number alone guarantees uniqueness — HHMM is informational and also
  disambiguates repeat sessions on the same animal on the same day.
- Add an **optional** `<view>` token (config-toggleable, default off) to the
  filename, so that when additional cameras are added the names stay unique even
  after DeepLabCut flattens the folder structure during import.
- Never overwrite an existing session directory.
- `session_metadata.json` holds the session form, all per-trial records, and all
  auto-captured fields, with a `schema_version` key.
- Provide an **export of the trial table to CSV** so flags and durations can be
  read directly by downstream analysis without parsing JSON. Downstream tooling
  will filter the training-frame pool on these flags, so the export must make
  valid/invalid trivially machine-readable.

## Storage management

Volume is substantial: at 720p60 H.264 (~75 MB/min), a 3-minute trial is roughly
225 MB, and a 10-trial session around 2–3 GB on one camera — 6–9 GB once three
cameras are added. Against ~350 GB usable, the transfer workflow is essential
rather than a convenience.

- Live free-space indicator **and an estimated remaining-recording-time readout**
  based on measured bitrate, shown during recording.
- Hard block on starting a session below a configurable threshold, surfaced as a
  clear preflight failure message.
- H.264 encode via `h264_qsv` at CRF ~18 (configurable), falling back to
  `libx264`. Quality matters — this video becomes pose-estimation training data,
  so avoid aggressive compression.
- A "stage for transfer" action that packages completed sessions into a staging
  directory and verifies checksums, for pushing to institutional network storage.
  Treat the remote as a generic mounted path or rsync/robocopy target; do not
  hardcode any institution-specific system.
- Purge-after-verified-transfer requires explicit confirmation.

## GUI style

**Deliberately plain.** Stock Qt widgets only — no custom stylesheets, no
theming, no icon packs. Three screens (session setup, recording, end-of-session
review), standard layouts.

The single exception: on the recording screen, the **trial counter, current state,
elapsed time, active flags, and dropped-frame counter must be rendered in a large
font**, readable from several feet away. The experimenter will be reading them
from across the rig with an animal in hand, over multi-minute trials.

Preflight checks before recording can begin: camera detected, `UserSet1` loaded,
FFmpeg available, free disk space above threshold.

## Deliverables

1. Clean package layout separating `gui/`, `acquisition/`, `paradigms/`,
   `storage/`, and `pose/`
2. A config file (TOML) covering: camera list, project-name options, initials
   options, paths, disk threshold, encoder settings, pre-roll duration,
   `min_trial_duration_s`, `suspicious_duration_s`, `max_trial_duration_s`, and
   the full flag keymap
3. `requirements.txt` / `pyproject.toml`
4. Unit tests for the trial state machine (minimum-duration guard, max-duration
   auto-stop, suspicious-short auto-flag), flag toggling and targeting logic,
   metadata schema validation, filename generation, and bounded-queue drop
   behavior — all runnable against `MockCamera` with no hardware
5. A README covering setup, the SpinView `UserSet1` configuration step, the hotkey
   reference, and how to run in mock mode

## Working style

Start by proposing the module layout and the core interfaces (`CameraBackend`,
`Paradigm`, `PoseProvider`, trial state machine) and let me review them before
writing the full implementation. Then build the mock-camera path end-to-end
before touching PySpin.

Ask me about anything ambiguous rather than guessing — particularly around trial
state machine semantics and metadata fields, since those encode experimental
design decisions.

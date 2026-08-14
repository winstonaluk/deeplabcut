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
  accuracy; do not trade quality for file size.

## Hardware

**Acquisition PC (runs this app):** i7-7700 @ 3.60 GHz · 16 GB RAM · Intel HD
Graphics 630 · 500 GB total · Windows.

- HD 630 has **no CUDA and no usable GPU compute**. Never propose GPU inference here.
- HD 630 **does** have Quick Sync fixed-function H.264/HEVC encode. Use it.
- 500 GB is a real constraint. Disk management is a feature, not an afterthought.

**Camera:** one Teledyne FLIR machine vision camera, 720p60, global shutter, via
Spinnaker/PySpin. Two more views (lateral, top-down) come later.

## Stack

Python 3.10+ · PySide6 (LGPL — **not PyQt5**) · PySpin · FFmpeg via subprocess
(`h264_qsv`, fallback `libx264`).

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
   CSV sidecar. Never substitute host wall-clock arrival time.
7. **No camera configuration UI.** Exposure/gain/ROI/gamma/trigger are set in
   SpinView and saved to `UserSet1`. App calls `UserSetLoad` at startup, verifies,
   and logs the result. Never expose these as editable controls.
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
onset is never clipped by reaction time. ~55 MB per camera per 2 s at 720p Mono8/30fps.

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

Acquisition runs at **30 fps** (camera capable of 60; fps is a config value).
~37 MB/min at 720p30 H.264. A 3-min trial ≈ 110 MB; a 10-trial session ≈ 1.1 GB
on one camera, ~3.3 GB at three. Against ~350 GB usable, transfer workflow is
essential, not a convenience.

- Live free-space indicator **and estimated remaining-recording-time** from
  measured bitrate. GB free is not actionable mid-session; "47 min remaining" is.
- Hard block on session start below threshold, surfaced as a clear preflight failure.
- `h264_qsv` at CRF ~18 (config), fallback `libx264`.
- "Stage for transfer": package completed sessions to a staging dir with checksum
  verification. Remote is a **generic mounted path / rsync / robocopy target** —
  never hardcode an institution-specific system.
- Purge-after-verified-transfer requires explicit confirmation.

## Preflight checks

Camera detected · `UserSet1` loaded and verified · FFmpeg available · free disk
above threshold. Block recording and show a clear message on any failure.

## Project structure

```
gui/           PySide6 screens and widgets
acquisition/   CameraBackend, capture threads, ring buffer, writer
paradigms/     Paradigm ABC + PDCTParadigm
storage/       Naming, metadata, sidecars, disk mgmt, staging
pose/          PoseProvider protocol, NullPoseProvider, TriggerService stub
tests/
config.toml
```

## Commands

```bash
# run against synthetic frames, no hardware
python -m app --mock

# run against real camera
python -m app

# tests (must pass with no hardware attached)
pytest
```

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
| A9 | `SpinnakerCamera` | **Not buildable unattended — requires hardware.** Scaffold the class against `CameraBackend` with `NotImplementedError` bodies and a written plan referencing the PySpin examples. |

# Questions logged during unattended build

One entry per ambiguity: file, the decision faced, options considered, which
was chosen, and why. Implemented as the most conservative interpretation per
`overnight-prompt.md`.

---

## A3 · trial-state-machine-min-duration-vs-predicate

**File:** `acquisition/acquisition/trial_state_machine.py`, `tick()`

**Decision faced:** `min_trial_duration_s` exists to swallow "double-tap
zero-length trials" from spacebar presses (acquisition/CLAUDE.md, "Trial
state machine" table). It's unclear whether that guard should also apply to
a future pose-driven `TrialStopCondition` firing `should_stop() == True`
before `min_trial_duration_s` has elapsed -- a predicate-triggered stop has
no "double-tap" to guard against.

**Options considered:**
1. Apply the min-duration guard uniformly to both manual (spacebar) and
   predicate-triggered stops.
2. Let a predicate-triggered stop bypass the guard entirely.

**Chosen:** (1) -- applied uniformly. Most conservative: it never produces a
trial shorter than `min_trial_duration_s` regardless of stop source, and
today's `KeypressStopCondition` never actually signals `should_stop()==True`
on its own, so this has zero effect on the current PDCT paradigm. A future
pose-driven paradigm author should revisit this when that predicate is
actually wired to something.

**Rework if wrong:** low. Isolated to `tick()`'s early-return condition; no
schema or file-format impact.

---

## A3 · trial-state-machine-predicate-stop-auto-flag

**File:** `acquisition/acquisition/trial_state_machine.py`, `tick()`

**Decision faced:** `max_trial_duration_s` auto-stop applies `auto_flags:
[max_duration_reached]`. CLAUDE.md doesn't specify whether a stop triggered
by `TrialStopCondition.should_stop()` (the pose-driven seam, not yet wired to
anything real) should carry its own distinct auto_flag.

**Chosen:** No extra auto_flag beyond whatever `suspiciously_short` the
final duration earns on its own merits. Conservative because inventing a new
auto_flag vocabulary entry (e.g. `predicate_stop`) now, before any predicate
actually exists beyond the inert `KeypressStopCondition`, risks a schema/QC
rule (analysis stage 1 `qc_gate`) being built against a code that may not
match what a real pose-driven condition eventually needs to express.

**Rework if wrong:** low-medium. If a future pose paradigm needs to
distinguish predicate-triggered stops in `trials.csv`/`auto_flags`, this is
a one-line addition in `_finalize_trial`'s caller in `tick()`, not a schema
change (the `auto_flags` field is an open string set already).

---

## B1 · stage-2-calibration-has-no-checkpoint

**File:** `analysis/CLAUDE.md` checkpoint table; `analysis/pipeline/contracts.py`

**Decision faced:** Stage 8 (`kinematics`, checkpoint B4) requires camera
intrinsics to undistort coordinates (invariant 2). Those intrinsics come
from stage 2 (`calibration`), described in the "Stage contracts" section --
but stage 2 is not assigned to any of B1-B7, and `calibration` is not one of
the `python -m pipeline` subcommands listed under "Commands" either. Every
other stage in the contract table maps to a checkpoint (0->B2, 1->B3,
3/5/6/7->B7, 8->B4, 9->B5) or is explicitly manual (4, labeling); 2 is the
one gap.

**Options considered:**
1. Build the calibration stage anyway (checkerboard corner detection via
   `cv2.calibrateCamera`) since B4 needs its output.
2. Treat it as out of scope for this run, and have B4's kinematics stage
   accept calibration parameters (camera matrix + distortion coefficients)
   as an explicit input/argument rather than computing them.

**Chosen:** (2). Building an unassigned stage is scope expansion the
overnight-prompt.md instructions explicitly warn against ("do not expand
scope... however small it seems"), and checkerboard calibration inherently
needs real calibration images -- there's no synthetic-data path for it the
way B4's kinematics core has one, so it wouldn't be unattended-buildable
even if in scope. `contracts.py`'s `CalibrationRecord` defines the data
shape so B4 and a future calibration stage share one contract.

**Rework if wrong:** low. `CalibrationRecord`'s shape (camera matrix +
distortion coefficients) is the standard OpenCV pinhole model; a real
calibration stage that populates it later is additive, not a rewrite of B4.

---

## B3 · qc-nominal-fps

**File:** `analysis/config.toml` `[qc]`, `analysis/pipeline/config.py` `QCConfig`

**Decision faced:** The QC gate's "achieved_fps deviating from nominal ->
exclude" rule (analysis/CLAUDE.md stage 1 contract) needs a nominal fps to
compare against, but "Config keys" only lists "fps deviation" (i.e. the
threshold) under QC thresholds -- no key holding the nominal value itself.
`analysis.fps` exists but is explicitly about post-hoc downsampling for
kinematics (invariant 12: "Analysis frame rate is decoupled from
acquisition frame rate"), a different concept from what the camera was
actually configured to capture at.

**Options considered:**
1. Reuse `analysis.fps` as the QC nominal-fps comparison value.
2. Add a new `qc.nominal_fps` key, separate from `analysis.fps`.

**Chosen:** (2). Reusing `analysis.fps` would silently couple two concepts
invariant 12 explicitly says must stay decoupled -- if someone sets
`analysis.fps` to downsample kinematics, every trial would suddenly fail QC
for "fps deviation" even though nothing about the actual capture changed.
Added `qc.nominal_fps` (default 30.0, matching acquisition's config.toml
default `capture.fps`) as its own key instead.

**Rework if wrong:** low. Single config key; renaming or removing it later
touches only `QCConfig` and `qc_gate.py`'s one comparison.

---

## B5 · report-stage-cannot-group-by-animal

**File:** `analysis/pipeline/stages/report.py`

**Decision faced:** Stage 9's contract says "Group-level aggregation,
statistics, figures. Reads only trial_summary.parquet and
kinematics_long.parquet." But `TrialSummaryRow` and `KinematicsLongRow`
(both defined at B1) carry `trial_uid` and `primary_keypoint`/`keypoint`,
not `animal_id`/`project_name` -- so report cannot group by animal or
project without either (a) parsing those fields back out of `trial_uid`'s
compound string, or (b) reading manifest_qc.parquet too, which the stated
contract excludes.

**Options considered:**
1. Parse `trial_uid` (format `{animal_id}_{project_name}_{date}_{initials}_
   {view}_t{trial_number:03d}`, from `manifest.py`'s `trial_uid()`) back
   into fields via string splitting.
2. Only build grouping that's possible from the declared inputs as-is
   (by `primary_keypoint`, and an overall/ungrouped summary), and leave
   animal/project grouping as something the caller does by joining against
   the manifest separately before calling into this module.

**Chosen:** (2). `trial_uid` parsing is fragile: animal_id, project_name,
and initials are all free-ish text that can themselves contain
underscores, so splitting the compound string back into fields is
ambiguous in general, not just an edge case. Building `aggregate_overall()`
and `aggregate_by_keypoint()` against exactly what's in the declared
inputs, and leaving per-animal grouping to whoever has both the manifest
and the trial summary in hand, avoids a parser that would silently misparse
some fraction of real animal IDs.

**Rework if wrong:** low-medium. If animal-level grouping needs to live
inside this module later, the clean fix is adding `animal_id`/
`project_name` columns to `TrialSummaryRow` itself (populated once, when
the row is created from a `ManifestRow` + kinematics result) rather than
reconstructing them downstream -- an additive schema change, not a rewrite.

---

## B6 · kinematics-cli-stage-not-wired

**File:** `analysis/pipeline/orchestration.py`

**Decision faced:** B6 ("Per-stage commands") is checkpointed *before* B7
(stages 3/5/6/7, including `infer`, which produces stage 7's pose `.h5`
output). But `kinematics` (stage 8, B4) needs pose data as input, and B4 is
checkpointed *before* B6 too -- so at every point in the prescribed build
order, there is no real (or even placeholder) source of pose data for a
`python -m pipeline kinematics` command to read. B4's own checkpoint scope
was explicitly "the pure pipeline as testable functions" operating on
in-memory arrays, not a file-reading stage runner.

**Options considered:**
1. Fabricate a synthetic DLC-shaped `.h5` pose file (pandas
   MultiIndex-column format DLC uses) purely for testing, and write a real
   `kinematics` stage runner against that format now.
2. Register `kinematics` in the CLI/orchestration layer as present but not
   implemented (same as `extract`/`train`/`evaluate`/`infer`), leaving the
   file-I/O wiring for whenever stage 7's real output format is settled.

**Chosen:** (2). Option 1 would mean inventing stage 7's output contract
under time pressure specifically to unblock stage 8's CLI wiring, then
potentially having to redo that contract once B7's actual scaffold (or a
future real implementation) settles on a shape -- speculative plumbing
built to satisfy a checkpoint rather than a real requirement. `kinematics`'s
pure computational core (B4) is fully built and tested regardless; only its
CLI-level file-reading wrapper is deferred, for the same structural reason
B7's stages are scaffold-only.

**Rework if wrong:** low. Wiring `kinematics` into `STAGE_REGISTRY` later
is additive -- one more `Stage(...)` entry calling into B4's already-tested
`compute_trial_kinematics()`, not a change to anything already built.

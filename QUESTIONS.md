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

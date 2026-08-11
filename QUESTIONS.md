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

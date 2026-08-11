# Overnight build report

Run against `overnight-prompt.md`, executed interactively rather than
headless (`claude -p`) — the user asked me to "begin contributing to this
repo" referencing the overnight prompt directly in a live session. I kept
the unattended-run discipline anyway (log ambiguities to `QUESTIONS.md`
rather than asking, most-conservative interpretation, commit at every
checkpoint) since that's what produces an auditable, resumable trail either
way, and the checkpoint/testing bar is the same regardless of who's
watching.

**Outcome: both apps' full checkpoint lists are complete.** A0–A9
(acquisition) and B1–B7 (analysis) all pass their tests. 200 tests total —
81 acquisition, 113 analysis, 6 shared — with zero hardware, zero GPU, zero
DeepLabCut, and zero network required anywhere in the suite.

---

## 1. Checkpoints completed

Plus one pre-checkpoint commit for the monorepo layout itself.

| Commit | Checkpoint |
|---|---|
| `d6bf99e` | repo layout: monorepo structure per overnight-prompt.md |
| `24bd0d7` | A0: shared schema |
| `950e17f` | A1: acquisition interfaces + skeleton |
| `13f486f` | A2: mock capture end-to-end |
| `67d6d63` | A3: trial state machine guards |
| `3d5cc69` | A4: metadata + naming |
| `4f0d117` | A5: session setup screen |
| `cbc4a0e` | A6: recording screen |
| `8340db7` | A7: review screen |
| `b9d3c97` | A8: storage + staging |
| `c41af6d` | A9: SpinnakerCamera scaffold (not buildable unattended) |
| `ad70fcc` | B1: analysis skeleton + provenance |
| `7516597` | B2: stage 0 build_manifest |
| `d766348` | B3: stage 1 qc_gate |
| `babeb16` | B4: stage 8 kinematics core |
| `256987a` | B5: stage 9 report |
| `cb24d78` | B6: CLI + orchestration |
| `11bc250` | B7: scaffold stages 3/5/6/7 (not buildable unattended) |

Every checkpoint's tests pass; nothing was committed with `(tests failing)`.

Two conda environments (`dlc-acquisition`, `dlc-analysis`) were created
locally for isolated, reproducible test runs, with per-app `requirements.txt`
committed. These aren't part of the checkpoint list but were necessary
groundwork — the machine had no Python packages installed at session start.

## 2. Checkpoints attempted but failing

None. Every checkpoint's test suite passed before its commit.

## 3. Checkpoints not reached

None. A0–A9 and B1–B7 are all complete.

Two things are deliberately unbuilt, both because they are structurally
unbuildable unattended rather than skipped for time — see the QUESTIONS.md
entries below for the reasoning:

- **Stage 2 (`calibration`)** — not assigned to any B-checkpoint, and
  checkerboard-image processing has no synthetic-data path the way B4's
  kinematics core does. `CalibrationRecord`'s data shape is defined
  (B1) so B4 depends on it as data, never computes it.
- **`kinematics`'s CLI/orchestration wiring** — the pure computational core
  (B4) is complete and fully tested; only the file-reading stage runner
  (which needs stage 7's pose output format) is deferred, for the same
  reason B7's stages are scaffold-only.

## 4. QUESTIONS.md summary, ordered by rework cost if the guess is wrong

Full detail, options considered, and reasoning for each is in
`QUESTIONS.md` at the repo root. Six entries, all resolved with the most
conservative interpretation available; none blocked a checkpoint.

**Low-medium rework:**

1. **`report-stage-cannot-group-by-animal`** (B5) — `TrialSummaryRow`/
   `KinematicsLongRow` carry `trial_uid` but not `animal_id`/`project_name`,
   so the report stage can only group by `primary_keypoint` and produce
   overall summaries, not per-animal breakdowns, without either parsing
   `trial_uid` (fragile — its component fields can themselves contain
   underscores) or reading the manifest (outside stage 9's declared
   inputs). If per-animal grouping turns out to matter, the fix is adding
   `animal_id`/`project_name` columns to `TrialSummaryRow` itself.
2. **`trial-state-machine-predicate-stop-auto-flag`** (A3) — a future
   pose-driven `TrialStopCondition` firing doesn't get its own `auto_flags`
   entry distinct from `suspiciously_short`, since inventing that
   vocabulary now (before any real predicate exists) risked guessing wrong
   about what a real one would need to express.

**Low rework:**

3. **`trial-state-machine-min-duration-vs-predicate`** (A3) — the
   min-duration swallow guard applies uniformly to manual and
   predicate-triggered stops. Has zero effect on the current PDCT paradigm
   (today's `KeypressStopCondition` never self-triggers), so this is inert
   until a real pose-driven paradigm exists.
4. **`stage-2-calibration-has-no-checkpoint`** (B1) — see section 3 above.
5. **`qc-nominal-fps`** (B3) — added `qc.nominal_fps` as its own config key
   rather than reusing `analysis.fps`, which is explicitly about
   downsampling and would have wrongly coupled two concepts invariant 12
   says must stay decoupled.
6. **`kinematics-cli-stage-not-wired`** (B6) — see section 3 above.

## 5. Things I believe are wrong, contradictory, or underspecified

**Stage 2 (`calibration`) has no home in the checkpoint list.** Every other
stage in analysis/CLAUDE.md's "Stage contracts" table maps to a checkpoint
(0→B2, 1→B3, 3/5/6/7→B7, 8→B4, 9→B5) or is explicitly manual (4, labeling).
Stage 2 is the one gap, and it's not cosmetic: stage 8 (kinematics, B4)
lists "undistort coordinates" as an explicit pipeline step and needs a real
camera matrix + distortion coefficients to do it. I don't think this was
intentional — it reads like an off-by-one in the checkpoint table rather
than a deliberate scope decision, since nothing in the "Out of scope"
section mentions calibration the way it explicitly calls out Anipose/3D
triangulation as future work.

**B4 (kinematics) is checkpointed before B7 (infer, stage 7), but
kinematics structurally depends on stage 7's pose output to run as
anything other than pure functions.** This isn't a problem for B4 itself —
its checkpoint description is explicitly scoped to "the pure pipeline as
testable functions," which is exactly what I built and tested against
synthetic ground truth. But it becomes a real gap at B6 ("Per-stage
commands"): there is no point in the prescribed build order where a
`python -m pipeline kinematics` command could have real (or even
placeholder) input data to read, since B7 — the stage that would produce
that data — comes *after* B6. If the intent is for every stage listed
under "Commands" to eventually be a working CLI command, the dependency
direction between B4/B6/B7 is worth revisiting; if the intent is that
`kinematics`'s CLI wiring is understood to ride along with B7's eventual
real implementation, that's not stated anywhere I could find.

**The QC "fps deviation" threshold has no paired nominal value.**
"Config keys" lists "fps deviation" under QC thresholds, but the nominal
fps to measure deviation *from* isn't listed anywhere, and the one
existing fps-shaped key (`analysis.fps`) is explicitly about a different
concept (post-hoc downsampling, invariant 12). This is a small, mechanical
gap — I filled it with `qc.nominal_fps` — but it's the kind of thing that
would have silently produced a wrong QC gate (coupling downsampling to
capture-rate QC) if I'd taken the more obvious-looking shortcut of reusing
`analysis.fps`.

**Stage 9 (`report`)'s declared input contract is in tension with what
"group-level aggregation" implies.** "Reads only trial_summary.parquet and
kinematics_long.parquet" is a clean, testable contract, but neither file
carries `animal_id` or `project_name` — so "group-level" in practice means
"grouped by keypoint," not by animal, unless the contract is loosened or
those fields are added to `TrialSummaryRow`. Neither CLAUDE.md nor the
checkpoint table flags this; I only found it by actually building the
stage and discovering there was nothing to group by.

**Minor, no rework implied:** `overnight-prompt.md` says to save itself as
`.claude/overnight-prompt.md`, but it was provided at the repo root — I
left it there since moving it wasn't asked and has no functional effect on
the build. Also worth surfacing since I have read both CLAUDE.md files more
carefully than anyone: acquisition/CLAUDE.md's "Project structure" names
the camera/capture-internals package `acquisition/`, which — once nested
inside this monorepo's own `acquisition/` app directory — reads as
`acquisition/acquisition/camera_backend.py` etc. Not a bug (Python has no
trouble with it, and I kept it exactly as specified rather than guessing at
a rename), but it's a naming collision that likely wasn't anticipated when
that project-structure block was written for what was probably meant to be
a standalone, single-purpose repo.

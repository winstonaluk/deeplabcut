# Overnight build — PDCT acquisition + analysis

Save as `.claude/overnight-prompt.md` at the monorepo root.

Invoke with:

```bash
claude -p "$(cat .claude/overnight-prompt.md)" \
  --max-turns 250 --output-format json > ~/logs/overnight.json 2>&1
```

---

## Repository layout

You are working in a monorepo containing two independent applications plus a
shared schema package:

```
./
├── CLAUDE.md                  root context (read first)
├── QUESTIONS.md               you append here; create if absent
├── shared/
│   └── schema/                the contract between the two apps
├── acquisition/
│   ├── CLAUDE.md              acquisition rules + checkpoints A0–A9
│   └── ...
└── analysis/
    ├── CLAUDE.md              analysis rules + checkpoints B1–B7
    └── ...
```

**Read `acquisition/CLAUDE.md` and `analysis/CLAUDE.md` in full before writing
anything.** They contain hard invariants, scope boundaries, and the checkpoint
definitions this run is organised around. Everything below assumes them.

Keep all files for each app inside its own subdirectory. The only shared code is
`shared/schema/`.

## This is an unattended run

I am asleep. I cannot answer questions. This changes how you must behave:

- **Never guess on an ambiguity you would normally ask about.** Append it to
  `QUESTIONS.md` — one entry per question, stating the file, the decision you
  faced, the options, which you chose, and why. Implement the **most conservative**
  interpretation, mark it `# TODO(QUESTIONS.md): <short ref>` in code, and continue.
- **Do not relax an invariant to make something work.** If an invariant appears to
  conflict with a requirement, implement the invariant, record the conflict in
  `QUESTIONS.md`, and continue.
- **Do not expand scope.** Both CLAUDE.md files have explicit "out of scope"
  sections. Do not build anything listed there, however small it seems.
- **Never install system-level software, modify git history, or force-push.**

## Execution order

Strictly sequential. Do not skip ahead; later checkpoints depend on earlier ones.

```
A0  →  A1  →  A2  →  A3  →  A4  →  A5  →  A6  →  A7  →  A8  →  A9(scaffold)
    →  B1  →  B2  →  B3  →  B4  →  B5  →  B6  →  B7(scaffold)
```

Acquisition comes first because data must be collected before it can be analysed.
If you run out of turns, a complete acquisition app and a partial analysis app is
a much better outcome than two half-built apps.

## Checkpoint protocol

For each checkpoint, in this order:

1. **State the checkpoint ID and its "done when" criterion** before starting.
2. Implement it.
3. Write or update its tests.
4. Run `pytest` in the relevant subdirectory.
5. If tests pass → commit as `checkpoint <ID>: <name>`.
6. If tests fail and you cannot fix them **within this checkpoint's scope** →
   commit the work anyway as `checkpoint <ID>: <name> (tests failing)`, write the
   failure and your diagnosis to `QUESTIONS.md`, and move to the next checkpoint.
   Do not stall, and do not delete or weaken a test to make it pass.
7. Never leave uncommitted work at a checkpoint boundary.

**A checkpoint is not complete until its tests pass or its failure is recorded.**

## A0 comes first and matters most

`shared/schema/` is the contract between the two applications: acquisition writes
`session_metadata.json`, `trials.csv`, and timestamp sidecars; analysis stage 0
reads them as the spine of its manifest.

Define these schemas **once**, in one place, with a `schema_version`, and have both
sides import them. Do not let either app define its own copy — divergence here
surfaces as a crash on real data months from now.

Include round-trip tests: acquisition writes a synthetic session, analysis reads
it and produces a manifest. That test is the contract's proof and should exist
from A0 onward.

## Testing requirements

Both apps must be fully testable **with no hardware, no GPU, no real data, and no
network**. This is not a nice-to-have — it is what makes this run verifiable.

- Acquisition: everything runs against `MockCamera`. Never require a camera.
- Analysis: everything runs against **synthetic pose arrays with known ground
  truth**. A fabricated constant-velocity descent must recover the correct
  velocity; a fabricated gap longer than `max_gap_frames` must stay NaN.
- No test may require DLC, PySpin, CUDA, or a network mount.

Prefer a smaller number of tests that genuinely verify behaviour over broad
coverage of trivial getters. The bounded-queue drop behaviour, the trial state
machine guards, and the kinematics ground-truth recovery are the three places
where tests earn their keep.

## Things that will tempt you — do not do them

These are the specific drift paths I expect. Each is an invariant violation:

- Making the frame queue **unbounded** because bounded queues are fiddly. It must
  be bounded and must drop-and-count on overflow.
- Writing **PySpin code** before the mock path is complete and tested.
- Having the QC gate **drop rows** instead of marking `included=False`.
- **Undistorting video** instead of undistorting coordinates post-hoc.
- Hardcoding thresholds, durations, or keybindings instead of reading config.
- Welding the trial **stop condition** into the Qt keypress handler instead of
  keeping it a pluggable predicate.
- Adding **stylesheets or theming** to the GUI. Stock Qt widgets only.
- **Silently bridging** long interpolation gaps in kinematics.

## When you finish or run low on turns

Write `OVERNIGHT_REPORT.md` at the repo root containing:

1. Checkpoints completed, with commit hashes
2. Checkpoints attempted but failing, with the specific failure
3. Checkpoints not reached
4. A summary of every `QUESTIONS.md` entry, ordered by how much rework a wrong
   guess would cause
5. Anything you believe is wrong, contradictory, or underspecified in either
   CLAUDE.md — you have read them more carefully than anyone, so say so plainly

Then stop. Do not begin a checkpoint you cannot finish.

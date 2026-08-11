# CLAUDE.md — PDCT analysis pipeline

Project context for the scriptable DeepLabCut analysis pipeline. Auto-loaded each
session — treat everything here as standing rules unless I say otherwise in chat.

Companion repo: the acquisition GUI (separate project, has its own CLAUDE.md).
This repo has **no PySpin dependency** and never touches camera hardware.

---

## What this is

A config-driven, scriptable analysis pipeline that turns acquired PDCT video into
height-resolved descent kinematics. Replaces ad-hoc notebook workflows and the DLC
GUI, which are neither reproducible nor batchable.

**The pipeline's product is `y(t)` — a trustworthy, correctly-scaled vertical
position time series for the animal on the pole.** Descent time is a trivial query
against `y(t)`; the height-resolved velocity profile is the novel measurement and
cannot be obtained any other way. Design every stage to serve `y(t)` accuracy.

## Glossary

| Term | Meaning |
|---|---|
| **PDCT** | Pole Descent Cognitive Test. Rat placed atop a vertical pole, descends. |
| **VCA** | Visual Cliff Assay. Second paradigm, same pipeline. |
| **Trial** | One descent. 1–5 minutes for our rats. One video file. |
| **Session** | All trials for one animal on one day. |
| **View** | Camera position: `lateral_L`, `lateral_R`, `top_down`. Currently one camera. |
| **DLC** | DeepLabCut 3.0, **PyTorch engine** (not TensorFlow). |
| **SuperAnimal** | DLC's pretrained zero-shot models used as training init. |
| **Anipose** | Multi-camera 3D triangulation on DLC output. Future stage. |
| **CRSP** | Institutional network storage. **Storage only — no compute.** |
| **Pole landmarks** | Static keypoints on the apparatus, labelled alongside the animal. |
| **Trial UID** | Stable unique key for a trial+view. Primary join key everywhere. |

## Domain context

- Subjects are **rats**. Trials run **1–5 minutes**.
- **Acquisition is 30 fps** (camera capable of 60; fps is an acquisition config
  value). 33 ms temporal resolution — ample for minute-scale descents, marginal
  for limb-level kinematics. Do not assume 60 fps anywhere.
- **Descent duration and the velocity-by-height profile are the dependent
  variables.** The scientific hypothesis is that slowing concentrates near the
  pole top. Anything that distorts apparent velocity as a function of height is a
  first-order threat, not a cosmetic issue — this is why lens distortion
  correction is mandatory rather than optional.
- Rats **spiral around the pole** during descent. With a single lateral camera the
  animal is occluded behind the pole for a meaningful fraction of every trial.
  Single-camera kinematics are **provisional** until 3D triangulation exists.
- A rat occupies a substantial fraction of the pole's length. Snout, centroid, and
  tail base are separated along the height axis, so keypoint choice changes the
  shape of the velocity profile — it is not a constant offset.

## Hardware and environment

**Analysis PC:** RTX 5070 Ti — **Blackwell, sm_120**.

- Requires the PyTorch **`cu128`** index-URL wheel. PyTorch 2.6 has no Blackwell
  kernels at all and will fail or fall back silently.
- The CUDA version reported by `nvidia-smi` is the *driver ceiling*, not what
  PyTorch uses — PyTorch bundles its own runtime. Do not diagnose from `nvidia-smi`.
- DLC 3.0's `torch>=2.0.0` pin does not block upgrading.
- Verify with `torch.cuda.get_device_capability(0)` → expect `(12, 0)`.

**Storage:** CRSP is a network **archive only**. No jobs run there. One local GPU,
no cluster — inference is an overnight batch job, not an interactive step.

## Data tiering

Video is huge; everything derived from it is small. Inference is the **only** stage
that needs raw video.

| Tier | Location | Contents | Mutability |
|---|---|---|---|
| Archive | CRSP | Raw video, timestamp sidecars, session metadata | Write-once, read-only |
| Working cache | Analysis PC | Video for the batch currently being processed | Transient, deletable |
| Derived | CRSP + git | Manifest, pose `.h5`, kinematics, configs, reports | Versioned |

Inference loop: pull batch → infer → write pose → verify → delete local video.
Cache must be sized for one batch, never the whole corpus.

## Architecture invariants

Do not violate these. If a request seems to require breaking one, stop and ask.

1. **Raw video is immutable.** Never modify, re-encode, trim, or overwrite it.
2. **Undistort coordinates, never video.** Apply calibration to pose output
   post-hoc. Re-encoding video to undistort is lossy, slow, and destroys the
   archive's write-once property.
3. **QC marks, never deletes.** Excluded trials stay in the manifest with an
   `included` boolean and an `exclusion_reason`. Exclusions must be auditable and
   reversible.
4. **Every stage is idempotent and resumable.** Skip when outputs exist and input
   + config hashes match. A job that dies at trial 40 of 200 restarts skipping 39.
5. **Every artifact carries provenance.** Sidecar `.provenance.json` with input
   artifact hashes, config hash, code commit, DLC snapshot ID, stage version,
   timestamp.
6. **Config is the single source of truth.** No magic numbers in code. Thresholds,
   keypoint schemes, filter parameters, and rules all live in TOML.
7. **The descent onset/offset rule is named and versioned in config.** Changing it
   changes the config hash and regenerates downstream artifacts. It must be fixed
   before group comparisons are run.
8. **`primary_keypoint` is a config parameter**, never hardcoded. `y(t)` must
   regenerate for any labelled keypoint without re-labelling or re-training.
9. **Nothing downstream of inference requires CRSP or a GPU.** Kinematics, stats,
   and figures run on small derived files, offline, anywhere.
10. **All pose tables are view-tagged and long-format**, so 3D triangulation is an
    inserted stage rather than a rewrite. No 2D-only assumptions in schemas.
11. **Use the DLC Python API, never the DLC GUI**, except for manual labelling.
12. **Analysis frame rate is decoupled from acquisition frame rate.** Any temporal
    downsampling is an explicit, logged config choice.

## Stage contracts

Each stage: pure function of (inputs, config) → artifacts + provenance sidecar.

### 0 · `build_manifest`
- **In:** archive session directories
- **Reads:** `session_metadata.json`, `trials.csv` from each session
- **Out:** `manifest.parquet` — one row per **trial × view**
- **Key columns:** `trial_uid` (stable deterministic string), `animal_id`,
  `project_name`, `date`, `initials`, `view`, `trial_number`, `video_path`,
  `timestamps_path`, `duration_s`, `n_frames`, `dropped_frames`, `achieved_fps`,
  `flags`, `auto_flags`
- This manifest is the **spine**. Every later stage queries it rather than
  crawling the filesystem.

### 1 · `qc_gate`
- **In:** `manifest.parquet`
- **Out:** `manifest_qc.parquet` = manifest + `included` (bool) + `exclusion_reason`
- **Rules (all config thresholds):** experimenter `flags` non-empty → exclude ·
  `dropped_frames` rate above threshold → exclude · `duration_s` outside plausible
  range → exclude · `achieved_fps` deviating from nominal → exclude
- Never drops rows (invariant 3).

### 2 · `calibration`
- **In:** checkerboard image sets
- **Out:** `calibration/{camera_serial}_{epoch}.json` with camera matrix and
  distortion coefficients
- **Calibration epoch:** a calibration is valid until the camera is moved or
  refocused. Manifest rows map to an epoch by date range. A trial with no valid
  epoch is a QC failure, not a silent pass.
- Intrinsics only. **Pixel→mm scale is derived per-video from pole landmarks at
  the kinematics stage**, not here.
- Extrinsics for 3D triangulation come later.

### 3 · `extract_frames`
- **In:** `manifest_qc.parquet` (included rows only)
- **Sampling:** stratified across animal × date × session so no single animal or
  lighting condition dominates. Biased toward the descent phase.
- **Round 1:** motion/ROI prefilter, then k-means. Blind k-means wastes budget on
  uninformative and occluded frames.
- **Round 2 (after a first model exists):** DLC `extract_outlier_frames` with
  `uncertain` and `jump` modes.
- **Out:** `frames_manifest.csv` with `trial_uid`, `frame_index`,
  `extraction_method`, `extraction_round`, image path
- Frame provenance back to source trial is **mandatory** — a bad label must be
  traceable to its trial.

### 4 · `labeling` — manual
- DLC project directory, path referenced from config. Wrap DLC's structure; don't
  fight it.
- **Keypoint scheme lives in config as the single source of truth** and must
  include **static pole landmarks** (pole top, pole base, fixed fiducial).
- Label **snout, mid-back/centroid, and tail base** so `primary_keypoint` can be
  compared without re-labelling.
- Do not trim a SuperAnimal keypoint set down to a subset — fine-tuning to a
  reduced subset behaves unexpectedly. Use the full set or a custom scheme.

### 5 · `train`
- SuperAnimal initialisation. **Subjects are rats:** SuperAnimal-Quadruped is the
  expected init for lateral views. SuperAnimal-TopViewMouse is mouse-trained —
  decide top-down init by zero-shot comparison, not assumption.
- **Out:** snapshot + `training_log.json` (config, seed, train/test split, snapshot ID)

### 6 · `evaluate`
- Train/test pixel error overall and **per keypoint** (pole landmarks should be
  near-zero; a high error there means the coordinate frame is unreliable).
- `pcutoff` sweep.
- Manual validation on randomly sampled held-out frames (RpiBeh methodology).
- **Out:** `evaluation_report.json` + figures
- **Gate:** batch inference must not run if error exceeds the config threshold.

### 7 · `infer`
- **In:** `manifest_qc.parquet` (included only) + trained snapshot
- Pull video from archive → local cache → DLC `analyze_videos` → write pose `.h5`
  → verify → delete local copy
- **Resumable:** skip trials whose pose output exists with matching snapshot ID
  and config hash
- **Out:** pose `.h5` per trial + `pose_index.parquet` mapping `trial_uid` → pose path
- Log per-trial wall-clock throughput; this is the pipeline bottleneck.

### 8 · `kinematics`
- **In:** pose `.h5`, calibration, `manifest_qc.parquet`
- **Order matters:** likelihood filter → gap interpolation (config `max_gap_frames`;
  longer gaps stay NaN, never silently bridged) → temporal smoothing (median or
  Savitzky-Golay, config) → **undistort coordinates** → derive pole coordinate
  frame from pole landmarks → normalise height to fraction of pole length → scale
  to mm via known pole length
- **Pole landmark drift check:** if landmarks move mid-trial beyond threshold, the
  camera was bumped. Flag the trial.
- **Derive:** `y(t)`, `v(t)`, descent onset/offset per the configured named rule,
  descent duration, velocity binned by height, occlusion/visibility fraction
- **Out:** `kinematics_long.parquet` (per frame × trial × view × keypoint) +
  `trial_summary.parquet` (one row per trial)

### 9 · `report`
- Group-level aggregation, statistics, figures. Reads only `trial_summary.parquet`
  and `kinematics_long.parquet`.
- No GPU, no network storage, no video.

### Future · `triangulate`
- Anipose 3D from multi-view 2D pose. Inserts between stages 7 and 8. Design
  schemas so this is an insert, not a rewrite. **Do not build yet.**

## Config keys

Camera/view list · archive root · local cache root · derived root · DLC project
path · keypoint scheme (incl. pole landmarks) · `primary_keypoint` · SuperAnimal
init per view · QC thresholds (dropped-frame rate, duration range, fps deviation)
· pole length mm · likelihood cutoff · `max_gap_frames` · smoothing method and
window · descent rule name + parameters · evaluation error gate · analysis fps
(if downsampling) · batch size for inference · calibration epoch table

## Out of scope — do not build

- Anipose / 3D triangulation (define schema seam only)
- Any camera or acquisition code (that's the companion repo)
- A GUI. This pipeline is CLI + config. Labelling uses DLC's or napari's existing UI.
- Real-time or DLC-Live inference
- Re-encoding, trimming, or otherwise mutating archived video

## Commands

```bash
python -m pipeline manifest        # stage 0
python -m pipeline qc              # stage 1
python -m pipeline extract         # stage 3
python -m pipeline train           # stage 5
python -m pipeline evaluate        # stage 6
python -m pipeline infer           # stage 7, resumable batch
python -m pipeline kinematics      # stage 8
python -m pipeline report          # stage 9

python -m pipeline run --from manifest --to kinematics   # chain, skipping cached
python -m pipeline status                                # what's stale and why

pytest
```

Every command takes `--config path.toml` and `--dry-run`.

## Conventions

- Type hints throughout; dataclasses for artifact schemas
- **Parquet for all tabular artifacts**; CSV only where a human or external tool
  must read it
- Long/tidy format over wide — one row per observation, view-tagged
- Structured logging to a per-run log file, not bare `print`
- Tests run on **synthetic pose data**, no GPU and no real video required
- Stage functions are importable and unit-testable independent of the CLI

## Cross-repo contract

Stage 0 reads `session_metadata.json` and `trials.csv` produced by the acquisition
repo. These are a **contract, not an incidental format**.

- Schemas live in `shared/schema/` and are imported here, never redefined locally.
- Validate `schema_version` on read and fail loudly on mismatch — never coerce.
- Never change a field name, type, or meaning without updating `shared/schema/`
  and the acquisition writer in the same commit.

## Unattended runs

When running headless (`claude -p`) I cannot answer questions. Therefore:

- **Never guess on an ambiguity you would normally ask about.** Append it to
  `QUESTIONS.md` at repo root with the affected file and line, implement the most
  conservative interpretation, mark it `# TODO(QUESTIONS.md): <ref>` in code, and
  continue. Scientific-definition questions (descent rule parameters, QC
  thresholds, filter windows) go here rather than being invented.
- **A checkpoint is not complete until `pytest` passes.** If tests fail and can't
  be fixed within scope, commit, record in `QUESTIONS.md`, and move on.
- **Commit at every checkpoint** with message `checkpoint B<n>: <name>`.
- **Never skip ahead.** Checkpoints are ordered by dependency.
- Do not relax an invariant to make a test pass. Record the conflict instead.

## Checkpoints

`A0` (shared schema, defined in the acquisition repo's checkpoint list) must exist
before `B2`.

**Buildable unattended** — pure functions, synthetic fixtures, no GPU or real data:

| ID | Name | Done when |
|---|---|---|
| B1 | Skeleton + provenance | Package layout; config schema with every key and default; hashing utilities (input artifact hash, config hash, code commit); `.provenance.json` writer/reader; stage-contract dataclasses with full type signatures. Tests importable. |
| B2 | Stage 0 manifest | Scans session dirs, validates against `shared/schema/`, emits `manifest.parquet` with `trial_uid` and all key columns. Tests run against a synthetic session tree fixture. |
| B3 | Stage 1 QC gate | All config-driven rules; marks `included` + `exclusion_reason`; **never drops rows**. Tests cover each rule independently. |
| B4 | Stage 8 kinematics core | The pure pipeline as testable functions: likelihood filter → gap interpolation (`max_gap_frames`, long gaps stay NaN) → smoothing → coordinate undistortion → pole-landmark coordinate frame → mm scaling → descent rule → `y(t)`, `v(t)`, velocity-by-height. **Tests use synthetic pose arrays with known ground truth** — a fabricated constant-velocity descent must recover the right velocity. |
| B5 | Stage 9 report | Aggregation and table generation from `trial_summary.parquet`. Figures optional. |
| B6 | CLI + orchestration | Per-stage commands, `run --from --to`, `status` showing what's stale and why, `--config`, `--dry-run`. Idempotency and resumability tested with fake artifacts. |

**Not buildable unattended** — require DLC installed, a trained model, or real
data. Scaffold the interfaces and write a plan; do not fake implementations:

| ID | Name | Note |
|---|---|---|
| B7 | Stages 3, 5, 6, 7 | Frame extraction, train, evaluate, infer. Define signatures and the resumability/caching logic, which *is* testable with fake artifacts. Leave DLC calls as thin wrappers. |

## Open decisions — do not resolve unattended

These are experimental-design choices. Record them in `QUESTIONS.md` if they block
progress; never pick a value and proceed silently.

- Zero-shot SuperAnimal comparison (Quadruped vs TopViewMouse on ~20 rat frames)
  decides the training init — must run before labelling budget is spent
- `primary_keypoint` comparison on pilot data (visibility fraction, jitter, mean
  likelihood), criteria fixed **before** looking at group differences
- Descent onset/offset rule parameters
- QC thresholds and filter window sizes
- PyTorch `cu128` verification on the 5070 Ti (needs the physical machine)

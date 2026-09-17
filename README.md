# PDCT behavioral acquisition and analysis

Software for the Pole Descent Cognitive Test (PDCT): a rat is placed atop a
vertical pole and descends. Video is captured with metadata bound at write time,
then analysed offline with DeepLabCut.

```
./
├── shared/schema/    the contract: session_metadata.json, trials.csv, sidecars
├── acquisition/      capture backend + web UI, runs at the rig
└── analysis/         DeepLabCut pipeline, runs on a GPU workstation
```

The two applications share no code except `shared/schema/`, run on different
machines, and **need separate Python environments** — see below.

Standing rules, domain context and architecture invariants live in
`acquisition/CLAUDE.md` and `analysis/CLAUDE.md`. Read those before changing
either app. This file is only about getting it running.

## Why two environments

They cannot share an interpreter:

| | Python | Pinned by |
|---|---|---|
| `acquisition` | **3.10 exactly** | The `cp310` PySpin wheel. Teledyne builds PySpin per Python version. |
| `analysis` | **3.11+** (target 3.12) | `pipeline/config.py` imports `tomllib`, stdlib only from 3.11. |

They also disagree on numpy: acquisition pins `numpy<2` because PySpin cannot
load 2.x, while analysis has no ceiling. In a shared environment acquisition's
bound silently caps analysis at numpy 1.x, and nothing in `analysis/` records
that it is being capped.

> `analysis/` is being split into its own repository (`pdct-analysis`) for this
> reason. Until then, treat the two subdirectories as separate projects that
> happen to share a checkout.

## Acquisition setup

Target hardware is an **NVIDIA Jetson Orin Nano Super 8 GB** (JetPack 6.x,
Ubuntu 22.04, aarch64). It also runs on any machine for development, against the
mock camera.

```bash
conda create -n acquire python=3.10
conda activate acquire

pip install -r acquisition/requirements.txt
pip install -e shared/          # see "The shared schema" below — do not skip
```

**FFmpeg must be on `PATH`.** It is an external binary, not a pip package. The
app treats a missing FFmpeg as a blocking preflight failure, and FFmpeg-dependent
tests skip with a named reason rather than failing.

For real hardware, additionally:

1. **Spinnaker SDK** from Teledyne — vendor installer, not pip. On the Jetson
   this is the **ARM64/Ubuntu** package, a *separate download* from the x86-64
   one with its own version and Python matrix.
2. **The matching PySpin wheel** from that SDK. Wheels are per-Python-version and
   not interchangeable.
3. **Raise the USB buffer** (Linux only). The 16 MB default is far too small for
   USB3 machine vision and shows up as incomplete frames, not a clear error:
   ```bash
   sudo sh -c 'echo 1000 > /sys/module/usbcore/parameters/usbfs_memory_mb'
   ```
   Make it persistent via `usbcore.usbfs_memory_mb=1000` on the kernel cmdline.
4. **Camera configuration is done in SpinView**, not in this app, and saved to
   `UserSet1`. The app loads that user set, verifies it against the
   `[camera_verify]` table in `acquisition/config.toml`, and **refuses to record
   if they disagree** — it never writes a node to make a check pass. See
   invariant 7.

### Run it

```bash
cd acquisition

python -m app --mock --headless   # full session, synthetic frames, no hardware
python -m app --headless          # full session, real cameras
python -m app                     # API + web UI (checkpoint A14; not built yet)
```

Sessions land under `storage.session_root` in `config.toml` (`./sessions` by
default, relative to the working directory). Override with `--session-root`.

Every threshold, path, reason code and encoder setting comes from
`acquisition/config.toml`. Nothing is a literal in code (invariant 9).

## Analysis setup

Runs on the GPU workstation (RTX 5070 Ti, Blackwell/sm_120), not at the rig.

```bash
conda create -n analysis python=3.12
conda activate analysis

pip install -r analysis/requirements.txt
pip install -e shared/
```

DeepLabCut and PyTorch are **deliberately excluded** from
`analysis/requirements.txt`. On Blackwell, torch must come from the `cu128`
index-URL wheel — a plain `pip install torch` gets a build with no Blackwell
kernels, which fails or silently falls back. See `analysis/CLAUDE.md`.

```bash
cd analysis
python -m pipeline status                 # what has run
python -m pipeline manifest               # one stage
python -m pipeline run --from manifest --to qc
```

## The shared schema

`shared/schema/` defines the three artifacts that cross between the apps:
`session_metadata.json`, `trials.csv`, and the per-trial timestamp sidecars.
Both apps import it as `schema` and **never redefine it locally**. It is pure
stdlib with no third-party dependencies, so it installs into either environment.

**Install it as editable in every environment** (`pip install -e shared/`).
Neither app currently declares it as a dependency, so nothing will tell you it is
missing until an import fails — and if the install points at a *moved* directory,
`import schema` breaks and the entire test suite stops collecting with no
indication why. This has happened. If tests fail with
`ModuleNotFoundError: No module named 'schema'`, re-run the editable install:

```bash
python -c "import schema; print(schema.__file__)"   # should be inside this checkout
```

All three artifacts carry a `schema_version`. Readers **fail loudly** on a
mismatch and never coerce. Changing a field is a coordinated version bump across
both apps — the protocol is in each app's CLAUDE.md under "Cross-repo contract".

## Tests

Each package has its own suite and its own environment.

```bash
cd acquisition && pytest    # 143 passed, 6 deselected
cd shared       && pytest   # 6 passed
cd analysis     && pytest   # needs the analysis environment
```

No test may require a camera, PySpin, CUDA, a trained DLC model, or a network
mount. Hardware tests are marked `hardware` and deselected by default; run them
at the rig with `pytest -m hardware`. Tests that spawn FFmpeg are marked
`requires_ffmpeg` and skip by name when it is absent.

## Knowledge graph

The repo carries a queryable graph of itself in `graphify-out/`. For questions
about structure, prefer it over grepping:

```bash
graphify query "how does a frame get from the camera to disk"
graphify path "SpinnakerCamera" "WriterThread"
graphify update .        # after changing code — run from the repo root
```

Run `graphify update` from the **repo root**. Running it from inside a
subdirectory rescopes the graph to that subtree and drops everything else.

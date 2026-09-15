# SpinnakerCamera.start_streaming

> 8 nodes

## Key Concepts

- **SpinnakerCamera.start_streaming()** (3 connections) — `acquisition/acquisition/SPINNAKER_PLAN.md`
- **Invariant 3 — Capture Never Blocks** (3 connections) — `acquisition/CLAUDE.md`
- **720 × 540 Sensor Correction (not 1280 × 720)** (2 connections) — `acquisition/acquisition/HARDWARE.md`
- **Pre-Roll Ring Buffer (2 s)** (2 connections) — `acquisition/CLAUDE.md`
- **Original Acquisition GUI Prompt (v3)** (2 connections) — `claude_code_prompt_behavior_acquisition_gui.md`
- **Copy GetNDArray() Before the Frame Escapes** (2 connections) — `acquisition/acquisition/SPINNAKER_PLAN.md`
- **Incomplete Frames Counted Separately From Dropped Frames** (2 connections) — `acquisition/acquisition/SPINNAKER_PLAN.md`
- **Decoupled Capture/Encode/Display Threading Model** (1 connections) — `claude_code_prompt_behavior_acquisition_gui.md`

## Relationships

- [Stage 1 · qc_gate](Stage_1_·_qc_gate.md) (2 shared connections)
- [Monorepo Layout (shared/schema + acquisition + analysis)](Monorepo_Layout_shared-schema_+_acquisition_+_analysis.md) (1 shared connections)

## Source Files

- `acquisition/CLAUDE.md`
- `acquisition/acquisition/HARDWARE.md`
- `acquisition/acquisition/SPINNAKER_PLAN.md`
- `claude_code_prompt_behavior_acquisition_gui.md`

## Audit Trail

- EXTRACTED: 6 (60%)
- INFERRED: 4 (40%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
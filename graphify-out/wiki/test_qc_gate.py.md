# test_qc_gate.py

> 26 nodes

## Key Concepts

- **test_qc_gate.py** (28 connections) — `analysis/tests/test_qc_gate.py`
- **qc_gate.py** (19 connections) — `analysis/pipeline/stages/qc_gate.py`
- **evaluate_trial()** (18 connections) — `analysis/pipeline/stages/qc_gate.py`
- **_row()** (16 connections) — `analysis/tests/test_qc_gate.py`
- **write_qc_gate()** (12 connections) — `analysis/pipeline/stages/qc_gate.py`
- **qc_gate()** (10 connections) — `analysis/pipeline/stages/qc_gate.py`
- **QCConfig** (9 connections) — `analysis/pipeline/config.py`
- **qc_rows_to_dataframe()** (4 connections) — `analysis/pipeline/stages/qc_gate.py`
- **test_qc_gate_never_drops_rows()** (4 connections) — `analysis/tests/test_qc_gate.py`
- **test_auto_flags_alone_do_not_exclude()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_clean_trial_is_included()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_dropped_frame_rate_above_threshold_excludes()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_dropped_frame_rate_at_threshold_is_included()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_duration_above_max_excludes()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_duration_below_min_excludes()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_duration_within_range_is_included()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_experimenter_flags_exclude()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_fps_deviation_above_threshold_excludes()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_fps_within_deviation_threshold_is_included()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_multiple_failing_rules_all_appear_in_exclusion_reason()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **test_zero_frames_counts_as_full_drop_rate()** (3 connections) — `analysis/tests/test_qc_gate.py`
- **DataFrame** (2 connections)
- **Path** (1 connections)
- **Stage 1: qc_gate. All rules are config-driven thresholds (invariant 6). Never…** (1 connections) — `analysis/pipeline/stages/qc_gate.py`
- **Returns (included, exclusion_reason). Every failing rule is recorded in…** (1 connections) — `analysis/pipeline/stages/qc_gate.py`
- *... and 1 more nodes in this community*

## Relationships

- [Provenance](Provenance.md) (14 shared connections)
- [manifest.py](manifest.py.md) (10 shared connections)
- [test_stages_b7_scaffold.py](test_stages_b7_scaffold.py.md) (5 shared connections)
- [pipeline/config.py](pipeline-config.py.md) (4 shared connections)
- [orchestration.py](orchestration.py.md) (3 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (2 shared connections)

## Source Files

- `analysis/pipeline/config.py`
- `analysis/pipeline/stages/qc_gate.py`
- `analysis/tests/test_qc_gate.py`

## Audit Trail

- EXTRACTED: 97 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
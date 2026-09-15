# test_orchestration.py

> 26 nodes

## Key Concepts

- **test_orchestration.py** (42 connections) — `analysis/tests/test_orchestration.py`
- **_config()** (23 connections) — `analysis/tests/test_orchestration.py`
- **_fake_chain()** (16 connections) — `analysis/tests/test_orchestration.py`
- **run_pipeline()** (13 connections) — `analysis/pipeline/orchestration.py`
- **test_real_report_stage_via_orchestration_with_fake_upstream_artifacts()** (8 connections) — `analysis/tests/test_orchestration.py`
- **test_real_manifest_then_qc_via_orchestration()** (6 connections) — `analysis/tests/test_orchestration.py`
- **_write_synthetic_session()** (5 connections) — `analysis/tests/test_orchestration.py`
- **test_downstream_stage_goes_stale_when_upstream_output_changes()** (4 connections) — `analysis/tests/test_orchestration.py`
- **test_run_pipeline_chains_and_skips_up_to_date()** (4 connections) — `analysis/tests/test_orchestration.py`
- **test_run_pipeline_dry_run_reports_without_running()** (4 connections) — `analysis/tests/test_orchestration.py`
- **test_run_pipeline_rejects_reversed_range()** (4 connections) — `analysis/tests/test_orchestration.py`
- **test_run_pipeline_rejects_unknown_stage_name()** (4 connections) — `analysis/tests/test_orchestration.py`
- **test_unwired_stage_run_raises()** (4 connections) — `analysis/tests/test_orchestration.py`
- **test_dry_run_never_calls_run_fn_or_writes_artifact()** (3 connections) — `analysis/tests/test_orchestration.py`
- **test_stage_goes_stale_when_config_changes()** (3 connections) — `analysis/tests/test_orchestration.py`
- **test_stage_run_is_a_noop_when_already_up_to_date()** (3 connections) — `analysis/tests/test_orchestration.py`
- **test_stage_run_then_status_up_to_date()** (3 connections) — `analysis/tests/test_orchestration.py`
- **test_stage_status_missing_before_first_run()** (3 connections) — `analysis/tests/test_orchestration.py`
- **test_status_report_lists_every_stage_in_order()** (3 connections) — `analysis/tests/test_orchestration.py`
- **test_unwired_stage_reports_not_implemented()** (3 connections) — `analysis/tests/test_orchestration.py`
- **Path** (3 connections)
- **parametrize** (2 connections)
- **Runs stages from_stage..to_stage inclusive, in registry order, skipping any…** (1 connections) — `analysis/pipeline/orchestration.py`
- **Checkpoint B6: per-stage commands, run --from --to, status, --dry-run.…** (1 connections) — `analysis/tests/test_orchestration.py`
- **kinematics isn't wired (see QUESTIONS.md), so this places fake…** (1 connections) — `analysis/tests/test_orchestration.py`
- *... and 1 more nodes in this community*

## Relationships

- [orchestration.py](orchestration.py.md) (12 shared connections)
- [pipeline/config.py](pipeline-config.py.md) (9 shared connections)
- [Provenance](Provenance.md) (8 shared connections)
- [test_report.py](test_report.py.md) (4 shared connections)
- [manifest.py](manifest.py.md) (3 shared connections)
- [test_qc_gate.py](test_qc_gate.py.md) (2 shared connections)
- [test_kinematics.py](test_kinematics.py.md) (2 shared connections)
- [TrialRecord](TrialRecord.md) (2 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (2 shared connections)
- [test_roundtrip.py](test_roundtrip.py.md) (1 shared connections)
- [CameraInfo](CameraInfo.md) (1 shared connections)
- [test_stages_b7_scaffold.py](test_stages_b7_scaffold.py.md) (1 shared connections)

## Source Files

- `analysis/pipeline/orchestration.py`
- `analysis/tests/test_orchestration.py`

## Audit Trail

- EXTRACTED: 103 (96%)
- INFERRED: 4 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
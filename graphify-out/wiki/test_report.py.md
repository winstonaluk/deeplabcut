# test_report.py

> 25 nodes

## Key Concepts

- **test_report.py** (22 connections) — `analysis/tests/test_report.py`
- **KinematicsLongRow** (11 connections) — `analysis/pipeline/contracts.py`
- **TrialSummaryRow** (11 connections) — `analysis/pipeline/contracts.py`
- **aggregate_overall()** (8 connections) — `analysis/pipeline/stages/report.py`
- **_summary_df()** (8 connections) — `analysis/tests/test_report.py`
- **test_write_report_produces_parquet_tables_and_provenance()** (8 connections) — `analysis/tests/test_report.py`
- **aggregate_velocity_by_height()** (7 connections) — `analysis/pipeline/stages/report.py`
- **_summary_row()** (7 connections) — `analysis/tests/test_report.py`
- **aggregate_by_keypoint()** (6 connections) — `analysis/pipeline/stages/report.py`
- **_long_df()** (6 connections) — `analysis/tests/test_report.py`
- **DataFrame** (6 connections)
- **_long_row()** (5 connections) — `analysis/tests/test_report.py`
- **_descent_summary_stats()** (4 connections) — `analysis/pipeline/stages/report.py`
- **test_aggregate_by_keypoint_groups_correctly()** (4 connections) — `analysis/tests/test_report.py`
- **test_aggregate_overall_basic_stats()** (4 connections) — `analysis/tests/test_report.py`
- **test_aggregate_overall_counts_drift_flagged_trials()** (4 connections) — `analysis/tests/test_report.py`
- **test_aggregate_overall_handles_undetected_descent()** (4 connections) — `analysis/tests/test_report.py`
- **test_aggregate_velocity_by_height_bins_across_trials()** (4 connections) — `analysis/tests/test_report.py`
- **test_aggregate_velocity_by_height_excludes_nan_rows()** (4 connections) — `analysis/tests/test_report.py`
- **test_trial_summary_row_allows_none_for_undetected_descent()** (2 connections) — `analysis/tests/test_contracts.py`
- **DataFrame** (2 connections)
- **Stage 8 (kinematics, B4) output: kinematics_long.parquet -- one row per frame x…** (1 connections) — `analysis/pipeline/contracts.py`
- **Stage 8 (kinematics, B4) output: trial_summary.parquet -- one row per trial.** (1 connections) — `analysis/pipeline/contracts.py`
- **Pools velocity samples across every trial/frame present, binned by…** (1 connections) — `analysis/pipeline/stages/report.py`
- **Checkpoint B5: stage 9 report -- aggregation and table generation from…** (1 connections) — `analysis/tests/test_report.py`

## Relationships

- [Provenance](Provenance.md) (16 shared connections)
- [test_stages_b7_scaffold.py](test_stages_b7_scaffold.py.md) (7 shared connections)
- [test_kinematics.py](test_kinematics.py.md) (4 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (4 shared connections)

## Source Files

- `analysis/pipeline/contracts.py`
- `analysis/pipeline/stages/report.py`
- `analysis/tests/test_contracts.py`
- `analysis/tests/test_report.py`

## Audit Trail

- EXTRACTED: 83 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
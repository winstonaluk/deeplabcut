# manifest.py

> 34 nodes

## Key Concepts

- **manifest.py** (23 connections) — `analysis/pipeline/stages/manifest.py`
- **test_manifest.py** (21 connections) — `analysis/tests/test_manifest.py`
- **build_manifest()** (14 connections) — `analysis/pipeline/stages/manifest.py`
- **_write_session()** (14 connections) — `analysis/tests/test_manifest.py`
- **ManifestRow** (13 connections) — `analysis/pipeline/contracts.py`
- **write_manifest()** (12 connections) — `analysis/pipeline/stages/manifest.py`
- **compute_manifest_input_hashes()** (10 connections) — `analysis/pipeline/stages/manifest.py`
- **scan_session_directory()** (10 connections) — `analysis/pipeline/stages/manifest.py`
- **_trial()** (9 connections) — `analysis/tests/test_manifest.py`
- **manifest_rows_to_dataframe()** (8 connections) — `analysis/pipeline/stages/manifest.py`
- **dataframe_to_manifest_rows()** (7 connections) — `analysis/pipeline/stages/manifest.py`
- **trial_uid()** (7 connections) — `analysis/pipeline/stages/manifest.py`
- **test_write_manifest_produces_parquet_and_provenance()** (7 connections) — `analysis/tests/test_manifest.py`
- **test_write_manifest_provenance_changes_when_a_session_changes()** (6 connections) — `analysis/tests/test_manifest.py`
- **test_build_manifest_preserves_flags_through_dataframe_round_trip()** (5 connections) — `analysis/tests/test_manifest.py`
- **Path** (5 connections)
- **_find_trial_file()** (4 connections) — `analysis/pipeline/stages/manifest.py`
- **test_build_manifest_multi_view_produces_one_row_per_trial_per_view()** (4 connections) — `analysis/tests/test_manifest.py`
- **test_build_manifest_single_session_single_view()** (4 connections) — `analysis/tests/test_manifest.py`
- **test_build_manifest_skips_non_session_directories()** (4 connections) — `analysis/tests/test_manifest.py`
- **test_build_manifest_two_sessions()** (4 connections) — `analysis/tests/test_manifest.py`
- **DataFrame** (3 connections)
- **test_trial_uid_is_deterministic()** (2 connections) — `analysis/tests/test_manifest.py`
- **Path** (1 connections)
- **Stage 0 (build_manifest) output: manifest.parquet, one row per trial x view.** (1 connections) — `analysis/pipeline/contracts.py`
- *... and 9 more nodes in this community*

## Relationships

- [Provenance](Provenance.md) (14 shared connections)
- [test_qc_gate.py](test_qc_gate.py.md) (10 shared connections)
- [orchestration.py](orchestration.py.md) (5 shared connections)
- [TrialRecord](TrialRecord.md) (5 shared connections)
- [test_stages_b7_scaffold.py](test_stages_b7_scaffold.py.md) (4 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (4 shared connections)
- [test_roundtrip.py](test_roundtrip.py.md) (3 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (3 shared connections)
- [CameraInfo](CameraInfo.md) (1 shared connections)

## Source Files

- `analysis/pipeline/contracts.py`
- `analysis/pipeline/stages/manifest.py`
- `analysis/tests/test_manifest.py`

## Audit Trail

- EXTRACTED: 119 (93%)
- INFERRED: 9 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
# TrialRecord

> 13 nodes

## Key Concepts

- **TrialRecord** (19 connections) — `shared/schema/trials.py`
- **read_trials_csv()** (17 connections) — `shared/schema/trials.py`
- **write_trials_csv()** (14 connections) — `shared/schema/trials.py`
- **_synthetic_trials()** (5 connections) — `shared/tests/test_roundtrip.py`
- **test_trials_csv_rejects_future_schema_version()** (5 connections) — `shared/tests/test_roundtrip.py`
- **.from_row()** (4 connections) — `shared/schema/trials.py`
- **test_trials_csv_round_trip()** (4 connections) — `shared/tests/test_roundtrip.py`
- **.included()** (2 connections) — `shared/schema/trials.py`
- **.to_row()** (2 connections) — `shared/schema/trials.py`
- **Any** (2 connections)
- **Path** (2 connections)
- **One trial's outcome: identity, timing, flags, and capture stats.** (1 connections) — `shared/schema/trials.py`
- **Valid by default; only experimenter flags make a trial invalid. auto_flags…** (1 connections) — `shared/schema/trials.py`

## Relationships

- [ReviewSessionController](ReviewSessionController.md) (9 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (9 shared connections)
- [test_roundtrip.py](test_roundtrip.py.md) (9 shared connections)
- [manifest.py](manifest.py.md) (5 shared connections)
- [test_full_session_round_trip_via_acquisition_naming_and_glue](test_full_session_round_trip_via_acquisition_naming_and_glue.md) (3 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (3 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (2 shared connections)

## Source Files

- `shared/schema/trials.py`
- `shared/tests/test_roundtrip.py`

## Audit Trail

- EXTRACTED: 53 (90%)
- INFERRED: 6 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
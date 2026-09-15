# test_roundtrip.py

> 17 nodes

## Key Concepts

- **test_roundtrip.py** (23 connections) — `shared/tests/test_roundtrip.py`
- **SessionMetadata** (20 connections) — `shared/schema/session_metadata.py`
- **test_full_session_round_trip()** (10 connections) — `shared/tests/test_roundtrip.py`
- **.read_json()** (8 connections) — `shared/schema/session_metadata.py`
- **write_timestamps_csv()** (8 connections) — `shared/schema/timestamps.py`
- **_synthetic_session_metadata()** (6 connections) — `shared/tests/test_roundtrip.py`
- **test_session_metadata_rejects_future_schema_version()** (5 connections) — `shared/tests/test_roundtrip.py`
- **_synthetic_timestamps()** (4 connections) — `shared/tests/test_roundtrip.py`
- **test_session_metadata_round_trip()** (4 connections) — `shared/tests/test_roundtrip.py`
- **test_timestamps_csv_round_trip()** (4 connections) — `shared/tests/test_roundtrip.py`
- **.to_dict()** (3 connections) — `shared/schema/session_metadata.py`
- **.write_json()** (3 connections) — `shared/schema/session_metadata.py`
- **Path** (2 connections)
- **Path** (2 connections)
- **One row: everything captured once per session, at lock time.** (1 connections) — `shared/schema/session_metadata.py`
- **Round-trip proof of the acquisition <-> analysis contract (checkpoint A0).…** (1 connections) — `shared/tests/test_roundtrip.py`
- **Simulates the contract end-to-end: everything one session directory holds.** (1 connections) — `shared/tests/test_roundtrip.py`

## Relationships

- [SchemaValidationError](SchemaValidationError.md) (17 shared connections)
- [TrialRecord](TrialRecord.md) (9 shared connections)
- [CameraInfo](CameraInfo.md) (7 shared connections)
- [test_full_session_round_trip_via_acquisition_naming_and_glue](test_full_session_round_trip_via_acquisition_naming_and_glue.md) (3 shared connections)
- [manifest.py](manifest.py.md) (3 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (1 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (1 shared connections)

## Source Files

- `shared/schema/session_metadata.py`
- `shared/schema/timestamps.py`
- `shared/tests/test_roundtrip.py`

## Audit Trail

- EXTRACTED: 62 (85%)
- INFERRED: 11 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
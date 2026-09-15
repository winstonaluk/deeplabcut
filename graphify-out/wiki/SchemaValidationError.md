# SchemaValidationError

> 22 nodes

## Key Concepts

- **SchemaValidationError** (17 connections) — `shared/schema/errors.py`
- **trials.py** (17 connections) — `shared/schema/trials.py`
- **TimestampRow** (16 connections) — `shared/schema/timestamps.py`
- **SchemaVersionError** (15 connections) — `shared/schema/errors.py`
- **session_metadata.py** (13 connections) — `shared/schema/session_metadata.py`
- **timestamps.py** (13 connections) — `shared/schema/timestamps.py`
- **read_timestamps_csv()** (11 connections) — `shared/schema/timestamps.py`
- **schema/__init__.py** (11 connections) — `shared/schema/__init__.py`
- **errors.py** (8 connections) — `shared/schema/errors.py`
- **.from_row()** (3 connections) — `shared/schema/timestamps.py`
- **.timestamp_rows()** (2 connections) — `acquisition/acquisition/writer.py`
- **ValueError** (2 connections)
- **.__init__()** (1 connections) — `shared/schema/errors.py`
- **.to_row()** (1 connections) — `shared/schema/timestamps.py`
- **Exceptions raised by the shared schema readers/writers.** (1 connections) — `shared/schema/errors.py`
- **On-disk data was written by an incompatible schema version. Per the cross-repo…** (1 connections) — `shared/schema/errors.py`
- **A record is missing a required field or holds an invalid value.** (1 connections) — `shared/schema/errors.py`
- **Shared data contract between the acquisition GUI and the analysis pipeline.…** (1 connections) — `shared/schema/__init__.py`
- **``session_metadata.json`` — the session-level record. Written once by the…** (1 connections) — `shared/schema/session_metadata.py`
- **Per-trial timestamp sidecar CSV — hardware chunk-data timestamps and frame IDs.…** (1 connections) — `shared/schema/timestamps.py`
- **One captured frame's chunk-data identity.** (1 connections) — `shared/schema/timestamps.py`
- **``trials.csv`` — one row per trial, the machine-readable valid/invalid table.…** (1 connections) — `shared/schema/trials.py`

## Relationships

- [test_roundtrip.py](test_roundtrip.py.md) (17 shared connections)
- [TrialRecord](TrialRecord.md) (9 shared connections)
- [CameraInfo](CameraInfo.md) (7 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (5 shared connections)
- [manifest.py](manifest.py.md) (4 shared connections)
- [WriterThread](WriterThread.md) (3 shared connections)
- [test_full_session_round_trip_via_acquisition_naming_and_glue](test_full_session_round_trip_via_acquisition_naming_and_glue.md) (3 shared connections)
- [test_storage.py](test_storage.py.md) (3 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (3 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (2 shared connections)
- [ReviewSessionController](ReviewSessionController.md) (2 shared connections)

## Source Files

- `acquisition/acquisition/writer.py`
- `shared/schema/__init__.py`
- `shared/schema/errors.py`
- `shared/schema/session_metadata.py`
- `shared/schema/timestamps.py`
- `shared/schema/trials.py`

## Audit Trail

- EXTRACTED: 87 (89%)
- INFERRED: 11 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
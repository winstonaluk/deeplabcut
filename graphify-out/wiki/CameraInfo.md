# CameraInfo

> 11 nodes

## Key Concepts

- **CameraInfo** (13 connections) — `shared/schema/session_metadata.py`
- **build_session_metadata()** (7 connections) — `acquisition/storage/metadata.py`
- **.from_dict()** (6 connections) — `shared/schema/session_metadata.py`
- **metadata.py** (5 connections) — `acquisition/storage/metadata.py`
- **test_build_session_metadata_maps_config_and_runtime_info()** (4 connections) — `acquisition/tests/test_storage.py`
- **.from_dict()** (4 connections) — `shared/schema/session_metadata.py`
- **Any** (4 connections)
- **.to_dict()** (2 connections) — `shared/schema/session_metadata.py`
- **datetime** (2 connections)
- **Assembles SessionMetadata at session lock (A5) from config + runtime info.** (1 connections) — `acquisition/storage/metadata.py`
- **One camera's identity and onboard-settings verification for a session.** (1 connections) — `shared/schema/session_metadata.py`

## Relationships

- [test_roundtrip.py](test_roundtrip.py.md) (7 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (7 shared connections)
- [test_storage.py](test_storage.py.md) (3 shared connections)
- [test_full_session_round_trip_via_acquisition_naming_and_glue](test_full_session_round_trip_via_acquisition_naming_and_glue.md) (2 shared connections)
- [manifest.py](manifest.py.md) (1 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (1 shared connections)

## Source Files

- `acquisition/storage/metadata.py`
- `acquisition/tests/test_storage.py`
- `shared/schema/session_metadata.py`

## Audit Trail

- EXTRACTED: 28 (80%)
- INFERRED: 7 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
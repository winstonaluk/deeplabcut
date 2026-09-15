# test_storage.py

> 21 nodes

## Key Concepts

- **test_storage.py** (26 connections) — `acquisition/tests/test_storage.py`
- **trial_video_filename()** (11 connections) — `acquisition/storage/naming.py`
- **naming.py** (11 connections) — `acquisition/storage/naming.py`
- **create_session_directory()** (8 connections) — `acquisition/storage/naming.py`
- **trial_timestamps_filename()** (8 connections) — `acquisition/storage/naming.py`
- **SessionDirectoryExistsError** (6 connections) — `acquisition/storage/naming.py`
- **session_dir_path()** (6 connections) — `acquisition/storage/naming.py`
- **session_dir_name()** (4 connections) — `acquisition/storage/naming.py`
- **_trial_basename()** (4 connections) — `acquisition/storage/naming.py`
- **test_create_session_directory_never_overwrites()** (4 connections) — `acquisition/tests/test_storage.py`
- **datetime** (4 connections)
- **test_trial_timestamps_filename_matches_video_basename()** (3 connections) — `acquisition/tests/test_storage.py`
- **test_session_dir_name_matches_spec_pattern()** (2 connections) — `acquisition/tests/test_storage.py`
- **test_trial_video_filename_matches_spec_pattern()** (2 connections) — `acquisition/tests/test_storage.py`
- **test_view_token_is_off_by_default_and_opt_in()** (2 connections) — `acquisition/tests/test_storage.py`
- **test_view_token_requires_a_view_name()** (2 connections) — `acquisition/tests/test_storage.py`
- **Path** (2 connections)
- **Session directory and trial filename generation. See acquisition/CLAUDE.md…** (1 connections) — `acquisition/storage/naming.py`
- **Refusing to overwrite an existing session directory (never allowed).** (1 connections) — `acquisition/storage/naming.py`
- **Creates and returns the session directory. Never overwrites.** (1 connections) — `acquisition/storage/naming.py`
- **Checkpoint A4: filename generation, session_metadata.json, trials.csv,…** (1 connections) — `acquisition/tests/test_storage.py`

## Relationships

- [test_full_session_round_trip_via_acquisition_naming_and_glue](test_full_session_round_trip_via_acquisition_naming_and_glue.md) (8 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (3 shared connections)
- [CameraInfo](CameraInfo.md) (3 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (3 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (2 shared connections)
- [test_storage_a8.py](test_storage_a8.py.md) (1 shared connections)
- [test_interfaces.py](test_interfaces.py.md) (1 shared connections)

## Source Files

- `acquisition/storage/naming.py`
- `acquisition/tests/test_storage.py`

## Audit Trail

- EXTRACTED: 64 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
# load_config

> 23 nodes

## Key Concepts

- **load_config()** (28 connections) — `acquisition/app/config.py`
- **app/config.py** (27 connections) — `acquisition/app/config.py`
- **ConfigError** (13 connections) — `acquisition/app/config.py`
- **app/__main__.py** (6 connections) — `acquisition/app/__main__.py`
- **acquisition/tests/test_config.py** (6 connections) — `acquisition/tests/test_config.py`
- **main()** (4 connections) — `acquisition/app/__main__.py`
- **_node_value_str()** (3 connections) — `acquisition/app/config.py`
- **parse_args()** (3 connections) — `acquisition/app/__main__.py`
- **test_load_config_rejects_empty_camera_list()** (3 connections) — `acquisition/tests/test_config.py`
- **test_load_config_rejects_missing_top_level_key()** (3 connections) — `acquisition/tests/test_config.py`
- **CameraConfig** (2 connections) — `acquisition/app/config.py`
- **StagingConfig** (2 connections) — `acquisition/app/config.py`
- **test_camera_verify_table_covers_the_settings_that_corrupt_training_data()** (2 connections) — `acquisition/tests/test_camera_schema.py`
- **test_keyframe_interval_becomes_a_gop_in_frames()** (2 connections) — `acquisition/tests/test_camera_schema.py`
- **test_load_config_has_every_key_and_default()** (2 connections) — `acquisition/tests/test_config.py`
- **Path** (1 connections)
- **ValueError** (1 connections)
- **Namespace** (1 connections)
- **Loads and validates config.toml into typed dataclasses. Every threshold, path,…** (1 connections) — `acquisition/app/config.py`
- **Renders a TOML scalar the way a GenICam node reports it. Booleans are the only…** (1 connections) — `acquisition/app/config.py`
- **Parses and validates config.toml. Raises ConfigError on any missing key.…** (1 connections) — `acquisition/app/config.py`
- **config.toml is missing a required key or holds an invalid value.** (1 connections) — `acquisition/app/config.py`
- **CLI entry point. python -m app --mock # synthetic frames, no hardware python -m…** (1 connections) — `acquisition/app/__main__.py`

## Relationships

- [test_recording_screen.py](test_recording_screen.py.md) (8 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (7 shared connections)
- [test_storage_a8.py](test_storage_a8.py.md) (4 shared connections)
- [pipeline/config.py](pipeline-config.py.md) (3 shared connections)
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) (3 shared connections)
- [verify_a10.py](verify_a10.py.md) (3 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (2 shared connections)
- [TrialStateMachine](TrialStateMachine.md) (2 shared connections)
- [PixelFormat](PixelFormat.md) (2 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (2 shared connections)
- [test_interfaces.py](test_interfaces.py.md) (2 shared connections)
- [test_stages_b7_scaffold.py](test_stages_b7_scaffold.py.md) (1 shared connections)

## Source Files

- `acquisition/app/__main__.py`
- `acquisition/app/config.py`
- `acquisition/tests/test_camera_schema.py`
- `acquisition/tests/test_config.py`

## Audit Trail

- EXTRACTED: 71 (91%)
- INFERRED: 7 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
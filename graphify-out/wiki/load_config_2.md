# load_config()

> God node · 28 connections · `acquisition/app/config.py`

**Community:** [load_config](load_config.md)

## Connections by Relation

### calls
- ConfigError `EXTRACTED`
- CaptureConfig `EXTRACTED`
- EncoderConfig `EXTRACTED`
- TrialTimingConfig `EXTRACTED`
- main() `EXTRACTED`
- StorageConfig `EXTRACTED`
- MetadataConfig `EXTRACTED`
- AppConfig `EXTRACTED`
- main() `EXTRACTED`
- test_config_matches_the_rig_camera() `EXTRACTED`
- _node_value_str() `EXTRACTED`
- test_camera_verify_pixel_format_agrees_with_capture_pixel_format() `EXTRACTED`
- test_load_config_rejects_empty_camera_list() `EXTRACTED`
- test_load_config_rejects_missing_top_level_key() `EXTRACTED`
- test_open_reports_real_geometry_and_is_idempotent() `EXTRACTED`
- CameraConfig `EXTRACTED`
- StagingConfig `EXTRACTED`
- test_camera_verify_table_covers_the_settings_that_corrupt_training_data() `EXTRACTED`
- test_keyframe_interval_becomes_a_gop_in_frames() `EXTRACTED`
- test_load_config_has_every_key_and_default() `EXTRACTED`
- *…and 1 more `calls` connection(s) not listed (lowest-degree first to go)*

### contains
- app/config.py `EXTRACTED`

### imports
- [test_camera_schema.py](test_camera_schema.py.md) `EXTRACTED`
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) `EXTRACTED`
- [verify_a10.py](verify_a10.py.md) `EXTRACTED`
- app/__main__.py `EXTRACTED`
- acquisition/tests/test_config.py `EXTRACTED`

### rationale_for
- Parses and validates config.toml. Raises ConfigError on any missing key.… `EXTRACTED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
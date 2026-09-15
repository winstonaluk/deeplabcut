# test_camera_schema.py

> 46 nodes

## Key Concepts

- **test_camera_schema.py** (47 connections) — `acquisition/tests/test_camera_schema.py`
- **MockCamera** (42 connections) — `acquisition/acquisition/mock_camera.py`
- **run_preflight_checks()** (22 connections) — `acquisition/acquisition/preflight.py`
- **_WrongSettingsCamera** (7 connections) — `acquisition/tests/test_camera_schema.py`
- **test_mock_camera_emits_frames_in_its_declared_pixel_format()** (4 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_blocks_on_frame_rate_mismatch()** (4 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_reports_every_failure_in_one_pass()** (4 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_skips_camera_checks_when_the_camera_will_not_open()** (4 connections) — `acquisition/tests/test_camera_schema.py`
- **test_writer_command_carries_the_right_quality_flag()** (4 connections) — `acquisition/tests/test_camera_schema.py`
- **._make_frame()** (3 connections) — `acquisition/acquisition/mock_camera.py`
- **._run()** (3 connections) — `acquisition/acquisition/mock_camera.py`
- **test_camera_verify_pixel_format_agrees_with_capture_pixel_format()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_config_rejects_an_unknown_pixel_format()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_mock_camera_reports_its_own_geometry_and_rate()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_open_is_idempotent()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_accepts_frame_rate_inside_tolerance()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_blocks_on_resolution_mismatch()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_passes_when_resolution_agrees()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_reports_each_wrong_camera_setting_separately()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_preflight_retains_passing_checks_for_display()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_qsv_and_x264_get_their_own_quality_scale()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **test_qsv_quality_falls_back_to_crf_when_unset()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **.close()** (2 connections) — `acquisition/acquisition/mock_camera.py`
- **.start_streaming()** (2 connections) — `acquisition/acquisition/mock_camera.py`
- **.stop_streaming()** (2 connections) — `acquisition/acquisition/mock_camera.py`
- *... and 21 more nodes in this community*

## Relationships

- [test_storage_a8.py](test_storage_a8.py.md) (10 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (8 shared connections)
- [NodeCheck](NodeCheck.md) (8 shared connections)
- [test_recording_screen.py](test_recording_screen.py.md) (7 shared connections)
- [PixelFormat](PixelFormat.md) (7 shared connections)
- [load_config](load_config.md) (7 shared connections)
- [Frame](Frame.md) (5 shared connections)
- [WriterThread](WriterThread.md) (5 shared connections)
- [CameraBackend](CameraBackend.md) (4 shared connections)
- [CameraError](CameraError.md) (3 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (2 shared connections)
- [verify_a10.py](verify_a10.py.md) (2 shared connections)

## Source Files

- `acquisition/acquisition/mock_camera.py`
- `acquisition/acquisition/preflight.py`
- `acquisition/tests/test_camera_schema.py`

## Audit Trail

- EXTRACTED: 124 (90%)
- INFERRED: 14 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
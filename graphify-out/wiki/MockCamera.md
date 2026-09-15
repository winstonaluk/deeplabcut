# MockCamera

> God node · 42 connections · `acquisition/acquisition/mock_camera.py`

**Community:** [test_camera_schema.py](test_camera_schema.py.md)

## Connections by Relation

### calls
- _make_screen() `EXTRACTED`
- test_begin_trial_hands_off_preroll_and_live_frames_without_gap_or_duplicate() `EXTRACTED`
- _make_rig() `EXTRACTED`
- test_mock_camera_emits_frames_in_its_declared_pixel_format() `EXTRACTED`
- test_preflight_blocks_on_frame_rate_mismatch() `EXTRACTED`
- test_mock_camera_reports_its_own_geometry_and_rate() `EXTRACTED`
- test_open_is_idempotent() `EXTRACTED`
- test_preflight_accepts_frame_rate_inside_tolerance() `EXTRACTED`
- test_preflight_blocks_on_resolution_mismatch() `EXTRACTED`
- test_preflight_passes_when_resolution_agrees() `EXTRACTED`
- test_preflight_retains_passing_checks_for_display() `EXTRACTED`
- test_queue_drops_and_counts_under_backpressure() `EXTRACTED`
- test_preflight_blocks_session_start_below_disk_threshold() `EXTRACTED`
- test_mock_verify_settings_passes_everything_so_the_no_hardware_path_works() `EXTRACTED`

### contains
- mock_camera.py `EXTRACTED`

### imports
- [test_camera_schema.py](test_camera_schema.py.md) `EXTRACTED`
- [test_recording_session.py](test_recording_session.py.md) `EXTRACTED`
- [test_recording_screen.py](test_recording_screen.py.md) `EXTRACTED`
- [test_storage_a8.py](test_storage_a8.py.md) `EXTRACTED`
- test_capture_pipeline.py `EXTRACTED`

### inherits
- [CameraBackend](CameraBackend.md) `EXTRACTED`
- _WrongSettingsCamera `EXTRACTED`

### method
- ._run() `EXTRACTED`
- ._make_frame() `EXTRACTED`
- .verify_settings() `EXTRACTED`
- .pixel_format() `EXTRACTED`
- .__init__() `EXTRACTED`
- .close() `EXTRACTED`
- .start_streaming() `EXTRACTED`
- .stop_streaming() `EXTRACTED`
- .frame_rate() `EXTRACTED`
- .incomplete_frame_count() `EXTRACTED`
- .open() `EXTRACTED`
- .load_user_set() `EXTRACTED`
- .serial() `EXTRACTED`
- .is_streaming() `EXTRACTED`
- .resolution() `EXTRACTED`

### uses
- [Frame](Frame.md) `INFERRED`
- [PixelFormat](PixelFormat.md) `INFERRED`
- [NodeCheck](NodeCheck.md) `INFERRED`
- test_mock_capture_produces_playable_h264() `INFERRED`
- test_preflight_skips_camera_checks_when_the_camera_will_not_open() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
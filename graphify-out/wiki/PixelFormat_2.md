# PixelFormat

> God node · 39 connections · `acquisition/acquisition/frame.py`

**Community:** [PixelFormat](PixelFormat.md)

## Connections by Relation

### calls
- .source_pixel_format() `EXTRACTED`

### contains
- frame.py `EXTRACTED`

### imports
- [test_camera_schema.py](test_camera_schema.py.md) `EXTRACTED`
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) `EXTRACTED`
- app/config.py `EXTRACTED`
- spinnaker_camera.py `EXTRACTED`
- camera_backend.py `EXTRACTED`
- capture_controller.py `EXTRACTED`
- writer.py `EXTRACTED`
- mock_camera.py `EXTRACTED`

### inherits
- Enum `EXTRACTED`
- str `EXTRACTED`

### method
- .ffmpeg_pixel_format() `EXTRACTED`
- .channels() `EXTRACTED`
- .expected_shape() `EXTRACTED`

### rationale_for
- Pixel formats a CameraBackend may deliver. Deliberately a small closed set, not… `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- .pixel_format() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .pixel_format() `EXTRACTED`
- .pixel_format() `EXTRACTED`
- .pixel_format() `EXTRACTED`

### uses
- [MockCamera](MockCamera.md) `INFERRED`
- [SpinnakerCamera](SpinnakerCamera.md) `INFERRED`
- [CameraBackend](CameraBackend.md) `INFERRED`
- [WriterThread](WriterThread.md) `INFERRED`
- [CaptureController](CaptureController.md) `INFERRED`
- CaptureConfig `INFERRED`
- _make_frame_event_handler() `INFERRED`
- test_writer_rejects_frames_that_do_not_match_its_ffmpeg_pipe() `INFERRED`
- test_writer_rejects_a_pixel_format_it_was_not_configured_for() `INFERRED`
- _build_handler_class() `INFERRED`
- test_config_matches_the_rig_camera() `INFERRED`
- test_mock_camera_emits_frames_in_its_declared_pixel_format() `INFERRED`
- test_pixel_format_is_known_before_the_camera_is_open() `INFERRED`
- test_frame_defaults_to_mono8() `INFERRED`
- test_mock_camera_reports_its_own_geometry_and_rate() `INFERRED`
- test_streaming_delivers_frames_with_intact_chunk_data() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
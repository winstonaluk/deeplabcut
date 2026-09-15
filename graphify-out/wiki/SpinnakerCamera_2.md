# SpinnakerCamera

> God node · 35 connections · `acquisition/acquisition/spinnaker_camera.py`

**Community:** [SpinnakerCamera](SpinnakerCamera.md)

## Connections by Relation

### calls
- main() `EXTRACTED`
- test_pixel_format_is_known_before_the_camera_is_open() `EXTRACTED`
- test_satisfies_camera_backend() `EXTRACTED`
- test_verify_settings_requires_an_open_camera() `EXTRACTED`
- test_close_is_idempotent_on_a_camera_that_never_opened() `EXTRACTED`
- test_load_user_set_reports_why_it_failed_rather_than_raising() `EXTRACTED`

### contains
- spinnaker_camera.py `EXTRACTED`

### imports
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) `EXTRACTED`
- [verify_a10.py](verify_a10.py.md) `EXTRACTED`

### inherits
- [CameraBackend](CameraBackend.md) `EXTRACTED`

### method
- .open() `EXTRACTED`
- ._configure_chunk_data() `EXTRACTED`
- ._configure_stream_buffers() `EXTRACTED`
- .verify_settings() `EXTRACTED`
- ._teardown() `EXTRACTED`
- ._find_by_serial() `EXTRACTED`
- .start_streaming() `EXTRACTED`
- .close() `EXTRACTED`
- .load_user_set() `EXTRACTED`
- .last_user_set_error() `EXTRACTED`
- ._refresh_reported_state() `EXTRACTED`
- .stop_streaming() `EXTRACTED`
- .frame_rate() `EXTRACTED`
- .__init__() `EXTRACTED`
- .resolution() `EXTRACTED`
- .pixel_format() `EXTRACTED`
- .serial() `EXTRACTED`
- .is_streaming() `EXTRACTED`
- .incomplete_frame_count() `EXTRACTED`

### uses
- [PixelFormat](PixelFormat.md) `INFERRED`
- [CameraError](CameraError.md) `INFERRED`
- [NodeCheck](NodeCheck.md) `INFERRED`
- test_hardware_reported_properties_refuse_to_guess() `INFERRED`
- test_unknown_serial_raises_camera_error() `INFERRED`
- camera() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
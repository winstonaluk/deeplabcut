# CameraBackend

> God node · 31 connections · `acquisition/acquisition/camera_backend.py`

**Community:** [CameraBackend](CameraBackend.md)

## Connections by Relation

### calls
- test_camera_backend_is_abstract() `EXTRACTED`

### contains
- camera_backend.py `EXTRACTED`

### imports
- [test_camera_schema.py](test_camera_schema.py.md) `EXTRACTED`
- [test_interfaces.py](test_interfaces.py.md) `EXTRACTED`
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) `EXTRACTED`
- spinnaker_camera.py `EXTRACTED`
- capture_controller.py `EXTRACTED`
- preflight.py `EXTRACTED`
- mock_camera.py `EXTRACTED`

### inherits
- [MockCamera](MockCamera.md) `EXTRACTED`
- [SpinnakerCamera](SpinnakerCamera.md) `EXTRACTED`
- ABC `EXTRACTED`

### method
- .start_streaming() `EXTRACTED`
- .pixel_format() `EXTRACTED`
- .verify_settings() `EXTRACTED`
- .stop_streaming() `EXTRACTED`
- .serial() `EXTRACTED`
- .resolution() `EXTRACTED`
- .frame_rate() `EXTRACTED`
- .incomplete_frame_count() `EXTRACTED`
- .open() `EXTRACTED`
- .close() `EXTRACTED`
- .load_user_set() `EXTRACTED`
- .is_streaming() `EXTRACTED`

### rationale_for
- One physical (or simulated) camera. Lifecycle: ``open()`` ->… `EXTRACTED`

### references
- .__init__() `EXTRACTED`

### uses
- [PixelFormat](PixelFormat.md) `INFERRED`
- [CaptureController](CaptureController.md) `INFERRED`
- run_preflight_checks() `INFERRED`
- _camera_checks() `INFERRED`
- test_satisfies_camera_backend() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
# SpinnakerCamera

> 15 nodes

## Key Concepts

- **SpinnakerCamera** (35 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **._teardown()** (4 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **test_pixel_format_is_known_before_the_camera_is_open()** (4 connections) — `acquisition/tests/test_spinnaker_camera.py`
- **.close()** (3 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.frame_rate()** (3 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.load_user_set()** (3 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **._refresh_reported_state()** (3 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.stop_streaming()** (3 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **_release_system()** (2 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **test_close_is_idempotent_on_a_camera_that_never_opened()** (2 connections) — `acquisition/tests/test_spinnaker_camera.py`
- **.incomplete_frame_count()** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.is_streaming()** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.serial()** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **Read live, not cached. While ExposureAuto is on, the resulting rate tracks…** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **The target format is a construction-time decision from config, unlike…** (1 connections) — `acquisition/tests/test_spinnaker_camera.py`

## Relationships

- [CameraError](CameraError.md) (14 shared connections)
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) (10 shared connections)
- [PixelFormat](PixelFormat.md) (4 shared connections)
- [verify_a10.py](verify_a10.py.md) (2 shared connections)
- [CameraBackend](CameraBackend.md) (1 shared connections)
- [test_storage_a8.py](test_storage_a8.py.md) (1 shared connections)
- [NodeCheck](NodeCheck.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/spinnaker_camera.py`
- `acquisition/tests/test_spinnaker_camera.py`

## Audit Trail

- EXTRACTED: 43 (86%)
- INFERRED: 7 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
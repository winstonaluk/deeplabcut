# NodeCheck

> 11 nodes

## Key Concepts

- **NodeCheck** (14 connections) — `acquisition/acquisition/camera_backend.py`
- **mock_camera.py** (13 connections) — `acquisition/acquisition/mock_camera.py`
- **.verify_settings()** (3 connections) — `acquisition/acquisition/camera_backend.py`
- **.verify_settings()** (3 connections) — `acquisition/acquisition/mock_camera.py`
- **test_node_check_describes_a_mismatch_usefully()** (2 connections) — `acquisition/tests/test_camera_schema.py`
- **.verify_settings()** (2 connections) — `acquisition/tests/test_camera_schema.py`
- **.describe()** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **One camera setting read back and compared against its expected value. Values…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **Reads back each named camera node and compares it to ``expected``. Read-only by…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **Synthetic camera backend. The whole app must run against this with zero…** (1 connections) — `acquisition/acquisition/mock_camera.py`
- **Every check passes: a synthetic camera has no real nodes to contradict the…** (1 connections) — `acquisition/acquisition/mock_camera.py`

## Relationships

- [test_camera_schema.py](test_camera_schema.py.md) (8 shared connections)
- [CameraBackend](CameraBackend.md) (4 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (2 shared connections)
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) (1 shared connections)
- [CameraError](CameraError.md) (1 shared connections)
- [SpinnakerCamera](SpinnakerCamera.md) (1 shared connections)
- [Frame](Frame.md) (1 shared connections)
- [PixelFormat](PixelFormat.md) (1 shared connections)
- [test_recording_screen.py](test_recording_screen.py.md) (1 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (1 shared connections)
- [test_storage_a8.py](test_storage_a8.py.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/camera_backend.py`
- `acquisition/acquisition/mock_camera.py`
- `acquisition/tests/test_camera_schema.py`

## Audit Trail

- EXTRACTED: 29 (91%)
- INFERRED: 3 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
# CameraBackend

> 27 nodes

## Key Concepts

- **CameraBackend** (31 connections) — `acquisition/acquisition/camera_backend.py`
- **camera_backend.py** (16 connections) — `acquisition/acquisition/camera_backend.py`
- **.pixel_format()** (3 connections) — `acquisition/acquisition/camera_backend.py`
- **.start_streaming()** (3 connections) — `acquisition/acquisition/camera_backend.py`
- **.close()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **.frame_rate()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **.incomplete_frame_count()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **.load_user_set()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **.open()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **.resolution()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **.serial()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **.stop_streaming()** (2 connections) — `acquisition/acquisition/camera_backend.py`
- **ABC** (2 connections)
- **.is_streaming()** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **FrameCallback** (1 connections)
- **Camera abstraction. SpinnakerCamera and MockCamera both implement this. Every…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **Begins delivering frames to ``on_frame`` from the backend's own thread. Must…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **Stops frame delivery. Idempotent if not currently streaming.** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **The camera's serial number (or a synthetic one for MockCamera).** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **``(width, height)`` actually being delivered, read from the camera. Not the…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **The format frames are delivered in, after any backend conversion.** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **The acquisition frame rate the camera reports, in frames per second. Compared…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **Frames the camera delivered incomplete, and the backend discarded. Counted…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **One physical (or simulated) camera. Lifecycle: ``open()`` ->…** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **Connects to the camera. Idempotent. Raises CameraError on failure.** (1 connections) — `acquisition/acquisition/camera_backend.py`
- *... and 2 more nodes in this community*

## Relationships

- [NodeCheck](NodeCheck.md) (4 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (4 shared connections)
- [test_interfaces.py](test_interfaces.py.md) (3 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (3 shared connections)
- [test_storage_a8.py](test_storage_a8.py.md) (3 shared connections)
- [CameraError](CameraError.md) (3 shared connections)
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) (3 shared connections)
- [Frame](Frame.md) (3 shared connections)
- [PixelFormat](PixelFormat.md) (3 shared connections)
- [SpinnakerCamera](SpinnakerCamera.md) (1 shared connections)
- [verify_a10.py](verify_a10.py.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/camera_backend.py`

## Audit Trail

- EXTRACTED: 53 (91%)
- INFERRED: 5 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
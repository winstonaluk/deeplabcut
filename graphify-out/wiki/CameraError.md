# CameraError

> 24 nodes

## Key Concepts

- **CameraError** (26 connections) — `acquisition/acquisition/camera_backend.py`
- **spinnaker_camera.py** (21 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **Any** (9 connections)
- **.open()** (8 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **_make_frame_event_handler()** (7 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **_set_enum()** (7 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **._configure_chunk_data()** (6 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **._configure_stream_buffers()** (6 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **_build_handler_class()** (5 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **_find_enum_entry()** (5 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **_node_value_str()** (5 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **._find_by_serial()** (4 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.start_streaming()** (4 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **_acquire_system()** (3 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.resolution()** (2 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **FrameCallback** (2 connections)
- **RuntimeError** (1 connections)
- **A camera failed to open, load its UserSet, or stream.** (1 connections) — `acquisition/acquisition/camera_backend.py`
- **Real hardware backend via Teledyne FLIR Spinnaker/PySpin. Implemented and…** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **Reads a node as a string, whatever its type. "<unreadable>" on failure. GenICam…** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **The readable entry named ``entry_name`` -- by exact symbolic name first, then…** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **Enables the chunks invariant 6 depends on. The camera ships with…** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **Sets buffer handling and depth. Not covered by user sets.** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **Builds the image event handler that feeds ``on_frame``. The class derives from…** (1 connections) — `acquisition/acquisition/spinnaker_camera.py`

## Relationships

- [SpinnakerCamera](SpinnakerCamera.md) (14 shared connections)
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) (10 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (3 shared connections)
- [verify_a10.py](verify_a10.py.md) (3 shared connections)
- [CameraBackend](CameraBackend.md) (3 shared connections)
- [PixelFormat](PixelFormat.md) (3 shared connections)
- [Frame](Frame.md) (2 shared connections)
- [test_storage_a8.py](test_storage_a8.py.md) (1 shared connections)
- [Logging.py](Logging.py.md) (1 shared connections)
- [NodeCheck](NodeCheck.md) (1 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/camera_backend.py`
- `acquisition/acquisition/spinnaker_camera.py`

## Audit Trail

- EXTRACTED: 77 (91%)
- INFERRED: 8 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
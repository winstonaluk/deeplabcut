# Frame

> 31 nodes

## Key Concepts

- **Frame** (42 connections) — `acquisition/acquisition/frame.py`
- **CaptureController** (28 connections) — `acquisition/acquisition/capture_controller.py`
- **PreRollBuffer** (9 connections) — `acquisition/acquisition/preroll_buffer.py`
- **preroll_buffer.py** (5 connections) — `acquisition/acquisition/preroll_buffer.py`
- **.begin_trial()** (4 connections) — `acquisition/acquisition/capture_controller.py`
- **.attach_sink()** (3 connections) — `acquisition/acquisition/capture_controller.py`
- **.__init__()** (3 connections) — `acquisition/acquisition/capture_controller.py`
- **.latest_frame()** (3 connections) — `acquisition/acquisition/capture_controller.py`
- **.get()** (3 connections) — `acquisition/acquisition/frame_queue.py`
- **.put_or_drop()** (3 connections) — `acquisition/acquisition/frame_queue.py`
- **.snapshot()** (3 connections) — `acquisition/acquisition/preroll_buffer.py`
- **test_frame_defaults_to_mono8()** (3 connections) — `acquisition/tests/test_camera_schema.py`
- **._on_frame()** (2 connections) — `acquisition/acquisition/capture_controller.py`
- **.pixel_format()** (2 connections) — `acquisition/acquisition/capture_controller.py`
- **.resolution()** (2 connections) — `acquisition/acquisition/capture_controller.py`
- **.push()** (2 connections) — `acquisition/acquisition/preroll_buffer.py`
- **.detach_sink()** (1 connections) — `acquisition/acquisition/capture_controller.py`
- **.incomplete_frame_count()** (1 connections) — `acquisition/acquisition/capture_controller.py`
- **.start()** (1 connections) — `acquisition/acquisition/capture_controller.py`
- **.stop()** (1 connections) — `acquisition/acquisition/capture_controller.py`
- **.__init__()** (1 connections) — `acquisition/acquisition/preroll_buffer.py`
- **.maxlen()** (1 connections) — `acquisition/acquisition/preroll_buffer.py`
- **Attaches ``sink`` and returns the pre-roll to prepend, atomically. The returned…** (1 connections) — `acquisition/acquisition/capture_controller.py`
- **Begins forwarding frames to ``sink`` with no pre-roll handoff. A trial with a…** (1 connections) — `acquisition/acquisition/capture_controller.py`
- **What the camera is actually delivering -- the writer sizes its FFmpeg pipe from…** (1 connections) — `acquisition/acquisition/capture_controller.py`
- *... and 6 more nodes in this community*

## Relationships

- [BoundedFrameQueue](BoundedFrameQueue.md) (21 shared connections)
- [PoseEstimate](PoseEstimate.md) (6 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (5 shared connections)
- [WriterThread](WriterThread.md) (5 shared connections)
- [PixelFormat](PixelFormat.md) (4 shared connections)
- [CameraBackend](CameraBackend.md) (3 shared connections)
- [test_recording_screen.py](test_recording_screen.py.md) (2 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (2 shared connections)
- [verify_a10.py](verify_a10.py.md) (2 shared connections)
- [CameraError](CameraError.md) (2 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (1 shared connections)
- [NodeCheck](NodeCheck.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/capture_controller.py`
- `acquisition/acquisition/frame.py`
- `acquisition/acquisition/frame_queue.py`
- `acquisition/acquisition/preroll_buffer.py`
- `acquisition/tests/test_camera_schema.py`

## Audit Trail

- EXTRACTED: 76 (81%)
- INFERRED: 18 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
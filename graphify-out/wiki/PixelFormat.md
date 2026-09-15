# PixelFormat

> 15 nodes

## Key Concepts

- **PixelFormat** (39 connections) — `acquisition/acquisition/frame.py`
- **.__init__()** (5 connections) — `acquisition/acquisition/writer.py`
- **test_config_matches_the_rig_camera()** (4 connections) — `acquisition/tests/test_camera_schema.py`
- **.ffmpeg_pixel_format()** (2 connections) — `acquisition/acquisition/frame.py`
- **.__init__()** (2 connections) — `acquisition/acquisition/mock_camera.py`
- **.pixel_format()** (2 connections) — `acquisition/acquisition/mock_camera.py`
- **.__init__()** (2 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.pixel_format()** (2 connections) — `acquisition/acquisition/spinnaker_camera.py`
- **.channels()** (1 connections) — `acquisition/acquisition/frame.py`
- **.expected_shape()** (1 connections) — `acquisition/acquisition/frame.py`
- **Path** (1 connections)
- **str** (1 connections)
- **Pixel formats a CameraBackend may deliver. Deliberately a small closed set, not…** (1 connections) — `acquisition/acquisition/frame.py`
- **The ``-pixel_format`` value for FFmpeg's rawvideo demuxer.** (1 connections) — `acquisition/acquisition/frame.py`
- **These values were read off the camera, not chosen. See HARDWARE.md.** (1 connections) — `acquisition/tests/test_camera_schema.py`

## Relationships

- [test_camera_schema.py](test_camera_schema.py.md) (7 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (5 shared connections)
- [Frame](Frame.md) (4 shared connections)
- [SpinnakerCamera](SpinnakerCamera.md) (4 shared connections)
- [WriterThread](WriterThread.md) (4 shared connections)
- [CameraBackend](CameraBackend.md) (3 shared connections)
- [CameraError](CameraError.md) (3 shared connections)
- [test_recording_screen.py](test_recording_screen.py.md) (2 shared connections)
- [load_config](load_config.md) (2 shared connections)
- [test_spinnaker_camera.py](test_spinnaker_camera.py.md) (2 shared connections)
- [NodeCheck](NodeCheck.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/frame.py`
- `acquisition/acquisition/mock_camera.py`
- `acquisition/acquisition/spinnaker_camera.py`
- `acquisition/acquisition/writer.py`
- `acquisition/tests/test_camera_schema.py`

## Audit Trail

- EXTRACTED: 35 (69%)
- INFERRED: 16 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
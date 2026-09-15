# BoundedFrameQueue

> 28 nodes

## Key Concepts

- **BoundedFrameQueue** (31 connections) — `acquisition/acquisition/frame_queue.py`
- **recording_session.py** (29 connections) — `acquisition/acquisition/recording_session.py`
- **test_capture_pipeline.py** (20 connections) — `acquisition/tests/test_capture_pipeline.py`
- **frame.py** (18 connections) — `acquisition/acquisition/frame.py`
- **capture_controller.py** (16 connections) — `acquisition/acquisition/capture_controller.py`
- **writer.py** (15 connections) — `acquisition/acquisition/writer.py`
- **frame_queue.py** (10 connections) — `acquisition/acquisition/frame_queue.py`
- **test_mock_capture_produces_playable_h264()** (7 connections) — `acquisition/tests/test_capture_pipeline.py`
- **test_a_recording_cut_off_mid_trial_still_decodes()** (6 connections) — `acquisition/tests/test_capture_pipeline.py`
- **test_begin_trial_hands_off_preroll_and_live_frames_without_gap_or_duplicate()** (5 connections) — `acquisition/tests/test_capture_pipeline.py`
- **test_writer_memory_growth_stays_bounded_over_a_long_run()** (5 connections) — `acquisition/tests/test_capture_pipeline.py`
- **_ffprobe_frame_count()** (3 connections) — `acquisition/tests/test_capture_pipeline.py`
- **test_queue_drops_and_counts_under_backpressure()** (3 connections) — `acquisition/tests/test_capture_pipeline.py`
- **requires_ffmpeg** (3 connections)
- **Enum** (2 connections)
- **.dropped_count()** (1 connections) — `acquisition/acquisition/frame_queue.py`
- **.__init__()** (1 connections) — `acquisition/acquisition/frame_queue.py`
- **.maxsize()** (1 connections) — `acquisition/acquisition/frame_queue.py`
- **.qsize()** (1 connections) — `acquisition/acquisition/frame_queue.py`
- **Path** (1 connections)
- **Wires one CameraBackend's frame callback to the pre-roll buffer, a latest-frame…** (1 connections) — `acquisition/acquisition/capture_controller.py`
- **Bounded, drop-on-full frame queue between capture and the writer thread.…** (1 connections) — `acquisition/acquisition/frame_queue.py`
- **The unit of data a CameraBackend produces per exposure.** (1 connections) — `acquisition/acquisition/frame.py`
- **Orchestrates capture, writing, and trial state for one locked session, across N…** (1 connections) — `acquisition/acquisition/recording_session.py`
- **Consumes frames from a bounded queue and pipes them to FFmpeg as raw video.…** (1 connections) — `acquisition/acquisition/writer.py`
- *... and 3 more nodes in this community*

## Relationships

- [Frame](Frame.md) (21 shared connections)
- [WriterThread](WriterThread.md) (11 shared connections)
- [verify_a10.py](verify_a10.py.md) (8 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (8 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (7 shared connections)
- [PixelFormat](PixelFormat.md) (5 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (4 shared connections)
- [CameraBackend](CameraBackend.md) (3 shared connections)
- [test_interfaces.py](test_interfaces.py.md) (3 shared connections)
- [Logging.py](Logging.py.md) (3 shared connections)
- [test_storage.py](test_storage.py.md) (3 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (3 shared connections)

## Source Files

- `acquisition/acquisition/capture_controller.py`
- `acquisition/acquisition/frame.py`
- `acquisition/acquisition/frame_queue.py`
- `acquisition/acquisition/recording_session.py`
- `acquisition/acquisition/writer.py`
- `acquisition/tests/test_capture_pipeline.py`

## Audit Trail

- EXTRACTED: 124 (89%)
- INFERRED: 16 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
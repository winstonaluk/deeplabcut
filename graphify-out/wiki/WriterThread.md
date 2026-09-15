# WriterThread

> 20 nodes

## Key Concepts

- **WriterThread** (31 connections) — `acquisition/acquisition/writer.py`
- **WriterError** (13 connections) — `acquisition/acquisition/writer.py`
- **test_writer_rejects_frames_that_do_not_match_its_ffmpeg_pipe()** (7 connections) — `acquisition/tests/test_camera_schema.py`
- **test_writer_rejects_a_pixel_format_it_was_not_configured_for()** (6 connections) — `acquisition/tests/test_camera_schema.py`
- **._assert_frame_matches_pipe()** (5 connections) — `acquisition/acquisition/writer.py`
- **._write_frame()** (5 connections) — `acquisition/acquisition/writer.py`
- **.run()** (4 connections) — `acquisition/acquisition/writer.py`
- **.build_command()** (3 connections) — `acquisition/acquisition/writer.py`
- **.raise_if_failed()** (2 connections) — `acquisition/acquisition/writer.py`
- **._shutdown_process()** (2 connections) — `acquisition/acquisition/writer.py`
- **.stop()** (2 connections) — `acquisition/acquisition/writer.py`
- **.frames_written()** (1 connections) — `acquisition/acquisition/writer.py`
- **.returncode()** (1 connections) — `acquisition/acquisition/writer.py`
- **.stderr_tail()** (1 connections) — `acquisition/acquisition/writer.py`
- **RuntimeError** (1 connections)
- **The FFmpeg invocation for this trial. Separated from :meth:`run` so it is…** (1 connections) — `acquisition/acquisition/writer.py`
- **Fails loudly on the first frame if its geometry doesn't match what FFmpeg was…** (1 connections) — `acquisition/acquisition/writer.py`
- **FFmpeg exited non-zero. Carries its stderr tail for diagnostics.** (1 connections) — `acquisition/acquisition/writer.py`
- **Requests a clean shutdown: drain whatever is already queued, then close…** (1 connections) — `acquisition/acquisition/writer.py`
- **The bug this exists for: FFmpeg does not error on a size mismatch, it silently…** (1 connections) — `acquisition/tests/test_camera_schema.py`

## Relationships

- [BoundedFrameQueue](BoundedFrameQueue.md) (11 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (5 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (5 shared connections)
- [Frame](Frame.md) (5 shared connections)
- [PixelFormat](PixelFormat.md) (4 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (3 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (2 shared connections)
- [verify_a10.py](verify_a10.py.md) (2 shared connections)

## Source Files

- `acquisition/acquisition/writer.py`
- `acquisition/tests/test_camera_schema.py`

## Audit Trail

- EXTRACTED: 47 (75%)
- INFERRED: 16 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
# WriterThread

> God node · 31 connections · `acquisition/acquisition/writer.py`

**Community:** [WriterThread](WriterThread.md)

## Connections by Relation

### calls
- main() `EXTRACTED`
- test_writer_rejects_frames_that_do_not_match_its_ffmpeg_pipe() `EXTRACTED`
- test_writer_rejects_a_pixel_format_it_was_not_configured_for() `EXTRACTED`
- ._start_recording() `EXTRACTED`

### contains
- writer.py `EXTRACTED`

### imports
- [test_camera_schema.py](test_camera_schema.py.md) `EXTRACTED`
- recording_session.py `EXTRACTED`
- [verify_a10.py](verify_a10.py.md) `EXTRACTED`
- test_capture_pipeline.py `EXTRACTED`

### method
- ._write_frame() `EXTRACTED`
- ._assert_frame_matches_pipe() `EXTRACTED`
- .__init__() `EXTRACTED`
- .run() `EXTRACTED`
- .build_command() `EXTRACTED`
- .raise_if_failed() `EXTRACTED`
- ._shutdown_process() `EXTRACTED`
- .stop() `EXTRACTED`
- .timestamp_rows() `EXTRACTED`
- .stderr_tail() `EXTRACTED`
- .frames_written() `EXTRACTED`
- .returncode() `EXTRACTED`

### uses
- [Frame](Frame.md) `INFERRED`
- [PixelFormat](PixelFormat.md) `INFERRED`
- [RecordingSessionController](RecordingSessionController.md) `INFERRED`
- [BoundedFrameQueue](BoundedFrameQueue.md) `INFERRED`
- TimestampRow `INFERRED`
- CameraRig `INFERRED`
- test_mock_capture_produces_playable_h264() `INFERRED`
- test_a_recording_cut_off_mid_trial_still_decodes() `INFERRED`
- test_writer_memory_growth_stays_bounded_over_a_long_run() `INFERRED`
- test_writer_command_carries_the_right_quality_flag() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
# BoundedFrameQueue

> God node · 31 connections · `acquisition/acquisition/frame_queue.py`

**Community:** [BoundedFrameQueue](BoundedFrameQueue.md)

## Connections by Relation

### calls
- main() `EXTRACTED`
- test_writer_rejects_frames_that_do_not_match_its_ffmpeg_pipe() `EXTRACTED`
- test_writer_rejects_a_pixel_format_it_was_not_configured_for() `EXTRACTED`
- ._start_recording() `EXTRACTED`
- test_begin_trial_hands_off_preroll_and_live_frames_without_gap_or_duplicate() `EXTRACTED`
- test_queue_drops_and_counts_under_backpressure() `EXTRACTED`

### contains
- frame_queue.py `EXTRACTED`

### imports
- [test_camera_schema.py](test_camera_schema.py.md) `EXTRACTED`
- recording_session.py `EXTRACTED`
- [verify_a10.py](verify_a10.py.md) `EXTRACTED`
- test_capture_pipeline.py `EXTRACTED`
- capture_controller.py `EXTRACTED`
- writer.py `EXTRACTED`

### method
- .put_or_drop() `EXTRACTED`
- .get() `EXTRACTED`
- .__init__() `EXTRACTED`
- .dropped_count() `EXTRACTED`
- .maxsize() `EXTRACTED`
- .qsize() `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- .begin_trial() `EXTRACTED`
- .attach_sink() `EXTRACTED`

### uses
- [Frame](Frame.md) `INFERRED`
- [RecordingSessionController](RecordingSessionController.md) `INFERRED`
- [WriterThread](WriterThread.md) `INFERRED`
- [CaptureController](CaptureController.md) `INFERRED`
- CameraRig `INFERRED`
- test_mock_capture_produces_playable_h264() `INFERRED`
- test_a_recording_cut_off_mid_trial_still_decodes() `INFERRED`
- test_writer_memory_growth_stays_bounded_over_a_long_run() `INFERRED`
- test_writer_command_carries_the_right_quality_flag() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
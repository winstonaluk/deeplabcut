# Frame

> God node · 42 connections · `acquisition/acquisition/frame.py`

**Community:** [Frame](Frame.md)

## Connections by Relation

### calls
- test_writer_rejects_frames_that_do_not_match_its_ffmpeg_pipe() `EXTRACTED`
- test_writer_rejects_a_pixel_format_it_was_not_configured_for() `EXTRACTED`
- _build_handler_class() `EXTRACTED`
- ._make_frame() `EXTRACTED`
- test_frame_defaults_to_mono8() `EXTRACTED`

### contains
- frame.py `EXTRACTED`

### imports
- [test_camera_schema.py](test_camera_schema.py.md) `EXTRACTED`
- spinnaker_camera.py `EXTRACTED`
- test_capture_pipeline.py `EXTRACTED`
- camera_backend.py `EXTRACTED`
- capture_controller.py `EXTRACTED`
- writer.py `EXTRACTED`
- mock_camera.py `EXTRACTED`
- recording_screen.py `EXTRACTED`
- frame_queue.py `EXTRACTED`
- pose_provider.py `EXTRACTED`
- null_pose_provider.py `EXTRACTED`
- preroll_buffer.py `EXTRACTED`

### rationale_for
- One captured image plus its camera-supplied chunk data.… `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- ._assert_frame_matches_pipe() `EXTRACTED`
- ._write_frame() `EXTRACTED`
- .begin_trial() `EXTRACTED`
- .infer() `EXTRACTED`
- .snapshot() `EXTRACTED`
- .put_or_drop() `EXTRACTED`
- .infer() `EXTRACTED`
- .latest_frame() `EXTRACTED`
- .get() `EXTRACTED`
- ._on_frame() `EXTRACTED`
- .push() `EXTRACTED`

### uses
- [MockCamera](MockCamera.md) `INFERRED`
- [BoundedFrameQueue](BoundedFrameQueue.md) `INFERRED`
- [WriterThread](WriterThread.md) `INFERRED`
- [CaptureController](CaptureController.md) `INFERRED`
- PreRollBuffer `INFERRED`
- NullPoseProvider `INFERRED`
- PoseProvider `INFERRED`
- test_a_recording_cut_off_mid_trial_still_decodes() `INFERRED`
- test_writer_memory_growth_stays_bounded_over_a_long_run() `INFERRED`
- frame_to_pixmap() `INFERRED`
- test_mock_camera_emits_frames_in_its_declared_pixel_format() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
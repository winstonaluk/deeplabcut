# CaptureController

> God node · 28 connections · `acquisition/acquisition/capture_controller.py`

**Community:** [Frame](Frame.md)

## Connections by Relation

### calls
- _make_screen() `EXTRACTED`
- main() `EXTRACTED`
- test_begin_trial_hands_off_preroll_and_live_frames_without_gap_or_duplicate() `EXTRACTED`
- _make_rig() `EXTRACTED`

### contains
- capture_controller.py `EXTRACTED`

### imports
- [test_recording_session.py](test_recording_session.py.md) `EXTRACTED`
- recording_session.py `EXTRACTED`
- [test_recording_screen.py](test_recording_screen.py.md) `EXTRACTED`
- [verify_a10.py](verify_a10.py.md) `EXTRACTED`
- test_capture_pipeline.py `EXTRACTED`

### method
- .begin_trial() `EXTRACTED`
- .__init__() `EXTRACTED`
- .attach_sink() `EXTRACTED`
- .latest_frame() `EXTRACTED`
- .resolution() `EXTRACTED`
- .pixel_format() `EXTRACTED`
- ._on_frame() `EXTRACTED`
- .start() `EXTRACTED`
- .stop() `EXTRACTED`
- .detach_sink() `EXTRACTED`
- .incomplete_frame_count() `EXTRACTED`

### uses
- [Frame](Frame.md) `INFERRED`
- [PixelFormat](PixelFormat.md) `INFERRED`
- [CameraBackend](CameraBackend.md) `INFERRED`
- [BoundedFrameQueue](BoundedFrameQueue.md) `INFERRED`
- CameraRig `INFERRED`
- PreRollBuffer `INFERRED`
- test_mock_capture_produces_playable_h264() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
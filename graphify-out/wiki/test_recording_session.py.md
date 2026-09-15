# test_recording_session.py

> 22 nodes

## Key Concepts

- **test_recording_session.py** (39 connections) — `acquisition/tests/test_recording_session.py`
- **_make_controller()** (18 connections) — `acquisition/tests/test_recording_session.py`
- **_teardown()** (13 connections) — `acquisition/tests/test_recording_session.py`
- **requires_ffmpeg** (10 connections)
- **hardware_fps()** (7 connections) — `acquisition/acquisition/recording_session.py`
- **test_achieved_fps_is_not_inflated_by_the_preroll()** (7 connections) — `acquisition/tests/test_recording_session.py`
- **test_full_trial_lifecycle_writes_video_timestamps_and_trials_csv()** (6 connections) — `acquisition/tests/test_recording_session.py`
- **test_max_duration_auto_stop_via_tick_finalizes_the_trial()** (6 connections) — `acquisition/tests/test_recording_session.py`
- **_make_rig()** (5 connections) — `acquisition/tests/test_recording_session.py`
- **test_min_duration_swallow_leaves_trial_recording()** (5 connections) — `acquisition/tests/test_recording_session.py`
- **test_one_camera_failing_does_not_cost_the_other_cameras_trial()** (5 connections) — `acquisition/tests/test_recording_session.py`
- **test_sidecar_frame_ids_are_contiguous_across_the_preroll_boundary()** (5 connections) — `acquisition/tests/test_recording_session.py`
- **test_discard_last_removes_files_and_record()** (4 connections) — `acquisition/tests/test_recording_session.py`
- **test_dropped_frame_count_aggregates_across_cameras()** (4 connections) — `acquisition/tests/test_recording_session.py`
- **test_flag_toggle_targets_current_recording_trial()** (4 connections) — `acquisition/tests/test_recording_session.py`
- **test_flag_toggle_targets_most_recent_completed_trial_after_stop()** (4 connections) — `acquisition/tests/test_recording_session.py`
- **test_multi_camera_writes_one_file_pair_per_camera()** (4 connections) — `acquisition/tests/test_recording_session.py`
- **test_flag_toggle_is_a_toggle_not_a_set()** (3 connections) — `acquisition/tests/test_recording_session.py`
- **test_hardware_fps_is_measured_on_the_camera_clock()** (3 connections) — `acquisition/tests/test_recording_session.py`
- **Frames per second measured on the camera's own clock. ``(n - 1) / span`` over…** (1 connections) — `acquisition/acquisition/recording_session.py`
- **Checkpoint A6 core: RecordingSessionController orchestrates capture, writing,…** (1 connections) — `acquisition/tests/test_recording_session.py`
- **Pre-roll frames are in the file but precede the trial's start, so counting them…** (1 connections) — `acquisition/tests/test_recording_session.py`

## Relationships

- [TrialPhase](TrialPhase.md) (7 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (5 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (5 shared connections)
- [test_recording_screen.py](test_recording_screen.py.md) (5 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (4 shared connections)
- [TrialStateMachine](TrialStateMachine.md) (4 shared connections)
- [test_interfaces.py](test_interfaces.py.md) (3 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (2 shared connections)
- [Frame](Frame.md) (2 shared connections)
- [WriterThread](WriterThread.md) (2 shared connections)
- [NodeCheck](NodeCheck.md) (1 shared connections)
- [load_config](load_config.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/recording_session.py`
- `acquisition/tests/test_recording_session.py`

## Audit Trail

- EXTRACTED: 89 (91%)
- INFERRED: 9 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
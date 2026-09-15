# RecordingSessionController

> God node · 35 connections · `acquisition/acquisition/recording_session.py`

**Community:** [RecordingSessionController](RecordingSessionController.md)

## Connections by Relation

### calls
- _make_controller() `EXTRACTED`
- _make_screen() `EXTRACTED`

### contains
- recording_session.py `EXTRACTED`

### imports
- [test_recording_session.py](test_recording_session.py.md) `EXTRACTED`
- [test_recording_screen.py](test_recording_screen.py.md) `EXTRACTED`
- recording_screen.py `EXTRACTED`

### method
- ._stop_recording() `EXTRACTED`
- ._persist_trials_csv() `EXTRACTED`
- ._video_filename() `EXTRACTED`
- ._timestamps_filename() `EXTRACTED`
- .__init__() `EXTRACTED`
- .discard_last() `EXTRACTED`
- ._start_recording() `EXTRACTED`
- .toggle_trial() `EXTRACTED`
- .toggle_flag() `EXTRACTED`
- .target_trial_number() `EXTRACTED`
- .trial_records() `EXTRACTED`
- .tick() `EXTRACTED`
- .rigs() `EXTRACTED`
- .set_note() `EXTRACTED`
- .phase() `EXTRACTED`
- .current_trial_number() `EXTRACTED`
- .elapsed_s() `EXTRACTED`
- .dropped_frame_count() `EXTRACTED`
- .active_flags() `EXTRACTED`

### references
- .__init__() `EXTRACTED`

### uses
- [BoundedFrameQueue](BoundedFrameQueue.md) `INFERRED`
- [WriterThread](WriterThread.md) `INFERRED`
- [TrialStateMachine](TrialStateMachine.md) `INFERRED`
- [TrialPhase](TrialPhase.md) `INFERRED`
- [TrialRecord](TrialRecord.md) `INFERRED`
- [RecordingScreen](RecordingScreen.md) `INFERRED`
- TrialToggleAction `INFERRED`
- WriterError `INFERRED`
- AppConfig `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
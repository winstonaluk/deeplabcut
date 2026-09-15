# TrialStateMachine

> 16 nodes

## Key Concepts

- **TrialStateMachine** (24 connections) — `acquisition/acquisition/trial_state_machine.py`
- **TrialTimingConfig** (12 connections) — `acquisition/app/config.py`
- **._elapsed()** (5 connections) — `acquisition/acquisition/trial_state_machine.py`
- **._finalize_trial()** (5 connections) — `acquisition/acquisition/trial_state_machine.py`
- **.request_toggle()** (5 connections) — `acquisition/acquisition/trial_state_machine.py`
- **test_trial_state_machine_starts_idle()** (5 connections) — `acquisition/tests/test_interfaces.py`
- **.tick()** (4 connections) — `acquisition/acquisition/trial_state_machine.py`
- **.elapsed_s()** (3 connections) — `acquisition/acquisition/trial_state_machine.py`
- **.__init__()** (3 connections) — `acquisition/acquisition/trial_state_machine.py`
- **TrialToggleResult** (2 connections) — `acquisition/acquisition/trial_state_machine.py`
- **.phase()** (2 connections) — `acquisition/acquisition/trial_state_machine.py`
- **.current_trial_number()** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- **Seconds since the current trial started; 0.0 while IDLE.** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- **Spacebar handler entry point. Starts a trial from IDLE, stops one from…** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- **Periodic check (e.g. a Qt timer) for max-duration auto-stop and…** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- **Owns trial phase and timing guards for one paradigm's trials. Not itself a Qt…** (1 connections) — `acquisition/acquisition/trial_state_machine.py`

## Relationships

- [test_interfaces.py](test_interfaces.py.md) (8 shared connections)
- [TrialPhase](TrialPhase.md) (6 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (4 shared connections)
- [test_recording_screen.py](test_recording_screen.py.md) (3 shared connections)
- [test_full_session_round_trip_via_acquisition_naming_and_glue](test_full_session_round_trip_via_acquisition_naming_and_glue.md) (3 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (2 shared connections)
- [load_config](load_config.md) (2 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/trial_state_machine.py`
- `acquisition/app/config.py`
- `acquisition/tests/test_interfaces.py`

## Audit Trail

- EXTRACTED: 47 (90%)
- INFERRED: 5 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
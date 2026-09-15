# test_full_session_round_trip_via_acquisition_naming_and_glue

> 13 nodes

## Key Concepts

- **test_full_session_round_trip_via_acquisition_naming_and_glue()** (16 connections) — `acquisition/tests/test_storage.py`
- **TrialOutcome** (10 connections) — `acquisition/acquisition/trial_state_machine.py`
- **build_trial_record()** (9 connections) — `acquisition/storage/trial_record.py`
- **trial_record.py** (8 connections) — `acquisition/storage/trial_record.py`
- **.discard_last()** (3 connections) — `acquisition/acquisition/trial_state_machine.py`
- **.last_outcome()** (3 connections) — `acquisition/acquisition/trial_state_machine.py`
- **test_build_trial_record_maps_outcome_to_schema_fields()** (3 connections) — `acquisition/tests/test_storage.py`
- **datetime** (2 connections)
- **Non-destructive peek at the most recently completed trial's outcome -- unlike…** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- **Ctrl+Delete handler: discards the last completed trial after confirmation is…** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- **A completed trial's timing and auto-applied flags. Experimenter-assigned flags…** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- **Bridges TrialStateMachine's TrialOutcome (monotonic timing, no wall-clock…** (1 connections) — `acquisition/storage/trial_record.py`
- **A4's proof: build a real session directory using only this app's own…** (1 connections) — `acquisition/tests/test_storage.py`

## Relationships

- [test_storage.py](test_storage.py.md) (8 shared connections)
- [TrialStateMachine](TrialStateMachine.md) (3 shared connections)
- [TrialRecord](TrialRecord.md) (3 shared connections)
- [test_roundtrip.py](test_roundtrip.py.md) (3 shared connections)
- [SchemaValidationError](SchemaValidationError.md) (3 shared connections)
- [test_interfaces.py](test_interfaces.py.md) (2 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (2 shared connections)
- [CameraInfo](CameraInfo.md) (2 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/trial_state_machine.py`
- `acquisition/storage/trial_record.py`
- `acquisition/tests/test_storage.py`

## Audit Trail

- EXTRACTED: 39 (91%)
- INFERRED: 4 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
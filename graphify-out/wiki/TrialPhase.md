# TrialPhase

> 27 nodes

## Key Concepts

- **TrialPhase** (24 connections) — `acquisition/acquisition/trial_state_machine.py`
- **test_trial_state_machine.py** (22 connections) — `acquisition/tests/test_trial_state_machine.py`
- **_machine()** (16 connections) — `acquisition/tests/test_trial_state_machine.py`
- **TrialToggleAction** (13 connections) — `acquisition/acquisition/trial_state_machine.py`
- **FakeClock** (6 connections) — `acquisition/tests/test_trial_state_machine.py`
- **ManualStopCondition** (6 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_spacebar_after_min_duration_stops_the_trial()** (4 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_spacebar_starts_a_trial_from_idle()** (4 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_spacebar_within_min_duration_is_swallowed()** (4 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_max_duration_auto_stops_via_tick()** (3 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_stop_condition_triggers_auto_stop_via_tick_after_min_duration()** (3 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_tick_is_a_noop_before_any_threshold()** (3 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_tick_is_a_noop_while_idle()** (3 connections) — `acquisition/tests/test_trial_state_machine.py`
- **Enum** (3 connections)
- **test_discard_last_decrements_counter_and_clears_outcome()** (2 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_discard_last_returns_none_when_nothing_completed()** (2 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_normal_trial_gets_no_auto_flags()** (2 connections) — `acquisition/tests/test_trial_state_machine.py`
- **test_short_trial_gets_suspiciously_short_auto_flag()** (2 connections) — `acquisition/tests/test_trial_state_machine.py`
- **.advance()** (1 connections) — `acquisition/tests/test_trial_state_machine.py`
- **.__call__()** (1 connections) — `acquisition/tests/test_trial_state_machine.py`
- **.__init__()** (1 connections) — `acquisition/tests/test_trial_state_machine.py`
- **.__init__()** (1 connections) — `acquisition/tests/test_trial_state_machine.py`
- **.set()** (1 connections) — `acquisition/tests/test_trial_state_machine.py`
- **.should_stop()** (1 connections) — `acquisition/tests/test_trial_state_machine.py`
- **What ``request_toggle()`` actually did, so the GUI can react (e.g. show the…** (1 connections) — `acquisition/acquisition/trial_state_machine.py`
- *... and 2 more nodes in this community*

## Relationships

- [test_interfaces.py](test_interfaces.py.md) (8 shared connections)
- [test_recording_session.py](test_recording_session.py.md) (7 shared connections)
- [TrialStateMachine](TrialStateMachine.md) (6 shared connections)
- [RecordingSessionController](RecordingSessionController.md) (4 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (2 shared connections)
- [test_recording_screen.py](test_recording_screen.py.md) (2 shared connections)
- [RecordingScreen](RecordingScreen.md) (1 shared connections)
- [load_config](load_config.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/trial_state_machine.py`
- `acquisition/tests/test_trial_state_machine.py`

## Audit Trail

- EXTRACTED: 60 (74%)
- INFERRED: 21 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
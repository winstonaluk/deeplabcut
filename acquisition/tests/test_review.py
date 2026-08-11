"""Checkpoint A7 (skippable, built anyway): trial table, flag editing, note
entry, other_invalid reason assignment."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from gui.review_screen import ReviewScreen
from paradigms.paradigm import ReasonCode
from schema.trials import TrialRecord, read_trials_csv, write_trials_csv
from storage.review import ReviewSessionController

RECORDS = [
    TrialRecord(
        trial_number=1, start_time="2026-08-11T09:05:00", duration_s=42.5,
        flags=frozenset(), auto_flags=frozenset(), note="", n_frames=100, dropped_frames=0, achieved_fps=30.0,
    ),
    TrialRecord(
        trial_number=2, start_time="2026-08-11T09:08:00", duration_s=12.0,
        flags=frozenset({"fall"}), auto_flags=frozenset({"suspiciously_short"}), note="",
        n_frames=30, dropped_frames=0, achieved_fps=29.9,
    ),
]


def _session_with_trials(tmp_path):
    write_trials_csv(tmp_path / "trials.csv", RECORDS)
    return tmp_path


# -- ReviewSessionController (no Qt) --

def test_loads_existing_trials_csv(tmp_path):
    session_dir = _session_with_trials(tmp_path)
    controller = ReviewSessionController(session_dir)
    assert controller.trial_records() == RECORDS


def test_toggle_flag_persists_to_disk(tmp_path):
    session_dir = _session_with_trials(tmp_path)
    controller = ReviewSessionController(session_dir)

    controller.toggle_flag(1, "other_invalid")

    _, reloaded = read_trials_csv(session_dir / "trials.csv")
    reloaded_by_number = {r.trial_number: r for r in reloaded}
    assert reloaded_by_number[1].flags == frozenset({"other_invalid"})
    assert reloaded_by_number[1].included is False


def test_toggle_flag_twice_clears_it(tmp_path):
    session_dir = _session_with_trials(tmp_path)
    controller = ReviewSessionController(session_dir)

    controller.toggle_flag(2, "fall")  # was already set -> clears
    assert controller.trial_records()[1].flags == frozenset()


def test_set_note_persists_reason_for_other_invalid(tmp_path):
    session_dir = _session_with_trials(tmp_path)
    controller = ReviewSessionController(session_dir)

    controller.toggle_flag(1, "other_invalid")
    controller.set_note(1, "camera occluded by experimenter's hand")

    _, reloaded = read_trials_csv(session_dir / "trials.csv")
    record = {r.trial_number: r for r in reloaded}[1]
    assert record.flags == frozenset({"other_invalid"})
    assert record.note == "camera occluded by experimenter's hand"


# -- ReviewScreen (Qt shell) --

REASON_CODES = (
    ReasonCode(key="F", code="fall", label="Fell from the pole"),
    ReasonCode(key="V", code="other_invalid", label="Generic; reason assigned later"),
)


def _key_event(key, text=""):
    return QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, text)


def test_table_populated_from_trials(qapp, tmp_path):
    session_dir = _session_with_trials(tmp_path)
    controller = ReviewSessionController(session_dir)
    screen = ReviewScreen(controller, REASON_CODES)

    assert screen.table.rowCount() == 2
    assert screen.table.item(0, 0).text() == "1"
    assert screen.table.item(1, 3).text() == "fall"
    assert screen.table.item(1, 5).text() == "invalid"


def test_hotkey_toggles_flag_on_selected_row_and_persists(qapp, tmp_path):
    session_dir = _session_with_trials(tmp_path)
    controller = ReviewSessionController(session_dir)
    screen = ReviewScreen(controller, REASON_CODES)

    screen.table.setCurrentCell(0, 0)  # select trial 1
    screen.keyPressEvent(_key_event(Qt.Key.Key_V, text="V"))

    assert controller.trial_records()[0].flags == frozenset({"other_invalid"})
    assert screen.table.item(0, 3).text() == "other_invalid"

    _, reloaded = read_trials_csv(session_dir / "trials.csv")
    assert {r.trial_number: r for r in reloaded}[1].flags == frozenset({"other_invalid"})


def test_editing_note_cell_persists(qapp, tmp_path):
    session_dir = _session_with_trials(tmp_path)
    controller = ReviewSessionController(session_dir)
    screen = ReviewScreen(controller, REASON_CODES)

    note_item = screen.table.item(0, 6)
    note_item.setText("late annotation: animal froze briefly then continued")
    screen._on_item_changed(note_item)

    assert controller.trial_records()[0].note == "late annotation: animal froze briefly then continued"
    _, reloaded = read_trials_csv(session_dir / "trials.csv")
    assert {r.trial_number: r for r in reloaded}[1].note == "late annotation: animal froze briefly then continued"

"""Checkpoint A5: form, dropdowns from config, validation, preflight checks,
lock-on-start."""

from __future__ import annotations

from datetime import date

from acquisition.preflight import PreflightResult
from app.config import MetadataConfig
from gui.session_setup_screen import SessionSetupResult, SessionSetupScreen

METADATA_CONFIG = MetadataConfig(
    projects=("pdct-pilot", "pdct-main"),
    experimenter_initials=("WL", "AB"),
    animal_id_regex="^[A-Za-z0-9_-]+$",
)


def _screen(qapp, run_preflight=None, known_animal_ids=None):
    if run_preflight is None:
        run_preflight = lambda: PreflightResult(passed=True, failures=())
    screen = SessionSetupScreen(METADATA_CONFIG, known_animal_ids or ["R001", "R002"], run_preflight)
    # Modal QMessageBox.warning/critical block on a click nobody will make
    # in an automated test -- stub them out and just record the call.
    screen.warnings = []
    screen.criticals = []
    screen._show_warning = lambda title, text: screen.warnings.append((title, text))
    screen._show_critical = lambda title, text: screen.criticals.append((title, text))
    return screen


def test_dropdowns_populated_from_config(qapp):
    screen = _screen(qapp)
    assert [screen.project_combo.itemText(i) for i in range(screen.project_combo.count())] == [
        "pdct-pilot",
        "pdct-main",
    ]
    assert [screen.initials_combo.itemText(i) for i in range(screen.initials_combo.count())] == ["WL", "AB"]


def test_date_defaults_to_today_iso_yyyymmdd(qapp):
    screen = _screen(qapp)
    assert screen.date_label.text() == date.today().strftime("%Y%m%d")


def test_validate_rejects_empty_animal_id(qapp):
    screen = _screen(qapp)
    screen.animal_id_edit.setText("")
    assert screen.validate() is None


def test_validate_rejects_animal_id_violating_regex(qapp):
    screen = _screen(qapp)
    screen.animal_id_edit.setText("bad id with spaces!")
    assert screen.validate() is None


def test_validate_accepts_a_valid_animal_id(qapp):
    screen = _screen(qapp)
    screen.animal_id_edit.setText("R042")
    result = screen.validate()
    assert result == SessionSetupResult(
        animal_id="R042", project_name="pdct-pilot", date=date.today().strftime("%Y%m%d"),
        experimenter_initials="WL",
    )


def test_failed_preflight_blocks_start_and_does_not_lock(qapp):
    calls = []

    def failing_preflight():
        calls.append(1)
        return PreflightResult(passed=False, failures=("FFmpeg not found on PATH",))

    screen = _screen(qapp, run_preflight=failing_preflight)
    screen.animal_id_edit.setText("R042")

    received = []
    screen.session_started.connect(lambda r: received.append(r))
    screen.start_button.click()

    assert calls == [1]
    assert received == []
    assert screen.is_locked is False
    assert screen.animal_id_edit.isEnabled() is True


def test_successful_preflight_locks_screen_and_emits_result(qapp):
    screen = _screen(qapp, run_preflight=lambda: PreflightResult(passed=True, failures=()))
    screen.animal_id_edit.setText("R042")
    screen.project_combo.setCurrentText("pdct-main")
    screen.initials_combo.setCurrentText("AB")

    received = []
    screen.session_started.connect(lambda r: received.append(r))
    screen.start_button.click()

    assert screen.is_locked is True
    assert screen.animal_id_edit.isEnabled() is False
    assert screen.project_combo.isEnabled() is False
    assert screen.initials_combo.isEnabled() is False
    assert screen.start_button.isEnabled() is False

    assert len(received) == 1
    assert received[0] == SessionSetupResult(
        animal_id="R042", project_name="pdct-main", date=date.today().strftime("%Y%m%d"),
        experimenter_initials="AB",
    )


def test_invalid_animal_id_does_not_run_preflight_or_lock(qapp):
    calls = []
    screen = _screen(qapp, run_preflight=lambda: calls.append(1) or PreflightResult(True, ()))
    screen.animal_id_edit.setText("")

    screen.start_button.click()

    assert calls == []
    assert screen.is_locked is False

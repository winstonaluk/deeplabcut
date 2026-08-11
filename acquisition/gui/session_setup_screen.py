"""Session setup screen (screen 1 of 3): form, dropdowns from config,
validation, autocomplete, preflight checks, lock-on-start.

Stock Qt widgets and standard layouts only (acquisition/CLAUDE.md "GUI
style"). Preflight logic itself lives in acquisition.preflight -- this class
only renders the result and manages form lock state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Callable

from PySide6.QtCore import QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from acquisition.preflight import PreflightResult
from app.config import MetadataConfig


@dataclass(frozen=True)
class SessionSetupResult:
    animal_id: str
    project_name: str
    date: str
    experimenter_initials: str


class SessionSetupScreen(QWidget):
    session_started = Signal(object)  # SessionSetupResult

    def __init__(
        self,
        metadata_config: MetadataConfig,
        known_animal_ids: list[str],
        run_preflight: Callable[[], PreflightResult],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._metadata_config = metadata_config
        self._run_preflight = run_preflight
        self._locked = False

        self.animal_id_edit = QLineEdit()
        self.animal_id_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(metadata_config.animal_id_regex))
        )
        self.animal_id_edit.setCompleter(QCompleter(known_animal_ids, self))

        self.project_combo = QComboBox()
        self.project_combo.addItems(list(metadata_config.projects))

        self.initials_combo = QComboBox()
        self.initials_combo.addItems(list(metadata_config.experimenter_initials))

        self.date_label = QLabel(date.today().strftime("%Y%m%d"))

        self.start_button = QPushButton("Start Session")
        self.start_button.clicked.connect(self._on_start_clicked)

        layout = QFormLayout()
        layout.addRow("Animal ID", self.animal_id_edit)
        layout.addRow("Project", self.project_combo)
        layout.addRow("Experimenter", self.initials_combo)
        layout.addRow("Date", self.date_label)
        layout.addRow(self.start_button)
        self.setLayout(layout)

    @property
    def is_locked(self) -> bool:
        return self._locked

    def validate(self) -> SessionSetupResult | None:
        """Returns the validated form contents, or None (and shows a warning)
        if the animal ID doesn't match config's regex."""
        animal_id = self.animal_id_edit.text().strip()
        if not animal_id or not re.fullmatch(self._metadata_config.animal_id_regex, animal_id):
            self._show_warning(
                "Invalid animal ID",
                f"Animal ID must match {self._metadata_config.animal_id_regex!r}.",
            )
            return None
        return SessionSetupResult(
            animal_id=animal_id,
            project_name=self.project_combo.currentText(),
            date=self.date_label.text(),
            experimenter_initials=self.initials_combo.currentText(),
        )

    def _on_start_clicked(self) -> None:
        result = self.validate()
        if result is None:
            return

        preflight = self._run_preflight()
        if not preflight.passed:
            self._show_critical("Preflight failed", "\n".join(preflight.failures))
            return

        self._lock()
        self.session_started.emit(result)

    def _show_warning(self, title: str, text: str) -> None:
        """Modal by default; tests override this to avoid blocking on a
        dialog nobody will click."""
        QMessageBox.warning(self, title, text)

    def _show_critical(self, title: str, text: str) -> None:
        QMessageBox.critical(self, title, text)

    def _lock(self) -> None:
        self._locked = True
        self.animal_id_edit.setEnabled(False)
        self.project_combo.setEnabled(False)
        self.initials_combo.setEnabled(False)
        self.start_button.setEnabled(False)

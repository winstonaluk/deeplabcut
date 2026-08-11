"""Review screen (screen 3 of 3, skippable): trial table, flag editing, note
entry, other_invalid reason assignment.

Reuses the same reason-code keymap as the recording screen -- hotkeys are
live "both during a trial and after it ends" per acquisition/CLAUDE.md
"Trial annotation", which this screen extends to apply after the whole
session too. Stock QTableWidget, no custom styling.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from paradigms.paradigm import ReasonCode
from storage.review import ReviewSessionController

_COLUMNS = ["Trial", "Start", "Duration (s)", "Flags", "Auto Flags", "Included", "Note"]
_NOTE_COLUMN = _COLUMNS.index("Note")
_READONLY_COLUMNS = [i for i in range(len(_COLUMNS)) if i != _NOTE_COLUMN]


class ReviewScreen(QWidget):
    def __init__(
        self,
        controller: ReviewSessionController,
        reason_codes: tuple[ReasonCode, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._controller = controller
        self._key_to_code = {rc.key.upper(): rc.code for rc in reason_codes}
        self._refreshing = False

        self.table = QTableWidget()
        self.table.setColumnCount(len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self._on_item_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

        self._refresh()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 -- Qt override
        code = self._key_to_code.get(event.text().upper())
        if code is not None:
            trial_number = self._selected_trial_number()
            if trial_number is not None:
                self._controller.toggle_flag(trial_number, code)
                self._refresh()
            return
        super().keyPressEvent(event)

    def _selected_trial_number(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._refreshing or item.column() != _NOTE_COLUMN:
            return
        trial_number = int(self.table.item(item.row(), 0).text())
        self._controller.set_note(trial_number, item.text())

    def _refresh(self) -> None:
        self._refreshing = True
        records = self._controller.trial_records()
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                str(record.trial_number),
                record.start_time,
                f"{record.duration_s:.1f}",
                ", ".join(sorted(record.flags)),
                ", ".join(sorted(record.auto_flags)),
                "valid" if record.included else "invalid",
                record.note,
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col in _READONLY_COLUMNS:
                    cell.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(row, col, cell)
        self._refreshing = False

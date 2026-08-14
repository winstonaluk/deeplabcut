"""Recording screen (screen 2 of 3): preview tiles, large-font readouts,
spacebar control, reason-code hotkeys, flag targeting, visual flag feedback.

Large font for trial counter/state/elapsed/flags/dropped-frame count is the
one deliberate exception to "stock Qt widgets, standard layouts"
(acquisition/CLAUDE.md "GUI style"). All control logic lives in
RecordingSessionController + TrialStateMachine; this widget only renders
their state and forwards Qt events to them -- never welds trial-stop policy
into a keypress handler (invariant 8).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent, QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from acquisition.frame import Frame
from acquisition.recording_session import RecordingSessionController
from acquisition.trial_state_machine import TrialPhase
from paradigms.paradigm import ReasonCode

_LARGE_FONT = "font-size: 24pt; font-weight: bold;"
_CHIP_INACTIVE = "padding: 4px 10px; border: 1px solid gray; border-radius: 4px;"
_CHIP_ACTIVE = "padding: 4px 10px; border: 2px solid #c00; border-radius: 4px; background-color: #fdd; font-weight: bold;"


def frame_to_pixmap(frame: Frame) -> QPixmap:
    height, width = frame.image.shape
    image = QImage(frame.image.tobytes(), width, height, width, QImage.Format.Format_Grayscale8)
    return QPixmap.fromImage(image)


class RecordingScreen(QWidget):
    def __init__(
        self,
        controller: RecordingSessionController,
        reason_codes: tuple[ReasonCode, ...],
        preview_fps: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._controller = controller
        self._key_to_code = {rc.key.upper(): rc.code for rc in reason_codes}

        self.state_label = QLabel()
        self.state_label.setStyleSheet(_LARGE_FONT)
        self.trial_counter_label = QLabel()
        self.trial_counter_label.setStyleSheet(_LARGE_FONT)
        self.elapsed_label = QLabel()
        self.elapsed_label.setStyleSheet(_LARGE_FONT)
        self.dropped_frames_label = QLabel()
        self.dropped_frames_label.setStyleSheet(_LARGE_FONT)

        readout_layout = QHBoxLayout()
        for label in (self.state_label, self.trial_counter_label, self.elapsed_label, self.dropped_frames_label):
            readout_layout.addWidget(label)

        self.flag_chips: dict[str, QLabel] = {}
        flags_layout = QHBoxLayout()
        for rc in reason_codes:
            chip = QLabel(f"[{rc.key}] {rc.label}")
            chip.setStyleSheet(_CHIP_INACTIVE)
            self.flag_chips[rc.code] = chip
            flags_layout.addWidget(chip)

        self.start_stop_button = QPushButton("Start / Stop (Space)")
        self.start_stop_button.clicked.connect(self._toggle_trial)
        self.discard_button = QPushButton("Discard Last (Ctrl+Delete)")
        self.discard_button.clicked.connect(self._discard_last)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_stop_button)
        buttons_layout.addWidget(self.discard_button)

        self.preview_labels: list[QLabel] = []
        preview_layout = QGridLayout()
        for i, rig in enumerate(controller.rigs):
            label = QLabel(rig.view_name)
            preview_layout.addWidget(label, 0, i)
            self.preview_labels.append(label)

        layout = QVBoxLayout()
        layout.addLayout(readout_layout)
        layout.addLayout(flags_layout)
        layout.addLayout(buttons_layout)
        layout.addLayout(preview_layout)
        self.setLayout(layout)

        self._refresh()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._timer.start(max(1, int(1000 / preview_fps)))

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 -- Qt override
        if event.key() == Qt.Key.Key_Space:
            self._toggle_trial()
            return
        if event.key() == Qt.Key.Key_Delete and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._discard_last()
            return
        code = self._key_to_code.get(event.text().upper())
        if code is not None:
            self._controller.toggle_flag(code)
            self._refresh()
            return
        super().keyPressEvent(event)

    def _toggle_trial(self) -> None:
        self._controller.toggle_trial()
        self._refresh()

    def _discard_last(self) -> None:
        self._controller.discard_last()
        self._refresh()

    def _on_timer(self) -> None:
        self._controller.tick()
        self._refresh()
        self._refresh_preview()

    def _refresh(self) -> None:
        phase = self._controller.phase
        self.state_label.setText("RECORDING" if phase is TrialPhase.RECORDING else "IDLE")
        self.trial_counter_label.setText(f"Trial {self._controller.current_trial_number}")
        self.elapsed_label.setText(f"{self._controller.elapsed_s:.1f}s")
        self.dropped_frames_label.setText(f"Dropped: {self._controller.dropped_frame_count}")

        target = self._controller.target_trial_number()
        active = self._controller.active_flags(target) if target is not None else frozenset()
        for code, chip in self.flag_chips.items():
            chip.setStyleSheet(_CHIP_ACTIVE if code in active else _CHIP_INACTIVE)

    def _refresh_preview(self) -> None:
        for label, rig in zip(self.preview_labels, self._controller.rigs):
            frame = rig.controller.latest_frame
            if frame is not None:
                label.setPixmap(frame_to_pixmap(frame))

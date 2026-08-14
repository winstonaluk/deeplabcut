"""Orchestrates capture, writing, and trial state for one locked session,
across N cameras (invariant 1).

Deliberately plain Python with no Qt dependency, so the whole recording
lifecycle -- start/stop, pre-roll prepending, per-trial file writing, flag
targeting -- is testable without a display. The GUI (A6 RecordingScreen) is
a thin shell that renders this controller's state and forwards keypresses to
it; recording integrity does not depend on the GUI thread (invariant 4).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Callable

from acquisition.capture_controller import CaptureController
from acquisition.frame_queue import BoundedFrameQueue
from acquisition.trial_state_machine import TrialPhase, TrialStateMachine, TrialToggleAction
from acquisition.writer import WriterThread
from app.config import AppConfig
from schema.timestamps import write_timestamps_csv
from schema.trials import TrialRecord, write_trials_csv
from storage.naming import trial_timestamps_filename, trial_video_filename
from storage.trial_record import build_trial_record

logger = logging.getLogger(__name__)


@dataclass
class CameraRig:
    """One camera's live capture pipeline for the session."""

    view_name: str
    controller: CaptureController
    writer: WriterThread | None = None
    writer_queue: BoundedFrameQueue | None = None


class RecordingSessionController:
    def __init__(
        self,
        session_dir: Path,
        animal_id: str,
        project_name: str,
        date: str,
        initials: str,
        config: AppConfig,
        state_machine: TrialStateMachine,
        rigs: list[CameraRig],
        wall_clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._session_dir = Path(session_dir)
        self._animal_id = animal_id
        self._project_name = project_name
        self._date = date
        self._initials = initials
        self._config = config
        self._state_machine = state_machine
        self._rigs = rigs
        self._wall_clock = wall_clock

        self._flags: dict[int, set[str]] = {}
        self._notes: dict[int, str] = {}
        self._trial_records: dict[int, TrialRecord] = {}
        self._trial_wall_start: dict[int, datetime] = {}

    # -- read-only state for the GUI to render --

    @property
    def phase(self) -> TrialPhase:
        return self._state_machine.phase

    @property
    def current_trial_number(self) -> int:
        return self._state_machine.current_trial_number

    @property
    def elapsed_s(self) -> float:
        return self._state_machine.elapsed_s

    @property
    def rigs(self) -> list[CameraRig]:
        return list(self._rigs)

    @property
    def dropped_frame_count(self) -> int:
        return sum(
            rig.writer_queue.dropped_count for rig in self._rigs if rig.writer_queue is not None
        )

    def target_trial_number(self) -> int | None:
        """Currently recording trial if active, else most recently completed
        (acquisition/CLAUDE.md "Trial annotation" -- target trial)."""
        if self._state_machine.phase is TrialPhase.RECORDING:
            return self._state_machine.current_trial_number
        if self._trial_records:
            return max(self._trial_records)
        return None

    def active_flags(self, trial_number: int) -> frozenset[str]:
        return frozenset(self._flags.get(trial_number, set()))

    def trial_records(self) -> list[TrialRecord]:
        return [self._trial_records[n] for n in sorted(self._trial_records)]

    # -- trial control --

    def toggle_trial(self) -> TrialToggleAction:
        result = self._state_machine.request_toggle()
        if result.action is TrialToggleAction.STARTED:
            self._start_recording(result.trial_number)
        elif result.action is TrialToggleAction.STOPPED:
            self._stop_recording(result.trial_number)
        return result.action

    def tick(self) -> None:
        """Periodic call (GUI timer): advances max-duration / stop-condition
        auto-stop and finalizes the recording the same way a manual stop does."""
        was_recording = self._state_machine.phase is TrialPhase.RECORDING
        trial_number = self._state_machine.current_trial_number
        self._state_machine.tick()
        if was_recording and self._state_machine.phase is TrialPhase.IDLE:
            self._stop_recording(trial_number)

    def toggle_flag(self, reason_code: str) -> None:
        """Reason-code hotkey handler. Toggles on the target trial and
        re-persists trials.csv immediately if that trial has already
        finished (live flags -- annotation is never blocking)."""
        trial_number = self.target_trial_number()
        if trial_number is None:
            return
        flags = self._flags.setdefault(trial_number, set())
        flags.symmetric_difference_update({reason_code})

        record = self._trial_records.get(trial_number)
        if record is not None:
            self._trial_records[trial_number] = replace(record, flags=frozenset(flags))
            self._persist_trials_csv()

    def set_note(self, trial_number: int, note: str) -> None:
        self._notes[trial_number] = note
        record = self._trial_records.get(trial_number)
        if record is not None:
            self._trial_records[trial_number] = replace(record, note=note)
            self._persist_trials_csv()

    def discard_last(self) -> int | None:
        """Ctrl+Delete: removes the last completed trial's video, sidecar,
        and record. Returns the discarded trial number, or None."""
        outcome = self._state_machine.discard_last()
        if outcome is None:
            return None

        trial_number = outcome.trial_number
        self._trial_records.pop(trial_number, None)
        self._flags.pop(trial_number, None)
        self._notes.pop(trial_number, None)
        wall_start = self._trial_wall_start.pop(trial_number, None)

        if wall_start is not None:
            for rig in self._rigs:
                video_name = self._video_filename(rig, wall_start, trial_number)
                timestamps_name = self._timestamps_filename(rig, wall_start, trial_number)
                (self._session_dir / video_name).unlink(missing_ok=True)
                (self._session_dir / timestamps_name).unlink(missing_ok=True)

        self._persist_trials_csv()
        return trial_number

    # -- internals --

    def _video_filename(self, rig: CameraRig, wall_start: datetime, trial_number: int) -> str:
        return trial_video_filename(
            self._animal_id, self._project_name, self._date, self._initials,
            wall_start, trial_number, view=rig.view_name,
            include_view_token=self._config.storage.filename_include_view_token,
        )

    def _timestamps_filename(self, rig: CameraRig, wall_start: datetime, trial_number: int) -> str:
        return trial_timestamps_filename(
            self._animal_id, self._project_name, self._date, self._initials,
            wall_start, trial_number, view=rig.view_name,
            include_view_token=self._config.storage.filename_include_view_token,
        )

    def _start_recording(self, trial_number: int) -> None:
        wall_start = self._wall_clock()
        self._trial_wall_start[trial_number] = wall_start
        self._flags.setdefault(trial_number, set())

        for rig in self._rigs:
            preroll_frames = rig.controller.preroll.snapshot()
            queue = BoundedFrameQueue(maxsize=self._config.capture.queue_maxsize)
            # Geometry and source format come from the camera, not config:
            # preflight has already blocked the session if they disagree, so
            # this is the same value with the hardware as its authority.
            width, height = rig.controller.resolution
            writer = WriterThread(
                frame_queue=queue,
                output_path=self._session_dir / self._video_filename(rig, wall_start, trial_number),
                width=width,
                height=height,
                fps=self._config.capture.fps,
                codec=self._config.encoder.codec,
                crf=self._config.encoder.crf,
                pixel_format=self._config.encoder.pixel_format,
                source_pixel_format=rig.controller.pixel_format,
                preroll_frames=preroll_frames,
            )
            writer.start()
            rig.controller.attach_sink(queue)
            rig.writer = writer
            rig.writer_queue = queue

        logger.info("trial %d started", trial_number)

    def _stop_recording(self, trial_number: int) -> None:
        outcome = self._state_machine.last_outcome
        assert outcome is not None and outcome.trial_number == trial_number
        wall_start = self._trial_wall_start[trial_number]

        total_frames = 0
        total_dropped = 0
        fps_samples: list[float] = []

        for rig in self._rigs:
            rig.controller.detach_sink()
            assert rig.writer is not None and rig.writer_queue is not None
            rig.writer.stop()
            rig.writer.join(timeout=30)
            rig.writer.raise_if_failed()

            write_timestamps_csv(
                self._session_dir / self._timestamps_filename(rig, wall_start, trial_number),
                rig.writer.timestamp_rows,
            )

            total_frames += rig.writer.frames_written
            total_dropped += rig.writer_queue.dropped_count
            if outcome.duration_s > 0:
                fps_samples.append(rig.writer.frames_written / outcome.duration_s)

            rig.writer = None
            rig.writer_queue = None

        achieved_fps = sum(fps_samples) / len(fps_samples) if fps_samples else 0.0

        record = build_trial_record(
            outcome,
            wall_start,
            flags=frozenset(self._flags.get(trial_number, set())),
            note=self._notes.get(trial_number, ""),
            n_frames=total_frames,
            dropped_frames=total_dropped,
            achieved_fps=achieved_fps,
        )
        self._trial_records[trial_number] = record
        self._persist_trials_csv()
        logger.info("trial %d stopped: %.1fs, auto_flags=%s", trial_number, outcome.duration_s, outcome.auto_flags)

    def _persist_trials_csv(self) -> None:
        write_trials_csv(self._session_dir / "trials.csv", self.trial_records())

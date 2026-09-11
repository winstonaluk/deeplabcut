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
from typing import Callable, Sequence

from acquisition.capture_controller import CaptureController
from acquisition.frame_queue import BoundedFrameQueue
from acquisition.trial_state_machine import TrialPhase, TrialStateMachine, TrialToggleAction
from acquisition.writer import WriterError, WriterThread
from app.config import AppConfig
from schema.timestamps import TimestampRow, write_timestamps_csv
from schema.trials import TrialRecord, write_trials_csv
from storage.naming import trial_timestamps_filename, trial_video_filename
from storage.trial_record import build_trial_record

logger = logging.getLogger(__name__)

# How long a trial's stop waits for each camera's writer to drain its queue and
# for FFmpeg to finish the file.
WRITER_JOIN_TIMEOUT_S = 30.0


def hardware_fps(rows: Sequence[TimestampRow]) -> float:
    """Frames per second measured on the camera's own clock.

    ``(n - 1) / span`` over the hardware timestamps of every frame in the
    file. Pre-roll frames count: they were captured at the same rate. What
    they must not do is count against the trial's *duration*, which begins
    after them -- that overstated achieved_fps by roughly
    ``preroll_s * fps / duration`` (31.7 fps on a 35 s trial and 37.3 on an
    8 s one, from a camera running at 29.996), and analysis stage 1 checks
    achieved_fps against the nominal rate. Dropped frames lower the result,
    as they should. 0.0 with too few frames to measure.
    """
    if len(rows) < 2:
        return 0.0
    span_ns = rows[-1].hardware_timestamp_ns - rows[0].hardware_timestamp_ns
    if span_ns <= 0:
        return 0.0
    return (len(rows) - 1) / (span_ns / 1e9)


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

        encoder = self._config.encoder
        quality_flag, quality_value = encoder.quality_for(encoder.codec)
        for rig in self._rigs:
            queue = BoundedFrameQueue(maxsize=self._config.capture.queue_maxsize)
            # Snapshot the pre-roll and attach the queue as one atomic step, so
            # the prepended frames and the queued ones are contiguous. As two
            # separate calls, a frame arriving in between was either lost or
            # written twice. Frames wait in the queue while the writer below
            # starts FFmpeg; queue_maxsize absorbs that.
            preroll_frames = rig.controller.begin_trial(queue)
            try:
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
                    codec=encoder.codec,
                    crf=quality_value,
                    pixel_format=encoder.pixel_format,
                    source_pixel_format=rig.controller.pixel_format,
                    quality_flag=quality_flag,
                    preset=encoder.preset_for(encoder.codec),
                    gop=max(1, round(encoder.keyframe_interval_s * self._config.capture.fps)),
                    preroll_frames=preroll_frames,
                )
                writer.start()
            except Exception:
                rig.controller.detach_sink()  # nothing would ever drain the queue
                raise
            rig.writer = writer
            rig.writer_queue = queue

        logger.info("trial %d started", trial_number)

    def _stop_recording(self, trial_number: int) -> None:
        outcome = self._state_machine.last_outcome
        assert outcome is not None and outcome.trial_number == trial_number
        wall_start = self._trial_wall_start[trial_number]

        # Stop every camera before checking any of them. Raising on the first
        # failed writer used to leave the cameras after it still attached and
        # recording, with no sidecar and no trial record -- one camera's FFmpeg
        # failure cost every camera's trial. Stopping them all first also lets
        # their queues drain in parallel.
        for rig in self._rigs:
            rig.controller.detach_sink()
            if rig.writer is not None:
                rig.writer.stop()

        total_frames = 0
        total_dropped = 0
        fps_samples: list[float] = []
        errors: list[Exception] = []

        for rig in self._rigs:
            writer, queue = rig.writer, rig.writer_queue
            rig.writer = None
            rig.writer_queue = None
            if writer is None or queue is None:
                continue

            writer.join(timeout=WRITER_JOIN_TIMEOUT_S)
            try:
                if writer.is_alive():
                    # A join() that times out is not success: FFmpeg has no
                    # return code yet, so raise_if_failed() would pass, and the
                    # file is still being written.
                    raise WriterError(
                        f"camera {rig.view_name}: writer still running after "
                        f"{WRITER_JOIN_TIMEOUT_S:g}s, video may be incomplete"
                    )
                writer.raise_if_failed()
            except Exception as exc:  # noqa: BLE001 -- collected, raised after persisting
                logger.error("trial %d, camera %s: %s", trial_number, rig.view_name, exc)
                errors.append(exc)

            # Written even when the video failed: it is the record of which
            # frames were sent, and the trial row below refers to them.
            rows = writer.timestamp_rows
            write_timestamps_csv(
                self._session_dir / self._timestamps_filename(rig, wall_start, trial_number),
                rows,
            )
            total_frames += writer.frames_written
            total_dropped += queue.dropped_count
            fps = hardware_fps(rows)
            if fps > 0:
                fps_samples.append(fps)

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

        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise WriterError(
                f"{len(errors)} cameras failed in trial {trial_number}: "
                + "; ".join(str(e) for e in errors)
            ) from errors[0]

    def _persist_trials_csv(self) -> None:
        write_trials_csv(self._session_dir / "trials.csv", self.trial_records())

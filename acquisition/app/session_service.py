"""Composition root and session lifecycle owner (checkpoint A12).

This is the piece that was missing. It constructs cameras from config, runs
preflight, starts capture, creates the session directory, assembles
``CaptureController`` / ``CameraRig`` / ``RecordingSessionController``, and
drives the trial state machine from its own thread. Everything above it -- the
HTTP API and the browser UI -- is a view over this object, never a participant
in recording.

Two rules live here rather than in the layer above:

* **The tick loop is server-side.** ``RecordingSessionController.tick()`` is
  what enforces ``max_trial_duration_s`` and polls the pluggable stop predicate
  (invariant 8). The retired Qt screen drove it from a UI timer, which meant
  the runaway-recording guard stopped working the moment the UI went away -- a
  standing tension with invariant 4. A daemon thread here owns it instead, so
  a closed browser cannot disable it.

* **One lock around the controller.** ``RecordingSessionController`` has no
  lock of its own; under Qt it was safe only because one GUI thread called it.
  Here the tick thread and any number of HTTP worker threads reach it at once,
  so every mutation goes through ``self._lock``.
"""

from __future__ import annotations

import logging
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Callable

from acquisition.camera_backend import CameraBackend
from acquisition.camera_registry import build_camera
from acquisition.capture_controller import CaptureController
from acquisition.encoder import resolve_encoder
from acquisition.frame import Frame
from acquisition.preflight import PreflightCheck, PreflightResult, run_preflight_checks
from acquisition.recording_session import CameraRig, RecordingSessionController
from acquisition.trial_state_machine import TrialPhase, TrialStateMachine, TrialToggleAction
from app.config import AppConfig, CameraConfig
from paradigms.paradigm import Paradigm
from paradigms.pdct import PDCTParadigm
from schema.session_metadata import CameraInfo
from schema.trials import TrialRecord
from storage.disk import check_disk_status, measure_bitrate_mb_per_min
from storage.metadata import build_session_metadata
from storage.naming import create_session_directory

logger = logging.getLogger(__name__)

# How long a state() reader waits for the controller lock before falling back
# to the last snapshot. A trial stop holds the lock while it joins writers and
# drains FFmpeg, which is normally milliseconds but is allowed up to 30 s; the
# status feed must not stall for that long, so it reports the last known state
# with `busy` set instead of blocking.
STATE_LOCK_TIMEOUT_S = 0.05

PARADIGMS: dict[str, Callable[[dict[str, str], dict[str, str]], Paradigm]] = {
    "pdct": PDCTParadigm,
}


class SessionError(RuntimeError):
    """The requested lifecycle transition is not valid right now."""


class PreflightFailed(SessionError):
    def __init__(self, failures: tuple[str, ...]) -> None:
        super().__init__("preflight failed: " + "; ".join(failures))
        self.failures = failures


@dataclass(frozen=True)
class CameraState:
    view: str
    serial: str
    type: str
    width: int
    height: int
    pixel_format: str
    frame_rate: float
    dropped_frames: int
    incomplete_frames: int


@dataclass(frozen=True)
class SessionState:
    """Everything a UI needs to render, in one immutable snapshot."""

    phase: str  # setup | idle | recording | closed
    busy: bool  # snapshot is stale: the controller was mid-transition
    session_dir: str | None
    animal_id: str
    project_name: str
    date: str
    experimenter_initials: str
    trial_number: int
    elapsed_s: float
    target_trial_number: int | None
    active_flags: tuple[str, ...]
    dropped_frames: int  # current trial; each trial gets a fresh queue
    completed_trials: int
    encoder: str
    free_gb: float
    estimated_remaining_minutes: float | None
    below_disk_threshold: bool
    last_error: str | None
    cameras: tuple[CameraState, ...] = field(default_factory=tuple)


def git_commit(repo_dir: Path) -> str:
    """The commit this code is running from, for session provenance.

    Never raises: a session recorded from a tarball with no .git is still a
    valid session, and "unknown" is a more useful record than a crash.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    return result.stdout.decode("utf-8", "replace").strip() or "unknown"


class SessionService:
    def __init__(
        self,
        config: AppConfig,
        *,
        mock: bool = False,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = datetime.now,
        tick_interval_s: float = 0.1,
        repo_dir: Path | None = None,
    ) -> None:
        self._config = config
        self._mock = mock
        self._clock = clock
        self._wall_clock = wall_clock
        self._tick_interval_s = tick_interval_s
        self._repo_dir = repo_dir or Path(__file__).resolve().parent.parent

        self._lock = threading.RLock()
        self._cameras: list[tuple[str, CameraBackend]] = []  # (view, backend)
        self._rigs: list[CameraRig] = []
        self._controller: RecordingSessionController | None = None
        self._paradigm: Paradigm | None = None

        self._tick_thread: threading.Thread | None = None
        self._tick_stop = threading.Event()

        self._session_dir: Path | None = None
        self._animal_id = ""
        self._project_name = ""
        self._date = ""
        self._initials = ""
        self._codec = ""
        self._closed = False
        self._last_error: str | None = None
        self._log_handler: logging.Handler | None = None
        self._preflight_by_view: dict[str, PreflightResult] = {}
        self._cached_state: SessionState | None = None

    # -- read-only accessors -------------------------------------------------

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def session_dir(self) -> Path | None:
        return self._session_dir

    @property
    def paradigm(self) -> Paradigm | None:
        return self._paradigm

    def views(self) -> tuple[str, ...]:
        return tuple(c.name for c in self._config.cameras)

    def latest_frame(self, view: str) -> Frame | None:
        """Newest frame from one camera, for preview (invariant 5).

        Deliberately outside ``self._lock``: ``CaptureController`` guards its
        own latest-frame slot, and a preview stream must never be able to
        block a trial stop.
        """
        for rig in self._rigs:
            if rig.view_name == view:
                return rig.controller.latest_frame
        return None

    # -- preflight -----------------------------------------------------------

    def preflight(self) -> PreflightResult:
        """Runs every camera's checks plus the shared FFmpeg/disk ones.

        Cameras are constructed here if they do not exist yet, and left open on
        success -- ``run_preflight_checks`` closes only on failure, and
        ``CaptureController.start()`` calls the idempotent ``open()`` again.

        Does not short-circuit: an experimenter with an animal in hand should
        see everything that needs fixing in one pass.
        """
        with self._lock:
            self._ensure_cameras()
            capture = self._config.capture
            merged: list[PreflightCheck] = []
            self._preflight_by_view = {}

            for camera_config, (view, camera) in zip(self._config.cameras, self._cameras):
                result = run_preflight_checks(
                    camera,
                    camera_config.user_set,
                    Path(self._config.storage.session_root),
                    self._config.storage.min_free_gb,
                    expected_resolution=capture.resolution,
                    expected_fps=float(capture.fps),
                    fps_tolerance=capture.fps_tolerance,
                    expected_nodes=self._config.camera_verify,
                )
                self._preflight_by_view[view] = result
                for check in result.checks:
                    # FFmpeg and free-disk are machine-wide, so every camera's
                    # run produces an identical copy. Deduplicating on the whole
                    # tuple keeps them once while preserving per-camera checks,
                    # which differ by serial or by detail.
                    if check not in merged:
                        merged.append(check)

            failures = tuple(c.describe() for c in merged if not c.passed)
            return PreflightResult(
                passed=not failures, failures=failures, checks=tuple(merged)
            )

    # -- lifecycle -----------------------------------------------------------

    def start_session(
        self,
        animal_id: str,
        project_name: str,
        experimenter_initials: str,
        date: str | None = None,
        *,
        preflight_result: PreflightResult | None = None,
    ) -> Path:
        """Locks the session: validates, preflights, starts capture, creates
        the directory, writes ``session_metadata.json``, and starts ticking.

        The session directory is created only after every camera is streaming,
        so a failed start leaves no half-session on disk to collide with the
        retry.
        """
        with self._lock:
            if self._controller is not None:
                raise SessionError("a session is already running")
            if self._closed:
                raise SessionError("this service has been closed")

            date = date or self._wall_clock().strftime("%Y%m%d")
            self._validate(animal_id, project_name, experimenter_initials, date)

            paradigm_factory = PARADIGMS.get(self._config.active_paradigm)
            if paradigm_factory is None:
                raise SessionError(
                    f"unknown paradigm {self._config.active_paradigm!r}, "
                    f"expected one of {sorted(PARADIGMS)}"
                )

            result = preflight_result or self.preflight()
            if not result.passed:
                raise PreflightFailed(result.failures)

            self._codec = resolve_encoder(
                self._config.encoder.codec, self._config.encoder.fallback_codec
            )

            started: list[CaptureController] = []
            try:
                for view, camera in self._cameras:
                    controller = CaptureController(
                        camera=camera,
                        preroll_duration_s=self._config.capture.preroll_buffer_s,
                        fps=float(self._config.capture.fps),
                    )
                    controller.start()
                    started.append(controller)
                    self._rigs.append(CameraRig(view_name=view, controller=controller))

                session_dir = create_session_directory(
                    Path(self._config.storage.session_root),
                    animal_id,
                    project_name,
                    date,
                    experimenter_initials,
                )
            except Exception:
                for controller in started:
                    _safe_stop(controller)
                self._rigs = []
                raise

            self._session_dir = session_dir
            self._animal_id = animal_id
            self._project_name = project_name
            self._date = date
            self._initials = experimenter_initials
            self._last_error = None

            self._attach_session_log(session_dir)
            self._write_session_metadata()
            self._paradigm = paradigm_factory(
                self._config.keymap, self._config.reason_code_labels
            )

            state_machine = TrialStateMachine(
                config=self._config.trial_timing,
                stop_condition=self._paradigm.default_stop_condition(),
                clock=self._clock,
            )
            self._controller = RecordingSessionController(
                session_dir=session_dir,
                animal_id=animal_id,
                project_name=project_name,
                date=date,
                initials=experimenter_initials,
                config=self._config,
                state_machine=state_machine,
                rigs=self._rigs,
                wall_clock=self._wall_clock,
            )

            self._start_tick_thread()
            logger.info("session started: %s (encoder %s)", session_dir, self._codec)
            return session_dir

    def end_session(self) -> None:
        """Stops any running trial, then the tick loop and every camera.

        Idempotent: ending an already-ended session is not an error, because
        both a UI action and process shutdown reach here.
        """
        with self._lock:
            controller = self._controller
            if controller is not None and controller.phase is TrialPhase.RECORDING:
                try:
                    controller.toggle_trial()
                except Exception as exc:  # noqa: BLE001 -- shutdown must continue
                    logger.exception("stopping the in-flight trial failed")
                    self._last_error = str(exc)

        self._stop_tick_thread()

        with self._lock:
            for rig in self._rigs:
                _safe_stop(rig.controller)
            self._rigs = []
            self._cameras = []
            self._controller = None
            self._closed = True
            self._cached_state = self._build_state(busy=False)
            self._detach_session_log()
            logger.info("session ended")

    # -- trial control -------------------------------------------------------

    def toggle_trial(self) -> TrialToggleAction:
        with self._lock:
            return self._require_controller().toggle_trial()

    def toggle_flag(self, reason_code: str) -> None:
        known = set(self._config.reason_code_labels)
        if reason_code not in known:
            raise SessionError(
                f"unknown reason code {reason_code!r}, expected one of {sorted(known)}"
            )
        with self._lock:
            self._require_controller().toggle_flag(reason_code)

    def set_note(self, trial_number: int, note: str) -> None:
        with self._lock:
            self._require_controller().set_note(trial_number, note)

    def discard_last(self) -> int | None:
        with self._lock:
            return self._require_controller().discard_last()

    def trial_records(self) -> list[TrialRecord]:
        with self._lock:
            controller = self._controller
            return controller.trial_records() if controller is not None else []

    # -- state ---------------------------------------------------------------

    def state(self) -> SessionState:
        """A snapshot for the UI. Never blocks on a slow trial stop.

        If the controller lock is held (a stop joining writers), returns the
        previous snapshot with ``busy=True`` rather than waiting, so the status
        feed stays live through a transition that is allowed to take seconds.
        """
        if self._lock.acquire(timeout=STATE_LOCK_TIMEOUT_S):
            try:
                self._cached_state = self._build_state(busy=False)
            finally:
                self._lock.release()
            return self._cached_state

        if self._cached_state is not None:
            return replace(self._cached_state, busy=True)
        # Contended before anything was ever cached. Report the little that is
        # knowable without the lock rather than blocking a status request.
        return SessionState(
            phase="setup",
            busy=True,
            session_dir=None,
            animal_id="",
            project_name="",
            date="",
            experimenter_initials="",
            trial_number=0,
            elapsed_s=0.0,
            target_trial_number=None,
            active_flags=(),
            dropped_frames=0,
            completed_trials=0,
            encoder=self._codec,
            free_gb=0.0,
            estimated_remaining_minutes=None,
            below_disk_threshold=False,
            last_error=self._last_error,
        )

    # -- internals -----------------------------------------------------------

    def _require_controller(self) -> RecordingSessionController:
        if self._controller is None:
            raise SessionError("no session is running -- call start_session first")
        return self._controller

    def _ensure_cameras(self) -> None:
        if self._cameras:
            return
        for camera_config in self._config.cameras:
            # --mock overrides every camera rather than only the first: a
            # partially-mocked rig would record real and synthetic views into
            # one session, which is worse than either alone.
            resolved = replace(camera_config, type="mock") if self._mock else camera_config
            self._cameras.append(
                (camera_config.name, build_camera(resolved, self._config.capture))
            )

    def _validate(self, animal_id: str, project_name: str, initials: str, date: str) -> None:
        metadata = self._config.metadata
        if not re.match(metadata.animal_id_regex, animal_id or ""):
            raise SessionError(
                f"animal_id {animal_id!r} does not match {metadata.animal_id_regex!r}"
            )
        if project_name not in metadata.projects:
            raise SessionError(
                f"project_name {project_name!r} is not one of {list(metadata.projects)}"
            )
        if initials not in metadata.experimenter_initials:
            raise SessionError(
                f"experimenter_initials {initials!r} is not one of "
                f"{list(metadata.experimenter_initials)}"
            )
        if not re.fullmatch(r"\d{8}", date):
            raise SessionError(f"date {date!r} must be ISO YYYYMMDD")

    def _write_session_metadata(self) -> None:
        assert self._session_dir is not None
        encoder = self._config.encoder
        quality_flag, quality_value = encoder.quality_for(self._codec)
        gop = max(1, round(encoder.keyframe_interval_s * self._config.capture.fps))
        params = (
            f"{quality_flag} {quality_value} -preset {encoder.preset_for(self._codec)} "
            f"-g {gop} -pix_fmt {encoder.pixel_format}"
        )

        cameras = []
        for camera_config, (view, camera) in zip(self._config.cameras, self._cameras):
            per_camera = self._preflight_by_view.get(view)
            cameras.append(
                CameraInfo(
                    serial=camera.serial,
                    user_set_loaded=camera_config.user_set,
                    # Schema v1 carries one boolean per camera. It is True only
                    # when that camera's whole preflight passed, which today is
                    # always the case because start_session blocks otherwise.
                    # Schema v2 replaces this with the per-node results.
                    user_set_verified=bool(per_camera and per_camera.passed),
                )
            )

        metadata = build_session_metadata(
            animal_id=self._animal_id,
            project_name=self._project_name,
            date=self._date,
            experimenter_initials=self._initials,
            session_start_timestamp=self._wall_clock(),
            cameras=tuple(cameras),
            app_version=self._config.version,
            git_commit=git_commit(self._repo_dir),
            ffmpeg_encoder=self._codec,
            ffmpeg_params=params,
            rig_id=self._config.rig_id,
        )
        metadata.write_json(self._session_dir / "session_metadata.json")

    def _build_state(self, *, busy: bool) -> SessionState:
        controller = self._controller
        if self._closed:
            phase = "closed"
        elif controller is None:
            phase = "setup"
        elif controller.phase is TrialPhase.RECORDING:
            phase = "recording"
        else:
            phase = "idle"

        target = controller.target_trial_number() if controller is not None else None
        flags = (
            tuple(sorted(controller.active_flags(target)))
            if controller is not None and target is not None
            else ()
        )
        records = controller.trial_records() if controller is not None else []

        root = self._session_dir or Path(self._config.storage.session_root)
        bitrate = None
        if self._session_dir is not None and records:
            bitrate = measure_bitrate_mb_per_min(
                sorted(self._session_dir.glob("*.mp4")),
                sum(r.duration_s for r in records),
            )
        disk = check_disk_status(root, self._config.storage.min_free_gb, bitrate)

        return SessionState(
            phase=phase,
            busy=busy,
            session_dir=str(self._session_dir) if self._session_dir else None,
            animal_id=self._animal_id,
            project_name=self._project_name,
            date=self._date,
            experimenter_initials=self._initials,
            trial_number=controller.current_trial_number if controller else 0,
            elapsed_s=controller.elapsed_s if controller else 0.0,
            target_trial_number=target,
            active_flags=flags,
            dropped_frames=controller.dropped_frame_count if controller else 0,
            completed_trials=len(records),
            encoder=self._codec,
            free_gb=disk.free_gb,
            estimated_remaining_minutes=disk.estimated_remaining_minutes,
            below_disk_threshold=disk.below_threshold,
            last_error=self._last_error,
            cameras=self._camera_states(),
        )

    def _camera_states(self) -> tuple[CameraState, ...]:
        by_view = {c.name: c for c in self._config.cameras}
        states: list[CameraState] = []
        for rig in self._rigs:
            camera_config: CameraConfig = by_view[rig.view_name]
            width, height = rig.controller.resolution
            states.append(
                CameraState(
                    view=rig.view_name,
                    serial=camera_config.serial,
                    type="mock" if self._mock else camera_config.type,
                    width=width,
                    height=height,
                    pixel_format=rig.controller.pixel_format.value,
                    frame_rate=float(self._config.capture.fps),
                    dropped_frames=(
                        rig.writer_queue.dropped_count if rig.writer_queue else 0
                    ),
                    incomplete_frames=rig.controller.incomplete_frame_count,
                )
            )
        return tuple(states)

    # -- tick loop -----------------------------------------------------------

    def _start_tick_thread(self) -> None:
        self._tick_stop.clear()
        self._tick_thread = threading.Thread(
            target=self._tick_loop, name="SessionTick", daemon=True
        )
        self._tick_thread.start()

    def _stop_tick_thread(self) -> None:
        self._tick_stop.set()
        thread, self._tick_thread = self._tick_thread, None
        if thread is not None:
            thread.join(timeout=5.0)

    def _tick_loop(self) -> None:
        """Drives max-duration auto-stop and the pluggable stop predicate.

        Swallows every exception on purpose. ``tick()`` finalizes a trial, so
        it can raise a WriterError exactly as a manual stop can -- and a dead
        tick thread would silently disable the runaway-recording guard for the
        rest of the session, which is the failure this thread exists to
        prevent. The error is recorded for the UI instead.
        """
        while not self._tick_stop.wait(self._tick_interval_s):
            try:
                with self._lock:
                    if self._controller is not None:
                        self._controller.tick()
            except Exception as exc:  # noqa: BLE001 -- see docstring
                logger.exception("tick failed")
                self._last_error = str(exc)

    # -- per-session logging -------------------------------------------------

    def _attach_session_log(self, session_dir: Path) -> None:
        handler = logging.FileHandler(session_dir / "session.log", encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logging.getLogger().addHandler(handler)
        self._log_handler = handler

    def _detach_session_log(self) -> None:
        handler, self._log_handler = self._log_handler, None
        if handler is not None:
            logging.getLogger().removeHandler(handler)
            handler.close()


def _safe_stop(controller: CaptureController) -> None:
    """Stopping one camera must not prevent stopping the rest."""
    try:
        controller.stop()
    except Exception:  # noqa: BLE001 -- teardown is best-effort
        logger.exception("stopping capture failed")

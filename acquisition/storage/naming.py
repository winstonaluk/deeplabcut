"""Session directory and trial filename generation.

See acquisition/CLAUDE.md "Files and naming":

    <session_root>/<animal_id>_<project_name>_<date>_<initials>/
        session_metadata.json
        trials.csv
        <animal_id>_<project_name>_<date>_<initials>_<HHMM>_t001.mp4
        <animal_id>_<project_name>_<date>_<initials>_<HHMM>_t001_timestamps.csv

``t<NNN>`` alone guarantees uniqueness; ``HHMM`` is informational. The
optional ``<view>`` token is config-toggleable and off by default.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class SessionDirectoryExistsError(FileExistsError):
    """Refusing to overwrite an existing session directory (never allowed)."""


def session_dir_name(animal_id: str, project_name: str, date: str, initials: str) -> str:
    return f"{animal_id}_{project_name}_{date}_{initials}"


def session_dir_path(
    session_root: Path, animal_id: str, project_name: str, date: str, initials: str
) -> Path:
    return Path(session_root) / session_dir_name(animal_id, project_name, date, initials)


def create_session_directory(
    session_root: Path, animal_id: str, project_name: str, date: str, initials: str
) -> Path:
    """Creates and returns the session directory. Never overwrites."""
    path = session_dir_path(session_root, animal_id, project_name, date, initials)
    if path.exists():
        raise SessionDirectoryExistsError(f"session directory already exists: {path}")
    path.mkdir(parents=True)
    return path


def _trial_basename(
    animal_id: str,
    project_name: str,
    date: str,
    initials: str,
    trial_start: datetime,
    trial_number: int,
    view: str | None = None,
    include_view_token: bool = False,
) -> str:
    if trial_number < 1:
        raise ValueError(f"trial_number must be >= 1, got {trial_number}")
    parts = [animal_id, project_name, date, initials]
    if include_view_token:
        if not view:
            raise ValueError("view is required when include_view_token is True")
        parts.append(view)
    parts.append(trial_start.strftime("%H%M"))
    parts.append(f"t{trial_number:03d}")
    return "_".join(parts)


def trial_video_filename(
    animal_id: str,
    project_name: str,
    date: str,
    initials: str,
    trial_start: datetime,
    trial_number: int,
    view: str | None = None,
    include_view_token: bool = False,
) -> str:
    base = _trial_basename(
        animal_id, project_name, date, initials, trial_start, trial_number, view, include_view_token
    )
    return f"{base}.mp4"


def trial_timestamps_filename(
    animal_id: str,
    project_name: str,
    date: str,
    initials: str,
    trial_start: datetime,
    trial_number: int,
    view: str | None = None,
    include_view_token: bool = False,
) -> str:
    base = _trial_basename(
        animal_id, project_name, date, initials, trial_start, trial_number, view, include_view_token
    )
    return f"{base}_timestamps.csv"

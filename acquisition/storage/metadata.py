"""Assembles SessionMetadata at session lock (A5) from config + runtime info."""

from __future__ import annotations

from datetime import datetime

from schema.session_metadata import CameraInfo, SessionMetadata


def build_session_metadata(
    animal_id: str,
    project_name: str,
    date: str,
    experimenter_initials: str,
    session_start_timestamp: datetime,
    cameras: tuple[CameraInfo, ...],
    app_version: str,
    git_commit: str,
    ffmpeg_encoder: str,
    ffmpeg_params: str,
    rig_id: str,
) -> SessionMetadata:
    return SessionMetadata(
        animal_id=animal_id,
        project_name=project_name,
        date=date,
        experimenter_initials=experimenter_initials,
        session_start_timestamp=session_start_timestamp.isoformat(),
        cameras=cameras,
        app_version=app_version,
        git_commit=git_commit,
        ffmpeg_encoder=ffmpeg_encoder,
        ffmpeg_params=ffmpeg_params,
        rig_id=rig_id,
    )

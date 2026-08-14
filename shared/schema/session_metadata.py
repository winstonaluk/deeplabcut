"""``session_metadata.json`` — the session-level record.

Written once by the acquisition app when a session locks on start; read by
analysis stage 0 (``build_manifest``) as part of the manifest spine. See the
"Cross-repo contract" section of both apps' CLAUDE.md: this is the interface,
not an incidental format, and any field change is a schema_version bump.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from schema.errors import SchemaValidationError, SchemaVersionError

SESSION_METADATA_SCHEMA_VERSION = 1

_DATE_RE = re.compile(r"^\d{8}$")


@dataclass(frozen=True)
class CameraInfo:
    """One camera's identity and onboard-settings verification for a session."""

    serial: str
    user_set_loaded: str
    user_set_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "CameraInfo":
        missing = {"serial", "user_set_loaded", "user_set_verified"} - d.keys()
        if missing:
            raise SchemaValidationError(f"CameraInfo missing fields: {sorted(missing)}")
        return CameraInfo(
            serial=str(d["serial"]),
            user_set_loaded=str(d["user_set_loaded"]),
            user_set_verified=bool(d["user_set_verified"]),
        )


@dataclass(frozen=True)
class SessionMetadata:
    """One row: everything captured once per session, at lock time."""

    animal_id: str
    project_name: str
    date: str  # ISO YYYYMMDD
    experimenter_initials: str
    session_start_timestamp: str  # ISO 8601
    cameras: tuple[CameraInfo, ...]
    app_version: str
    git_commit: str
    ffmpeg_encoder: str
    ffmpeg_params: str
    rig_id: str
    schema_version: int = field(default=SESSION_METADATA_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["cameras"] = [c.to_dict() for c in self.cameras]
        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "SessionMetadata":
        found_version = d.get("schema_version")
        if found_version is None:
            raise SchemaValidationError("session_metadata: missing schema_version")
        if int(found_version) != SESSION_METADATA_SCHEMA_VERSION:
            raise SchemaVersionError(
                "session_metadata.json", int(found_version), SESSION_METADATA_SCHEMA_VERSION
            )

        required = {
            "animal_id",
            "project_name",
            "date",
            "experimenter_initials",
            "session_start_timestamp",
            "cameras",
            "app_version",
            "git_commit",
            "ffmpeg_encoder",
            "ffmpeg_params",
            "rig_id",
        }
        missing = required - d.keys()
        if missing:
            raise SchemaValidationError(f"session_metadata: missing fields: {sorted(missing)}")

        if not _DATE_RE.match(str(d["date"])):
            raise SchemaValidationError(
                f"session_metadata: date must be YYYYMMDD, got {d['date']!r}"
            )
        if not d["animal_id"]:
            raise SchemaValidationError("session_metadata: animal_id must be non-empty")
        cameras = d["cameras"]
        if not isinstance(cameras, list) or not cameras:
            raise SchemaValidationError("session_metadata: cameras must be a non-empty list")

        return SessionMetadata(
            animal_id=str(d["animal_id"]),
            project_name=str(d["project_name"]),
            date=str(d["date"]),
            experimenter_initials=str(d["experimenter_initials"]),
            session_start_timestamp=str(d["session_start_timestamp"]),
            cameras=tuple(CameraInfo.from_dict(c) for c in cameras),
            app_version=str(d["app_version"]),
            git_commit=str(d["git_commit"]),
            ffmpeg_encoder=str(d["ffmpeg_encoder"]),
            ffmpeg_params=str(d["ffmpeg_params"]),
            rig_id=str(d["rig_id"]),
            schema_version=int(found_version),
        )

    def write_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def read_json(path: Path) -> "SessionMetadata":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return SessionMetadata.from_dict(d)

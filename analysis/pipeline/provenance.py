"""Hashing utilities and the .provenance.json sidecar writer/reader.

Every artifact carries provenance (invariant 5): input artifact hashes,
config hash, code commit, DLC snapshot ID, stage version, timestamp.
Resumability (invariant 4) is implemented on top of this: a stage skips
recomputing an artifact when a fresh provenance record would exactly match
the one already on disk.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_config(config_dict: dict[str, Any], algorithm: str = "sha256") -> str:
    """Deterministic hash of a config mapping. Callers pass a plain dict
    (e.g. dataclasses.asdict(config) or a specific stage's sub-config) --
    this function doesn't know about AnalysisConfig's shape."""
    canonical = json.dumps(config_dict, sort_keys=True, default=str)
    return hashlib.new(algorithm, canonical.encode("utf-8")).hexdigest()


def current_code_commit(repo_root: Path | None = None) -> str:
    """Short git commit hash of HEAD. Returns "unknown" outside a git repo
    rather than raising -- provenance should degrade gracefully, not block
    a run just because it's not in a git checkout."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, timeout=5, check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


@dataclass(frozen=True)
class Provenance:
    stage_name: str
    stage_version: str
    input_hashes: dict[str, str]  # input artifact name -> hash
    config_hash: str
    code_commit: str
    timestamp: str  # ISO 8601 UTC
    dlc_snapshot_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Provenance":
        return Provenance(
            stage_name=d["stage_name"],
            stage_version=d["stage_version"],
            input_hashes=dict(d["input_hashes"]),
            config_hash=d["config_hash"],
            code_commit=d["code_commit"],
            timestamp=d["timestamp"],
            dlc_snapshot_id=d.get("dlc_snapshot_id"),
        )

    def write_json(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def read_json(path: Path) -> "Provenance":
        return Provenance.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def matches_inputs(self, input_hashes: dict[str, str], config_hash: str) -> bool:
        """True if a rerun with these inputs/config would produce identical
        provenance -- the resumability check a stage runs before doing work
        (invariant 4: skip when outputs exist and input+config hashes match)."""
        return self.input_hashes == input_hashes and self.config_hash == config_hash


def make_provenance(
    stage_name: str,
    stage_version: str,
    input_hashes: dict[str, str],
    config_hash: str,
    dlc_snapshot_id: str | None = None,
    repo_root: Path | None = None,
    now: datetime | None = None,
) -> Provenance:
    now = now or datetime.now(timezone.utc)
    return Provenance(
        stage_name=stage_name,
        stage_version=stage_version,
        input_hashes=input_hashes,
        config_hash=config_hash,
        code_commit=current_code_commit(repo_root),
        timestamp=now.isoformat(),
        dlc_snapshot_id=dlc_snapshot_id,
    )


def provenance_path_for(artifact_path: Path) -> Path:
    """The sidecar path for a given artifact: foo.parquet -> foo.parquet.provenance.json."""
    return Path(str(artifact_path) + ".provenance.json")

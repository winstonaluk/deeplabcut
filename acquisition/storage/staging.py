"""Stage completed sessions for transfer, with checksum verification, and
purge only after an explicit confirmation.

The remote is a generic mounted filesystem path -- works for an rsync or
robocopy target, a network share, an external drive. Never anything
institution-specific (acquisition/CLAUDE.md "Storage"). Actual network
transfer is external to this app; staging just gets a verified copy ready
for it.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StagingResult:
    session_dir: Path
    staged_dir: Path
    checksums: dict[str, str]  # path relative to the session dir -> hex digest
    verified: bool


def _hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checksum_all(root: Path, algorithm: str) -> dict[str, str]:
    return {
        str(path.relative_to(root)): _hash_file(path, algorithm)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def stage_session(session_dir: Path, staging_root: Path, algorithm: str = "sha256") -> StagingResult:
    """Copies the session directory into staging_root and verifies every
    file's checksum matches post-copy. Never overwrites an existing staged
    copy of the same session."""
    session_dir = Path(session_dir)
    staged_dir = Path(staging_root) / session_dir.name

    if staged_dir.exists():
        raise FileExistsError(f"staging destination already exists: {staged_dir}")

    source_checksums = _checksum_all(session_dir, algorithm)
    shutil.copytree(session_dir, staged_dir)
    staged_checksums = _checksum_all(staged_dir, algorithm)

    return StagingResult(
        session_dir=session_dir,
        staged_dir=staged_dir,
        checksums=staged_checksums,
        verified=(source_checksums == staged_checksums),
    )


def purge_session(session_dir: Path, confirm: bool) -> None:
    """Deletes the local session directory. Requires explicit confirm=True --
    a verified stage_session() result is not itself permission to purge; the
    caller must still ask (acquisition/CLAUDE.md "Purge-after-verified-transfer
    requires explicit confirmation")."""
    if not confirm:
        raise ValueError("purge_session requires explicit confirm=True")
    shutil.rmtree(session_dir)

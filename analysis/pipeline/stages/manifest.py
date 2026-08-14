"""Stage 0: build_manifest.

Scans archive session directories, validates each session's
session_metadata.json / trials.csv against shared/schema/ (by using its
readers directly -- never redefining the schema locally), and emits
manifest.parquet: the spine every later stage queries instead of crawling
the filesystem.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.contracts import ManifestRow
from pipeline.provenance import Provenance, hash_file, make_provenance, provenance_path_for
from schema.session_metadata import SessionMetadata
from schema.trials import read_trials_csv

STAGE_VERSION = "1.0.0"


def trial_uid(animal_id: str, project_name: str, date: str, initials: str, view: str, trial_number: int) -> str:
    """Stable deterministic string -- the primary join key everywhere
    (analysis/CLAUDE.md glossary "Trial UID")."""
    return f"{animal_id}_{project_name}_{date}_{initials}_{view}_t{trial_number:03d}"


def _find_trial_file(session_dir: Path, trial_number: int, suffix: str, view: str | None) -> Path | None:
    """Locates this trial's file by its t<NNN> token, which alone
    guarantees uniqueness (acquisition/CLAUDE.md "Files and naming"). If a
    view token is present in the filenames (multi-camera sessions), prefer
    the match for this view; a single-camera session has no view token at
    all, so falls back to matching on the trial token alone.
    """
    token = f"_t{trial_number:03d}"
    candidates = [
        p for p in session_dir.iterdir()
        if p.is_file() and p.name.endswith(suffix) and token in p.name[: -len(suffix)]
    ]
    if view:
        view_matches = [p for p in candidates if f"_{view}_" in p.name]
        if view_matches:
            candidates = view_matches
    if len(candidates) > 1:
        raise ValueError(f"ambiguous file match for trial {trial_number} in {session_dir}: {candidates}")
    return candidates[0] if candidates else None


def scan_session_directory(session_dir: Path, view: str) -> list[ManifestRow]:
    """One session's trials, for one view."""
    meta = SessionMetadata.read_json(session_dir / "session_metadata.json")
    _, trials = read_trials_csv(session_dir / "trials.csv")

    rows = []
    for trial in trials:
        video_path = _find_trial_file(session_dir, trial.trial_number, ".mp4", view)
        timestamps_path = _find_trial_file(session_dir, trial.trial_number, "_timestamps.csv", view)
        rows.append(
            ManifestRow(
                trial_uid=trial_uid(
                    meta.animal_id, meta.project_name, meta.date, meta.experimenter_initials,
                    view, trial.trial_number,
                ),
                animal_id=meta.animal_id,
                project_name=meta.project_name,
                date=meta.date,
                initials=meta.experimenter_initials,
                view=view,
                trial_number=trial.trial_number,
                video_path=str(video_path) if video_path else "",
                timestamps_path=str(timestamps_path) if timestamps_path else "",
                duration_s=trial.duration_s,
                n_frames=trial.n_frames,
                dropped_frames=trial.dropped_frames,
                achieved_fps=trial.achieved_fps,
                flags=trial.flags,
                auto_flags=trial.auto_flags,
            )
        )
    return rows


def manifest_rows_to_dataframe(rows: list[ManifestRow]) -> pd.DataFrame:
    """frozenset fields become sorted lists -- parquet has no set type, and
    a deterministic order keeps the parquet bytes (and therefore its hash)
    stable across runs with identical content."""
    return pd.DataFrame(
        {
            "trial_uid": r.trial_uid,
            "animal_id": r.animal_id,
            "project_name": r.project_name,
            "date": r.date,
            "initials": r.initials,
            "view": r.view,
            "trial_number": r.trial_number,
            "video_path": r.video_path,
            "timestamps_path": r.timestamps_path,
            "duration_s": r.duration_s,
            "n_frames": r.n_frames,
            "dropped_frames": r.dropped_frames,
            "achieved_fps": r.achieved_fps,
            "flags": sorted(r.flags),
            "auto_flags": sorted(r.auto_flags),
        }
        for r in rows
    )


def dataframe_to_manifest_rows(df: pd.DataFrame) -> list[ManifestRow]:
    return [
        ManifestRow(
            trial_uid=row.trial_uid, animal_id=row.animal_id, project_name=row.project_name,
            date=row.date, initials=row.initials, view=row.view, trial_number=int(row.trial_number),
            video_path=row.video_path, timestamps_path=row.timestamps_path,
            duration_s=float(row.duration_s), n_frames=int(row.n_frames),
            dropped_frames=int(row.dropped_frames), achieved_fps=float(row.achieved_fps),
            flags=frozenset(row.flags), auto_flags=frozenset(row.auto_flags),
        )
        for row in df.itertuples()
    ]


def build_manifest(archive_root: Path, views: tuple[str, ...]) -> pd.DataFrame:
    """Scans every session directory under archive_root. A directory counts
    as a session iff it has a session_metadata.json -- anything else under
    archive_root is ignored rather than erroring, since the archive may
    hold other files alongside session directories."""
    archive_root = Path(archive_root)
    rows: list[ManifestRow] = []
    for session_dir in sorted(p for p in archive_root.iterdir() if p.is_dir()):
        if not (session_dir / "session_metadata.json").exists():
            continue
        for view in views:
            rows.extend(scan_session_directory(session_dir, view))
    return manifest_rows_to_dataframe(rows)


def compute_manifest_input_hashes(archive_root: Path) -> dict[str, str]:
    """One hash per session's session_metadata.json/trials.csv -- if any
    session's data changes, this changes, and a rerun regenerates the
    manifest instead of silently reusing a stale one (invariant 4)."""
    archive_root = Path(archive_root)
    hashes: dict[str, str] = {}
    for session_dir in sorted(p for p in archive_root.iterdir() if p.is_dir()):
        meta_path = session_dir / "session_metadata.json"
        trials_path = session_dir / "trials.csv"
        if meta_path.exists():
            hashes[f"{session_dir.name}/session_metadata.json"] = hash_file(meta_path)
        if trials_path.exists():
            hashes[f"{session_dir.name}/trials.csv"] = hash_file(trials_path)
    return hashes


def write_manifest(archive_root: Path, views: tuple[str, ...], output_path: Path, config_hash: str) -> Provenance:
    df = build_manifest(archive_root, views)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    prov = make_provenance(
        stage_name="build_manifest",
        stage_version=STAGE_VERSION,
        input_hashes=compute_manifest_input_hashes(archive_root),
        config_hash=config_hash,
    )
    prov.write_json(provenance_path_for(output_path))
    return prov

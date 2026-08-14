"""Stage 1: qc_gate.

All rules are config-driven thresholds (invariant 6). Never drops rows
(invariant 3) -- every manifest row survives into manifest_qc.parquet with
an added included/exclusion_reason pair; downstream stages filter on
included rather than the row simply being absent.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.config import QCConfig
from pipeline.contracts import ManifestRow, QCRow
from pipeline.provenance import Provenance, hash_file, make_provenance, provenance_path_for
from pipeline.stages.manifest import dataframe_to_manifest_rows

STAGE_VERSION = "1.0.0"


def evaluate_trial(row: ManifestRow, config: QCConfig) -> tuple[bool, str]:
    """Returns (included, exclusion_reason). Every failing rule is recorded
    in exclusion_reason (semicolon-joined), not just the first one, so a
    reviewer sees the whole picture at once."""
    reasons: list[str] = []

    if row.flags:
        reasons.append(f"experimenter flags: {','.join(sorted(row.flags))}")

    dropped_rate = (row.dropped_frames / row.n_frames) if row.n_frames > 0 else 1.0
    if dropped_rate > config.max_dropped_frame_rate:
        reasons.append(
            f"dropped_frame_rate {dropped_rate:.4f} > {config.max_dropped_frame_rate}"
        )

    if not (config.min_duration_s <= row.duration_s <= config.max_duration_s):
        reasons.append(
            f"duration_s {row.duration_s} outside [{config.min_duration_s}, {config.max_duration_s}]"
        )

    fps_deviation = abs(row.achieved_fps - config.nominal_fps)
    if fps_deviation > config.max_fps_deviation:
        reasons.append(
            f"achieved_fps {row.achieved_fps} deviates from nominal {config.nominal_fps} "
            f"by {fps_deviation:.2f} > {config.max_fps_deviation}"
        )

    return (len(reasons) == 0, "; ".join(reasons))


def qc_gate(manifest_df: pd.DataFrame, config: QCConfig) -> pd.DataFrame:
    qc_rows = []
    for row in dataframe_to_manifest_rows(manifest_df):
        included, exclusion_reason = evaluate_trial(row, config)
        qc_rows.append(
            QCRow(
                trial_uid=row.trial_uid, animal_id=row.animal_id, project_name=row.project_name,
                date=row.date, initials=row.initials, view=row.view, trial_number=row.trial_number,
                video_path=row.video_path, timestamps_path=row.timestamps_path,
                duration_s=row.duration_s, n_frames=row.n_frames, dropped_frames=row.dropped_frames,
                achieved_fps=row.achieved_fps, flags=row.flags, auto_flags=row.auto_flags,
                included=included, exclusion_reason=exclusion_reason,
            )
        )
    return qc_rows_to_dataframe(qc_rows)


def qc_rows_to_dataframe(rows: list[QCRow]) -> pd.DataFrame:
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
            "included": r.included,
            "exclusion_reason": r.exclusion_reason,
        }
        for r in rows
    )


def write_qc_gate(manifest_path: Path, output_path: Path, config: QCConfig, config_hash: str) -> Provenance:
    manifest_df = pd.read_parquet(manifest_path)
    qc_df = qc_gate(manifest_df, config)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    qc_df.to_parquet(output_path, index=False)

    prov = make_provenance(
        stage_name="qc_gate",
        stage_version=STAGE_VERSION,
        input_hashes={"manifest.parquet": hash_file(manifest_path)},
        config_hash=config_hash,
    )
    prov.write_json(provenance_path_for(output_path))
    return prov

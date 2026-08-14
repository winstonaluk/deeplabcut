"""Stage 7: infer. Batch pose inference via deeplabcut.analyze_videos().

Requires DeepLabCut installed, a trained snapshot, and (per analysis/
CLAUDE.md's hardware notes) the RTX 5070 Ti with the cu128 PyTorch build --
not buildable unattended.

Resumability is real and tested here even though the DLC call itself is a
stub: skip trials whose pose output already exists with a matching
snapshot ID *and* config hash (analysis/CLAUDE.md stage 7 contract) --
either changing invalidates the cached pose output. This is exactly the
per-stage caching logic invariant 4 asks for, and it doesn't need DLC or a
GPU to prove correct.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.contracts import PoseIndexRow


def pose_index_rows_to_dataframe(rows: list[PoseIndexRow]) -> pd.DataFrame:
    return pd.DataFrame(
        {"trial_uid": r.trial_uid, "pose_path": r.pose_path, "snapshot_id": r.snapshot_id, "config_hash": r.config_hash}
        for r in rows
    )


def dataframe_to_pose_index_rows(df: pd.DataFrame) -> list[PoseIndexRow]:
    return [
        PoseIndexRow(trial_uid=row.trial_uid, pose_path=row.pose_path, snapshot_id=row.snapshot_id, config_hash=row.config_hash)
        for row in df.itertuples()
    ]


def trials_needing_inference(
    manifest_qc_df: pd.DataFrame,
    existing_pose_index_df: pd.DataFrame | None,
    snapshot_id: str,
    config_hash: str,
) -> list[str]:
    """A trial_uid needs (re-)inference unless the pose index already has a
    row for it with both the current snapshot_id and config_hash. Excluded
    (included=False) manifest rows are never selected regardless of pose
    index state -- QC gate's exclusion is respected here too."""
    included = list(manifest_qc_df.loc[manifest_qc_df["included"], "trial_uid"])
    if existing_pose_index_df is None or existing_pose_index_df.empty:
        return included

    done = {
        row.trial_uid
        for row in existing_pose_index_df.itertuples()
        if row.snapshot_id == snapshot_id and row.config_hash == config_hash
    }
    return [uid for uid in included if uid not in done]


def infer_trial(
    trial_uid: str, video_path: Path, snapshot_id: str, local_cache_root: Path
) -> PoseIndexRow:
    """Pull video from archive -> local cache -> deeplabcut.analyze_videos()
    -> write pose .h5 -> verify -> delete local copy (analysis/CLAUDE.md
    "Data tiering" -- video is huge, everything derived from it is small).
    Requires DeepLabCut installed and a trained snapshot; not buildable
    unattended."""
    raise NotImplementedError("requires DeepLabCut installed and a trained snapshot")

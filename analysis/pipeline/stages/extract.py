"""Stage 3: extract_frames. Frame extraction for DLC labeling.

Round 1 (motion/ROI prefilter + k-means) needs real video decoding; round 2
(DLC extract_outlier_frames, uncertain/jump modes) needs a trained model --
neither buildable unattended. This module defines the frame-manifest
contract and the resumability check (which trials still need extraction)
as pure, testable functions; the actual frame-reading/k-means/DLC calls are
thin wrappers with NotImplementedError bodies.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.contracts import FrameManifestRow


def frame_manifest_rows_to_dataframe(rows: list[FrameManifestRow]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trial_uid": r.trial_uid,
            "frame_index": r.frame_index,
            "extraction_method": r.extraction_method,
            "extraction_round": r.extraction_round,
            "image_path": r.image_path,
        }
        for r in rows
    )


def dataframe_to_frame_manifest_rows(df: pd.DataFrame) -> list[FrameManifestRow]:
    return [
        FrameManifestRow(
            trial_uid=row.trial_uid, frame_index=int(row.frame_index),
            extraction_method=row.extraction_method, extraction_round=int(row.extraction_round),
            image_path=row.image_path,
        )
        for row in df.itertuples()
    ]


def trials_needing_extraction(
    manifest_qc_df: pd.DataFrame, existing_frames_df: pd.DataFrame | None
) -> list[str]:
    """Resumability: included trial_uids with no row yet in the frames
    manifest. Pure and testable with fake DataFrames -- no video required.
    """
    included = list(manifest_qc_df.loc[manifest_qc_df["included"], "trial_uid"])
    if existing_frames_df is None or existing_frames_df.empty:
        return included
    already_done = set(existing_frames_df["trial_uid"])
    return [uid for uid in included if uid not in already_done]


def extract_frames_for_trial(
    trial_uid: str, video_path: Path, round_number: int
) -> list[FrameManifestRow]:
    """Round 1: motion/ROI prefilter, then k-means (blind k-means alone
    wastes budget on uninformative/occluded frames). Round 2: DLC
    extract_outlier_frames once a first model exists. Requires real video
    decoding (round 1) or a trained DLC model (round 2); neither available
    unattended."""
    raise NotImplementedError(
        "requires real video decoding (round 1) or a trained DLC model (round 2)"
    )

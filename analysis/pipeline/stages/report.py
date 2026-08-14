"""Stage 9: report.

Group-level aggregation and table generation from trial_summary.parquet and
kinematics_long.parquet only -- no GPU, no network storage, no video
(analysis/CLAUDE.md stage 9 contract). Figures are optional and not built
here; this module produces the tables a figure would be drawn from.

Grouping is limited to what trial_summary/kinematics_long actually carry
(primary_keypoint) plus an overall summary -- animal/project-level grouping
would need fields that live only in the manifest, which stage 9's contract
excludes from its inputs. See QUESTIONS.md b5-report-stage-cannot-group-by-animal.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.provenance import Provenance, hash_file, make_provenance, provenance_path_for

STAGE_VERSION = "1.0.0"


def load_trial_summary(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_kinematics_long(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def _descent_summary_stats(df: pd.DataFrame) -> dict[str, float]:
    detected = df.dropna(subset=["descent_duration_s"])
    return {
        "n_trials": int(len(df)),
        "n_descent_detected": int(len(detected)),
        "fraction_descent_detected": float(len(detected) / len(df)) if len(df) else float("nan"),
        "mean_descent_duration_s": float(detected["descent_duration_s"].mean()) if len(detected) else float("nan"),
        "median_descent_duration_s": float(detected["descent_duration_s"].median()) if len(detected) else float("nan"),
        "mean_velocity_mm_s": float(df["mean_velocity_mm_s"].dropna().mean()) if df["mean_velocity_mm_s"].notna().any() else float("nan"),
        "mean_occlusion_fraction": float(df["occlusion_fraction"].mean()) if len(df) else float("nan"),
        "n_drift_flagged": int(df["pole_landmark_drift_flagged"].sum()),
    }


def aggregate_overall(trial_summary_df: pd.DataFrame) -> dict[str, float]:
    return _descent_summary_stats(trial_summary_df)


def aggregate_by_keypoint(trial_summary_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keypoint, group in trial_summary_df.groupby("primary_keypoint"):
        stats = _descent_summary_stats(group)
        stats["primary_keypoint"] = keypoint
        rows.append(stats)
    return pd.DataFrame(rows)


def aggregate_velocity_by_height(
    kinematics_long_df: pd.DataFrame, n_bins: int = 10
) -> pd.DataFrame:
    """Pools velocity samples across every trial/frame present, binned by
    height_fraction. Safe to pool across trials because velocity_mm_s is
    already a per-frame derivative computed within each trial (stage 8),
    never re-derived across trial boundaries here."""
    df = kinematics_long_df.dropna(subset=["height_fraction", "velocity_mm_s"])
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(df["height_fraction"], bins) - 1, 0, n_bins - 1)

    rows = []
    for b in range(n_bins):
        mask = bin_idx == b
        vals = df.loc[mask, "velocity_mm_s"]
        rows.append(
            {
                "height_bin_low": bins[b],
                "height_bin_high": bins[b + 1],
                "mean_velocity_mm_s": float(vals.mean()) if len(vals) else float("nan"),
                "n_samples": int(len(vals)),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    trial_summary_path: Path,
    kinematics_long_path: Path,
    output_dir: Path,
    config_hash: str,
) -> Provenance:
    trial_summary_df = load_trial_summary(trial_summary_path)
    kinematics_long_df = load_kinematics_long(kinematics_long_path)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    overall = aggregate_overall(trial_summary_df)
    pd.DataFrame([overall]).to_parquet(output_dir / "summary_overall.parquet", index=False)
    aggregate_by_keypoint(trial_summary_df).to_parquet(output_dir / "summary_by_keypoint.parquet", index=False)
    aggregate_velocity_by_height(kinematics_long_df).to_parquet(
        output_dir / "velocity_by_height.parquet", index=False
    )

    prov = make_provenance(
        stage_name="report",
        stage_version=STAGE_VERSION,
        input_hashes={
            "trial_summary.parquet": hash_file(trial_summary_path),
            "kinematics_long.parquet": hash_file(kinematics_long_path),
        },
        config_hash=config_hash,
    )
    prov.write_json(provenance_path_for(output_dir / "summary_overall.parquet"))
    return prov

"""Stage 6: evaluate. Train/test pixel error via deeplabcut.evaluate_network().

Requires DeepLabCut installed and a trained snapshot -- not buildable
unattended. The gate check itself (batch inference must not run if error
exceeds the config threshold) is pure and tested; the DLC call is a thin
wrapper.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.contracts import EvaluationReport


def passes_gate(overall_pixel_error: float, max_pixel_error: float) -> bool:
    """Batch inference (stage 7) must not run if error exceeds the config
    threshold (analysis/CLAUDE.md stage 6 "Gate"). Pure, testable without DLC."""
    return overall_pixel_error <= max_pixel_error


def build_evaluation_report(
    overall_pixel_error: float,
    per_keypoint_pixel_error: dict[str, float],
    pcutoff_sweep: dict[float, float],
    max_pixel_error: float,
) -> EvaluationReport:
    return EvaluationReport(
        overall_pixel_error=overall_pixel_error,
        per_keypoint_pixel_error=per_keypoint_pixel_error,
        pcutoff_sweep=pcutoff_sweep,
        passes_gate=passes_gate(overall_pixel_error, max_pixel_error),
    )


def evaluate(dlc_project_path: Path, snapshot_id: str) -> EvaluationReport:
    """deeplabcut.evaluate_network() + a pcutoff sweep + manual validation
    on randomly sampled held-out frames (RpiBeh methodology). Pole landmarks
    should show near-zero error; a high error there means the coordinate
    frame is unreliable. Requires DeepLabCut installed and a trained
    snapshot -- neither available unattended."""
    raise NotImplementedError("requires DeepLabCut installed and a trained snapshot")

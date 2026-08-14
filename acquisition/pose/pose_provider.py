"""PoseProvider protocol: the seam for DLC-Live, not implemented yet.

Any real-time pose inference is out of scope for this app (see
acquisition/CLAUDE.md "Out of scope"). This module exists so the recording
pipeline, TriggerService, and a future pose-driven TrialStopCondition can be
written against a stable interface today.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from acquisition.frame import Frame


@dataclass(frozen=True)
class PoseEstimate:
    """One frame's inferred keypoints. Shape TBD by the DLC-Live integration;
    placeholder fields only until that work begins.
    """

    frame_id: int
    keypoints: dict[str, tuple[float, float, float]]  # name -> (x, y, likelihood)


class PoseProvider(Protocol):
    def infer(self, frame: Frame) -> PoseEstimate | None:
        """Returns a pose estimate for this frame, or None if unavailable."""
        ...

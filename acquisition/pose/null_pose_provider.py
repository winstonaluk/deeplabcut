"""The only PoseProvider this app ships. Real inference is out of scope."""

from __future__ import annotations

from acquisition.frame import Frame
from pose.pose_provider import PoseEstimate


class NullPoseProvider:
    """Always returns None. Satisfies PoseProvider structurally so callers
    (e.g. a future TriggerService wiring) never special-case "no pose"."""

    def infer(self, frame: Frame) -> PoseEstimate | None:
        return None

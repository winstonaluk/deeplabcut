"""Electrophysiology trigger hook. Out of scope -- no-op by design.

Kept as a real call site (rather than omitted entirely) so a future trigger
implementation has one obvious place to attach, without touching the
recording pipeline that calls it.
"""

from __future__ import annotations

from pose.pose_provider import PoseEstimate


class TriggerService:
    def on_pose(self, pose: PoseEstimate | None) -> None:
        """No-op. Electrophysiology trigger logic is out of scope for this app."""
        return None

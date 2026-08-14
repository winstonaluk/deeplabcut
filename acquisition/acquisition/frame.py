"""The unit of data a CameraBackend produces per exposure."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Frame:
    """One captured image plus its camera-supplied chunk data.

    ``hardware_timestamp_ns`` and ``frame_id`` come from the camera's onboard
    chunk data, never host wall-clock arrival time (acquisition/CLAUDE.md
    invariant 6).
    """

    image: np.ndarray
    hardware_timestamp_ns: int
    frame_id: int

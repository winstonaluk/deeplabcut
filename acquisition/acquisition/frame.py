"""The unit of data a CameraBackend produces per exposure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class PixelFormat(str, Enum):
    """Pixel formats a CameraBackend may deliver.

    Deliberately a small closed set, not a passthrough of PySpin's ~20 format
    enums: this is the contract between the backend and the writer, and every
    member here must have a defined FFmpeg raw-input format (see
    ``ffmpeg_pixel_format``) and a defined numpy shape. Widening it is a real
    decision, not an implementation detail.

    The rig's camera (Blackfly S BFS-U3-04S2C) is a *colour* sensor, so Mono8
    frames are luma derived from the Bayer mosaic rather than a native
    monochrome readout -- see acquisition/acquisition/HARDWARE.md.
    """

    MONO8 = "mono8"
    BGR8 = "bgr8"

    @property
    def channels(self) -> int:
        return 1 if self is PixelFormat.MONO8 else 3

    @property
    def ffmpeg_pixel_format(self) -> str:
        """The ``-pixel_format`` value for FFmpeg's rawvideo demuxer."""
        return "gray8" if self is PixelFormat.MONO8 else "bgr24"

    def expected_shape(self, width: int, height: int) -> tuple[int, ...]:
        return (height, width) if self is PixelFormat.MONO8 else (height, width, 3)


@dataclass(frozen=True)
class Frame:
    """One captured image plus its camera-supplied chunk data.

    ``hardware_timestamp_ns`` and ``frame_id`` come from the camera's onboard
    chunk data, never host wall-clock arrival time (acquisition/CLAUDE.md
    invariant 6).

    ``image`` must own its memory. A real SDK hands back an array that views a
    buffer it will recycle, so :class:`SpinnakerCamera` copies before releasing
    the image -- frames outlive the callback that produced them (pre-roll
    deque, writer queue), so a view would silently alias overwritten data.
    """

    image: np.ndarray
    hardware_timestamp_ns: int
    frame_id: int
    pixel_format: PixelFormat = PixelFormat.MONO8

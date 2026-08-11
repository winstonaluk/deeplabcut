"""FFmpeg encoder capability probing and fallback selection.

h264_qsv (Intel Quick Sync) is the primary path on the target acquisition PC's
HD 630 iGPU; libx264 is the software fallback. Both are declared in
config.toml (invariant 9) -- this module decides which is actually usable on
the machine it's running on, once, rather than discovering failure mid-trial.
"""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def probe_encoder(codec: str, timeout: float = 15.0) -> bool:
    """Runs a throwaway 1-frame encode. Returns True iff it succeeds."""
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=black:s=32x32:d=0.04",
        "-frames:v", "1", "-c:v", codec, "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def resolve_encoder(preferred: str, fallback: str) -> str:
    """Returns ``preferred`` if it actually works here, else ``fallback``.

    Never silently drops to a third option -- if neither works, the caller's
    ffmpeg invocation will fail loudly at trial start, which is a preflight
    concern (A5), not something to paper over here.
    """
    if probe_encoder(preferred):
        return preferred
    logger.warning("encoder %r unavailable on this machine, falling back to %r", preferred, fallback)
    return fallback

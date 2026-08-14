"""Shared data contract between the acquisition GUI and the analysis pipeline.

Defines the on-disk schemas for ``session_metadata.json``, ``trials.csv``, and
the per-trial timestamp sidecar CSV, plus the read/write helpers both apps use
so serialization logic exists exactly once. Neither app should redefine these
structures locally (see the "Cross-repo contract" section of each app's
CLAUDE.md).
"""

from schema.errors import SchemaValidationError, SchemaVersionError
from schema.session_metadata import CameraInfo, SessionMetadata
from schema.timestamps import TIMESTAMPS_SCHEMA_VERSION, TimestampRow
from schema.trials import TRIALS_SCHEMA_VERSION, TrialRecord

__all__ = [
    "CameraInfo",
    "SessionMetadata",
    "TimestampRow",
    "TIMESTAMPS_SCHEMA_VERSION",
    "TrialRecord",
    "TRIALS_SCHEMA_VERSION",
    "SchemaValidationError",
    "SchemaVersionError",
]

"""Exceptions raised by the shared schema readers/writers."""

from __future__ import annotations


class SchemaValidationError(ValueError):
    """A record is missing a required field or holds an invalid value."""


class SchemaVersionError(ValueError):
    """On-disk data was written by an incompatible schema version.

    Per the cross-repo contract in both apps' CLAUDE.md, a schema_version
    mismatch must fail loudly. Callers must never silently coerce.
    """

    def __init__(self, artifact: str, found: int, expected: int) -> None:
        self.artifact = artifact
        self.found = found
        self.expected = expected
        super().__init__(
            f"{artifact}: schema_version {found} is incompatible with "
            f"the reader's expected major version {expected}"
        )

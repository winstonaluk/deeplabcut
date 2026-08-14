"""Forces offscreen Qt rendering so GUI tests run with zero display attached
-- matches "the whole app must run with zero hardware attached" in spirit:
no display server should be required to prove the widgets behave correctly.
"""

import os
import shutil

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_ffmpeg: test spawns a real FFmpeg process; skipped when "
        "ffmpeg is not on PATH.",
    )


def pytest_collection_modifyitems(config, items):
    """Skips FFmpeg-dependent tests when FFmpeg isn't installed.

    FFmpeg is an external binary, not a Python dependency, so a machine
    without it turns eleven tests into identical FileNotFoundError tracebacks
    that bury any real regression underneath them. Skipping names the missing
    dependency instead -- and the app itself already treats a missing FFmpeg
    as a blocking preflight failure, so nothing here papers over a
    user-visible problem.
    """
    if shutil.which("ffmpeg") is not None:
        return
    skip = pytest.mark.skip(reason="ffmpeg not found on PATH")
    for item in items:
        if "requires_ffmpeg" in item.keywords:
            item.add_marker(skip)

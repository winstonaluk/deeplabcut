"""Forces offscreen Qt rendering so GUI tests run with zero display attached
-- matches "the whole app must run with zero hardware attached" in spirit:
no display server should be required to prove the widgets behave correctly.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app

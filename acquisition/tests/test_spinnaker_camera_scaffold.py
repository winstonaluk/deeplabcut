"""Checkpoint A9 (not buildable unattended): structural check only -- confirms
the scaffold satisfies CameraBackend and its methods are clearly stubbed
pending hardware, per SPINNAKER_PLAN.md."""

from __future__ import annotations

import pytest

from acquisition.camera_backend import CameraBackend
from acquisition.spinnaker_camera import SpinnakerCamera


def test_spinnaker_camera_satisfies_camera_backend():
    camera = SpinnakerCamera(serial="12345678")
    assert isinstance(camera, CameraBackend)
    assert camera.serial == "12345678"
    assert camera.is_streaming is False


@pytest.mark.parametrize("method_name", ["open", "close"])
def test_lifecycle_methods_raise_not_implemented(method_name):
    camera = SpinnakerCamera(serial="12345678")
    with pytest.raises(NotImplementedError):
        getattr(camera, method_name)()


def test_load_user_set_raises_not_implemented():
    camera = SpinnakerCamera(serial="12345678")
    with pytest.raises(NotImplementedError):
        camera.load_user_set("UserSet1")


def test_streaming_methods_raise_not_implemented():
    camera = SpinnakerCamera(serial="12345678")
    with pytest.raises(NotImplementedError):
        camera.start_streaming(lambda frame: None)
    with pytest.raises(NotImplementedError):
        camera.stop_streaming()

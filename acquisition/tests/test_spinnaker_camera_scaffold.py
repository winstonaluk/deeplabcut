"""Structural check on the SpinnakerCamera scaffold: it satisfies the
CameraBackend contract, and every method that needs hardware says so clearly
rather than failing obscurely at run time.

Behaviour lands in checkpoint A10, which needs a camera on the bench --
see SPINNAKER_PLAN.md and HARDWARE.md.
"""

from __future__ import annotations

import pytest

from acquisition.camera_backend import CameraBackend
from acquisition.frame import PixelFormat
from acquisition.spinnaker_camera import (
    REQUIRED_CHUNKS,
    STREAM_BUFFER_HANDLING_MODE,
    SpinnakerCamera,
)


def test_spinnaker_camera_satisfies_camera_backend():
    camera = SpinnakerCamera(serial="12345678")
    assert isinstance(camera, CameraBackend)
    assert camera.serial == "12345678"
    assert camera.is_streaming is False
    assert camera.incomplete_frame_count == 0


def test_pixel_format_is_known_before_the_camera_is_open():
    """The target format is a construction-time decision (config), unlike
    resolution and frame rate, which are read from the camera at open()."""
    assert SpinnakerCamera(serial="1").pixel_format is PixelFormat.MONO8
    assert (
        SpinnakerCamera(serial="1", pixel_format=PixelFormat.BGR8).pixel_format
        is PixelFormat.BGR8
    )


@pytest.mark.parametrize(
    "method_name", ["open", "close", "stop_streaming"]
)
def test_lifecycle_methods_raise_not_implemented(method_name):
    camera = SpinnakerCamera(serial="12345678")
    with pytest.raises(NotImplementedError):
        getattr(camera, method_name)()


def test_user_set_and_verification_raise_not_implemented():
    camera = SpinnakerCamera(serial="12345678")
    with pytest.raises(NotImplementedError):
        camera.load_user_set("UserSet1")
    with pytest.raises(NotImplementedError):
        camera.verify_settings({"ExposureAuto": "Off"})


def test_start_streaming_raises_not_implemented():
    camera = SpinnakerCamera(serial="12345678")
    with pytest.raises(NotImplementedError):
        camera.start_streaming(lambda frame: None)


def test_hardware_reported_properties_refuse_to_guess():
    """Resolution and frame rate must come from the camera. Returning the
    configured value instead is exactly the failure this schema exists to
    prevent, so the scaffold refuses rather than inventing one."""
    camera = SpinnakerCamera(serial="12345678")
    with pytest.raises(NotImplementedError):
        _ = camera.resolution
    with pytest.raises(NotImplementedError):
        _ = camera.frame_rate


def test_recording_critical_constants_are_pinned():
    """These two are load-bearing and easy to regress silently.

    NewestOnly would drop frames without telling us (right for a viewer,
    wrong for a recorder), and invariant 6 is unsatisfiable without both
    chunks, since the rig camera ships with them disabled.
    """
    assert STREAM_BUFFER_HANDLING_MODE == "OldestFirst"
    assert set(REQUIRED_CHUNKS) == {"FrameID", "Timestamp"}

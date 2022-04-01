"""
`pymagewell` is a Python library for interfacing with Magewell ProCapture frame grabbers.

It is based on (and includes) Magewell's Windows SDK and is therefore Windows only. However, it provides a mock class
that for testing and development that does not depend on the SDK's Windows .dll files, so `pymagwell` can also be
installed on macOS and Linux.
"""
from . import _version
from .pro_capture_controller import ProCaptureController

from .pro_capture_device import ProCaptureDevice
from .pro_capture_device.device_settings import ProCaptureSettings, TransferMode, ImageSizeInPixels, ColourFormat
from .pro_capture_device.mock_pro_capture_device import MockProCaptureDevice

__version__ = _version.get_versions()["version"]  # type: ignore

__all__ = [
    "ProCaptureDevice",
    "MockProCaptureDevice",
    "ProCaptureController",
    "ProCaptureSettings",
    "TransferMode",
    "ImageSizeInPixels",
    "ColourFormat",
]

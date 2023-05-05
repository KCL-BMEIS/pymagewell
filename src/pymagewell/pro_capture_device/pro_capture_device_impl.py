from abc import ABC

from pymagewell.pro_capture_device.device_interface import (
    ProCaptureDeviceInterface,
    FrameProperties,
)
from pymagewell.pro_capture_device.device_settings import (
    TransferMode,
    ProCaptureSettings,
)


class ProCaptureDeviceImpl(ProCaptureDeviceInterface, ABC):
    """Implements methods of the interface that do not require communication with the driver or hardware, or require use
    of the Events system, and therefore are common to Mock and Real implementations of the interface."""

    def __init__(self, settings: ProCaptureSettings):
        self._settings = settings

    @property
    def transfer_mode(self) -> TransferMode:
        return self._settings.transfer_mode

    @property
    def frame_properties(self) -> FrameProperties:
        return FrameProperties(dimensions=self._settings.dimensions, size_in_bytes=self._settings.image_size_in_bytes)

    @property
    def fps(self) -> float:
        if self.signal_status.interlaced:
            fps = 2e7 / self.signal_status.frame_period_s
        else:
            fps = 1e7 / self.signal_status.frame_period_s
        return fps

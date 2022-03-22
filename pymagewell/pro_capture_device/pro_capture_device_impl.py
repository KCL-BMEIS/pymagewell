from abc import ABC
from dataclasses import dataclass

from pymagewell.events.events import TransferCompleteEvent, SignalChangeEvent, FrameBufferedEvent, FrameBufferingEvent, \
    TimerEvent
from pymagewell.pro_capture_device.device_interface import ProCaptureDeviceInterface
from pymagewell.pro_capture_device.device_settings import TransferMode, ProCaptureSettings
from pymagewell.pro_capture_device.pro_capture_device import FrameProperties


@dataclass
class ProCaptureEvents:
    transfer_complete: TransferCompleteEvent
    """ The event raised by the driver when a transfer (whole frame in normal mode, partial frame in low-latency
    mode) is complete."""
    signal_change: SignalChangeEvent
    """ The event raised by the driver when a source signal change is detected."""
    frame_buffered: FrameBufferedEvent
    """ The event raised by the driver in TransferMode.NORMAL when a frame has been acquired to on-device memory."""
    frame_buffering: FrameBufferingEvent
    """ The event raised by the driver in TransferMode.LOW_LATENCY when a frame has started to be acquired to on-device
    memory."""
    timer_event: TimerEvent
    """ The event raised by the driver in TransferMode.TIMER when a frame has been acquired to on-device memory."""


class ProCaptureDeviceImpl(ProCaptureDeviceInterface, ABC):
    """Implements methods of the interface that do not require communication with the driver or hardware, or require use
    of the Events system, and therefore are common to Mock and Real implementations of the interface."""

    def __init__(self, settings: ProCaptureSettings):
        super(ProCaptureDeviceImpl, self).__init__()
        self._settings = settings

    @property
    def transfer_mode(self) -> TransferMode:
        return self._settings.transfer_mode

    @property
    def frame_properties(self) -> FrameProperties:
        return FrameProperties(
            dimensions=self._settings.dimensions,
            size_in_bytes=self._settings.image_size_in_bytes
        )

    @property
    def fps(self) -> float:
        if self.signal_status.interlaced:
            fps = 2e7 / self.signal_status.frame_period_s
        else:
            fps = 1e7 / self.signal_status.frame_period_s
        return fps

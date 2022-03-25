from abc import ABC, abstractmethod
from ctypes import Array, c_char
from dataclasses import dataclass
from datetime import datetime

from pymagewell.events.device_events import (
    TransferCompleteEvent,
    SignalChangeEvent,
    FrameBufferedEvent,
    FrameBufferingEvent,
    TimerEvent,
)
from pymagewell.pro_capture_device.device_settings import (
    ProCaptureSettings,
    TransferMode,
    ImageSizeInPixels,
)
from pymagewell.pro_capture_device.device_status import (
    OnDeviceBufferStatus,
    FrameInfo,
    SignalStatus,
    TransferStatus,
)


@dataclass
class FrameProperties:
    dimensions: ImageSizeInPixels
    size_in_bytes: int


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


class ProCaptureDeviceInterface(ABC):
    @abstractmethod
    def __init__(self, settings: ProCaptureSettings):
        raise NotImplementedError()

    @property
    @abstractmethod
    def transfer_mode(self) -> TransferMode:
        raise NotImplementedError()

    @property
    @abstractmethod
    def frame_properties(self) -> FrameProperties:
        raise NotImplementedError()

    @property
    @abstractmethod
    def events(self) -> ProCaptureEvents:
        raise NotImplementedError()

    @abstractmethod
    def schedule_timer_event(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def buffer_status(self) -> OnDeviceBufferStatus:
        raise NotImplementedError()

    @property
    @abstractmethod
    def frame_info(self) -> FrameInfo:
        raise NotImplementedError()

    @property
    @abstractmethod
    def signal_status(self) -> SignalStatus:
        raise NotImplementedError()

    @property
    @abstractmethod
    def transfer_status(self) -> TransferStatus:
        raise NotImplementedError()

    @abstractmethod
    def start_grabbing(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_grabbing(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def fps(self) -> float:
        raise NotImplementedError()

    @abstractmethod
    def start_a_frame_transfer(self, frame_buffer: Array[c_char]) -> datetime:
        raise NotImplementedError()

    @abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError()

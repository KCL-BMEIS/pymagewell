from abc import ABC, abstractmethod
from ctypes import Array, c_char

from mwcapture.libmwcapture import mw_device_time
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, TransferMode
from pymagewell.pro_capture_device.device_status import OnDeviceBufferStatus, FrameStatus, SignalStatus, TransferStatus
from pymagewell.pro_capture_device.pro_capture_device import FrameProperties
from pymagewell.pro_capture_device.pro_capture_device_impl import ProCaptureEvents


class ProCaptureDeviceInterface(ABC):
    @abstractmethod
    def __init__(self, settings: ProCaptureSettings):
        raise NotImplementedError()

    @abstractmethod
    @property
    def transfer_mode(self) -> TransferMode:
        raise NotImplementedError()

    @abstractmethod
    @property
    def frame_properties(self) -> FrameProperties:
        raise NotImplementedError()

    @abstractmethod
    @property
    def events(self) -> ProCaptureEvents:
        raise NotImplementedError()

    @abstractmethod
    def schedule_timer_event(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    @property
    def buffer_status(self) -> OnDeviceBufferStatus:
        raise NotImplementedError()

    @abstractmethod
    @property
    def frame_status(self) -> FrameStatus:
        raise NotImplementedError()

    @abstractmethod
    @property
    def signal_status(self) -> SignalStatus:
        raise NotImplementedError()

    @abstractmethod
    @property
    def transfer_status(self) -> TransferStatus:
        raise NotImplementedError()

    @abstractmethod
    def start_grabbing(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_grabbing(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    @property
    def fps(self) -> float:
        raise NotImplementedError()

    @abstractmethod
    def start_a_frame_transfer(self, frame_buffer: Array[c_char]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError()
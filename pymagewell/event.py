from abc import ABC, abstractmethod
from typing import Any

import win32api
import win32event

from mwcapture.libmwcapture import MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE
from pymagewell.device import Device


class Event(ABC):
    def __init__(self, device: Device):
        self._device = device
        self._win32_event = win32event.CreateEvent(None, False, False, None)
        self._registered = self._register()

    @abstractmethod
    def _register(self) -> Any:
        raise NotImplementedError()

    @property
    def win32_event(self) -> Any:
        return self._win32_event

    @property
    def registered_event(self) -> Any:
        return self._registered

    def destroy(self) -> None:
        win32api.CloseHandle(int(self.win32_event))
        self._win32_event = 0


class SignalChangeEvent(Event):
    def _register(self) -> Any:
        return self._device.mw_register_notify(self._device.channel, self.win32_event, MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE)


class TimerEvent(Event):
    def _register(self) -> Any:
        return self._device.mw_register_timer(self._device.channel, self.win32_event)


class CaptureEvent(Event):
    def _register(self) -> Any:
        return None
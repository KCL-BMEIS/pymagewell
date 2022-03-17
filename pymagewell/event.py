from abc import ABC, abstractmethod
from typing import Any

import win32api
import win32event

from mwcapture.libmwcapture import MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE
from pymagewell.notifications import MWCAP_NOTIFY_VIDEO_FRAME_BUFFERING, MWCAP_NOTIFY_VIDEO_FRAME_BUFFERED


class Event:
    def __init__(self):
        self._win32_event = win32event.CreateEvent(None, False, False, None)

    @property
    def win32_event(self) -> Any:
        return self._win32_event

    def destroy(self) -> None:
        win32api.CloseHandle(int(self.win32_event))
        self._win32_event = 0


class RegisterableEvent(Event, ABC):
    @abstractmethod
    @property
    def registration_token(self) -> int:
        raise NotImplementedError()


class SignalChangeEvent(RegisterableEvent):
    @property
    def registration_token(self) -> int:
        return MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE


class FrameBufferingEvent(RegisterableEvent):
    @property
    def registration_token(self) -> int:
        return MWCAP_NOTIFY_VIDEO_FRAME_BUFFERING


class FrameBufferedEvent(RegisterableEvent):
    @property
    def registration_token(self) -> int:
        return MWCAP_NOTIFY_VIDEO_FRAME_BUFFERED


class CaptureEvent(Event):
    pass


class TimerEvent(Event):
    pass

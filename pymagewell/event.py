from mwcapture.libmwcapture import MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE
from pymagewell.event_state import Event, RegisterableEvent
from pymagewell.notifications import MWCAP_NOTIFY_VIDEO_FRAME_BUFFERING, MWCAP_NOTIFY_VIDEO_FRAME_BUFFERED, Notification


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

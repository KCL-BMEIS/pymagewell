from mwcapture.libmwcapture import MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE
from pymagewell.events.event_base import Event, RegisterableEvent
from pymagewell.events.notification import (
    MWCAP_NOTIFY_VIDEO_FRAME_BUFFERING,
    MWCAP_NOTIFY_VIDEO_FRAME_BUFFERED,
)


class SignalChangeEvent(RegisterableEvent):
    """This event is raised by the driver if the source video signal changes"""

    @property
    def registration_token(self) -> int:
        return MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE


class FrameBufferingEvent(RegisterableEvent):
    """Raised when frame starts to be acquired by the hardware."""

    @property
    def registration_token(self) -> int:
        return MWCAP_NOTIFY_VIDEO_FRAME_BUFFERING


class FrameBufferedEvent(RegisterableEvent):
    """Raised when a frame has been completely acquired by the hardware."""

    @property
    def registration_token(self) -> int:
        return MWCAP_NOTIFY_VIDEO_FRAME_BUFFERED


class TimerEvent(RegisterableEvent):
    """The driver provides a timer function to acquire frames at a custom rate. The _FrameTimer configures the driver
    to raise this event when the timer ticks/"""

    @property
    def registration_token(self) -> None:
        return None


class TransferCompleteEvent(Event):
    pass


class FrameTransferCompleteEvent(TransferCompleteEvent):
    """This event intended to be provided to Device.mw_start_video_capture(). The driver will then raise this event
    once a capture is complete. It is only used in normal mode, to signify that a whole frame has been transferred
    to PC memory."""

    pass


class PartialFrameTransferCompleteEvent(TransferCompleteEvent):
    """This event is intended to be provided to Device.mw_start_video_capture(). The driver will then raise this event
    once a capture is complete. It is only used in low-latency mode, and means that `cypartialnotify` lines have been
    transferred to PC memory."""

    pass

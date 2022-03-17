from ctypes import create_unicode_buffer
from typing import Any

from mwcapture.libmwcapture import mw_capture, mwcap_video_buffer_info, mwcap_video_frame_info, mw_video_signal_status, \
    MW_SUCCEEDED, MWCAP_VIDEO_SIGNAL_NONE, MWCAP_VIDEO_SIGNAL_UNSUPPORTED, MWCAP_VIDEO_SIGNAL_LOCKING, \
    MWCAP_VIDEO_SIGNAL_LOCKED, mw_video_capture_status
from pymagewell.event import RegisterableEvent, SignalChangeEvent, CaptureEvent, FrameBufferingEvent, FrameBufferedEvent


class Device(mw_capture):
    def __init__(self):
        super(Device, self).__init__()
        self.mw_capture_init_instance()
        self.mw_refresh_device()
        self._channel = create_channel(self)

        # Registerable events
        self._signal_change_event = SignalChangeEvent()
        self._signal_change_notification = self._register_event(self._signal_change_event)
        self._frame_buffered_event = FrameBufferedEvent()
        self._frame_buffered_notification = self._register_event(self._frame_buffered_event)
        self._frame_buffering_event = FrameBufferingEvent()
        self._frame_buffering_notification = self._register_event(self._frame_buffering_event)

        self._capture_event = CaptureEvent()

    @property
    def signal_change_event(self) -> SignalChangeEvent:
        return self._signal_change_event

    @property
    def capture_event(self) -> CaptureEvent:
        return self._capture_event

    def _register_event(self, event: RegisterableEvent) -> Any:
        return self.mw_register_notify(self.channel, event.win32_event, event.registration_token)

    @property
    def channel(self) -> int:
        return self._channel

    @property
    def buffer_info(self) -> mwcap_video_buffer_info:
        buffer_info = mwcap_video_buffer_info()
        self.mw_get_video_buffer_info(self.channel, buffer_info)
        return buffer_info

    @property
    def frame_info(self) -> mwcap_video_frame_info:
        frame_info = mwcap_video_frame_info()
        self.mw_get_video_frame_info(self.channel, self.buffer_info.iNewestBufferedFullFrame, frame_info)
        return frame_info

    @property
    def signal_status(self) -> mw_video_signal_status:
        signal_status = mw_video_signal_status()
        self.mw_get_video_signal_status(self.channel, signal_status)
        return signal_status

    def start(self) -> None:
        start_capture_result = self.mw_start_video_capture(self.channel, self._capture_event.win32_event)
        if start_capture_result != MW_SUCCEEDED:
            raise IOError(f"Start capture failed (error code {start_capture_result}).")
        # Check status of input signal
        if self.signal_status.state == MWCAP_VIDEO_SIGNAL_NONE:
            print("Input signal status: None")
        elif self.signal_status.state == MWCAP_VIDEO_SIGNAL_UNSUPPORTED:
            print("Input signal status: Unsupported")
        elif self.signal_status.state == MWCAP_VIDEO_SIGNAL_LOCKING:
            print("Input signal status: Locking")
        elif self.signal_status.state == MWCAP_VIDEO_SIGNAL_LOCKED:
            print("Input signal status: Locked")

        # Exit if signal not locked
        if self.signal_status.state != MWCAP_VIDEO_SIGNAL_LOCKED:
            self.mw_stop_video_capture(self.channel)
            self.shutdown()
            raise IOError('Signal not locked.')

    def stop(self) -> None:
        self.mw_stop_video_capture(self.channel)

    @property
    def fps(self) -> float:
        if self.signal_status.bInterlaced:
            fps = 2e7 / self.signal_status.dwFrameDuration
        else:
            fps = 1e7 / self.signal_status.dwFrameDuration
        return fps

    def print_signal_info(self) -> None:
        print(f"Input signal resolution: {self.signal_status.cx} by {self.signal_status.cy}")
        print(f"Input signal FPS: {self.fps}")
        print(f"Input signal interlaced: {self.signal_status.bInterlaced}")
        print(f"Input signal frame segmented: {self.signal_status.bSegmentedFrame}")

    @property
    def capture_status(self) -> mw_video_capture_status:
        capture_status = mw_video_capture_status()
        self.mw_get_video_capture_status(self.channel, capture_status)
        return capture_status

    def shutdown(self) -> None:
        self._signal_change_event.destroy()
        self._capture_event.destroy()
        self._frame_buffered_event.destroy()
        self._frame_buffering_event.destroy()

        self.mw_close_channel(self.channel)
        self.mw_capture_exit_instance()


def create_channel(capturer: mw_capture) -> int:
    t_path = create_unicode_buffer(128)
    capturer.mw_get_device_path(0, t_path)
    return capturer.mw_open_channel_by_path(t_path)
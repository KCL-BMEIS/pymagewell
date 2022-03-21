import math
from ctypes import create_unicode_buffer
from typing import cast

from mwcapture.libmwcapture import mw_capture, mwcap_video_buffer_info, mwcap_video_frame_info, mw_video_signal_status, \
    MW_SUCCEEDED, MWCAP_VIDEO_SIGNAL_NONE, MWCAP_VIDEO_SIGNAL_UNSUPPORTED, MWCAP_VIDEO_SIGNAL_LOCKING, \
    MWCAP_VIDEO_SIGNAL_LOCKED, mw_video_capture_status, mw_device_time
from pymagewell.events.events import RegisterableEvent, SignalChangeEvent, FrameBufferingEvent, \
    FrameBufferedEvent, FrameTransferCompleteEvent, TransferCompleteEvent, PartialFrameTransferCompleteEvent, TimerEvent
from pymagewell.notifications import Notification
from pymagewell.settings import TransferMode


def check_valid_chunk_size(n_scan_lines_per_chunk: int) -> int:
    if n_scan_lines_per_chunk < 64:
        raise ValueError('Minimum number of scan lines per chunk is 64.')
    elif round(math.log2(n_scan_lines_per_chunk)) != math.log2(n_scan_lines_per_chunk):
        raise ValueError('Number of scan lines per chunk must be a power of 2.')
    else:
        return n_scan_lines_per_chunk


class ProCaptureDevice(mw_capture):
    """ A ProCapture hardware device. Inherits from the mw_capture class provided by Magewell's python library.

    ProCaptureDevice is responsible for constructing and registering events with the Magewell driver. It also provides
     methods for accessing information about the video source connected to the device."""

    def __init__(self, transfer_mode: TransferMode, n_scan_lines_per_chunk: int = 64):
        """ transfer_mode determines which events are registered with the driver."""
        super(ProCaptureDevice, self).__init__()
        self._transfer_mode = transfer_mode
        self._n_scan_lines_per_chunk = check_valid_chunk_size(n_scan_lines_per_chunk)
        self.mw_capture_init_instance()
        self.mw_refresh_device()
        self._channel = create_channel(self)

        self._signal_change_event = cast(SignalChangeEvent, self._register_event(SignalChangeEvent()))

        self._frame_buffered_event = FrameBufferedEvent()
        self._frame_buffering_event = FrameBufferingEvent()

        if self._transfer_mode == TransferMode.NORMAL:
            self._frame_buffered_event = cast(FrameBufferedEvent, self._register_event(self._frame_buffered_event))
            self._transfer_complete_event: TransferCompleteEvent = FrameTransferCompleteEvent()

        elif self._transfer_mode == TransferMode.LOW_LATENCY:
            self._frame_buffering_event = cast(FrameBufferingEvent, self._register_event(self._frame_buffering_event))
            self._transfer_complete_event = PartialFrameTransferCompleteEvent()

        elif self._transfer_mode.TIMER:
            self._transfer_complete_event = FrameTransferCompleteEvent()

    @property
    def n_scan_lines_per_chunk(self) -> int:
        return self._n_scan_lines_per_chunk

    @property
    def transfer_mode(self) -> TransferMode:
        return self._transfer_mode

    @property
    def transfer_complete_event(self) -> TransferCompleteEvent:
        """ The event raised by the driver when a transfer (whole frame in normal mode, partial frame in low-latency
        mode) is complete."""
        return self._transfer_complete_event

    @property
    def signal_change_event(self) -> SignalChangeEvent:
        """ The event raised by the driver when a source signal change is detected."""
        return self._signal_change_event

    @property
    def frame_buffered_event(self) -> FrameBufferedEvent:
        """ The event raised by the driver in TransferMode.NORMAL when a frame has been acquired to on-device memory."""
        return self._frame_buffered_event

    @property
    def frame_buffering_event(self) -> FrameBufferingEvent:
        """ The event raised by the driver in TransferMode.LOW_LATENCY when a frame has started to be acquired to on-device
        memory."""
        return self._frame_buffering_event

    def _register_event(self, event: RegisterableEvent) -> RegisterableEvent:
        notification_handle = self.mw_register_notify(self.channel, event.win32_event, event.registration_token)
        event.register(Notification(notification_handle, self.channel))
        return event

    def register_timer_event(self, event: TimerEvent) -> TimerEvent:
        """ The FrameTimer class handles constructing TimerEvents and registering them here."""
        notification_handle = self.mw_register_timer(self.channel, event.win32_event)
        event.register(Notification(notification_handle, self.channel))
        return event

    @property
    def channel(self) -> int:
        """Handle to the devices 'channel', used by the frame grabbing function."""
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
        """ Starts the hardware acquiring frames"""
        start_capture_result = self.mw_start_video_capture(self.channel, self.transfer_complete_event.win32_event)
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
        """ Used to find out if a full frame has been transferred, or how many lines have been transferred, among other
        things."""
        capture_status = mw_video_capture_status()
        self.mw_get_video_capture_status(self.channel, capture_status)
        return capture_status

    def get_device_time(self) -> mw_device_time:
        """ Read a timestamp from the device."""
        time = mw_device_time()
        result = self.mw_get_device_time(self.channel, time)
        if result != MW_SUCCEEDED:
            raise IOError("Failed to read time from device")
        else:
            return time

    def shutdown(self) -> None:
        self._signal_change_event.destroy()
        self._transfer_complete_event.destroy()
        self._frame_buffered_event.destroy()
        self._frame_buffering_event.destroy()

        self.mw_close_channel(self.channel)
        self.mw_capture_exit_instance()


def create_channel(capturer: mw_capture) -> int:
    t_path = create_unicode_buffer(128)
    capturer.mw_get_device_path(0, t_path)
    return capturer.mw_open_channel_by_path(t_path)
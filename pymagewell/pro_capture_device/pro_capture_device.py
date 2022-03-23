from ctypes import create_unicode_buffer, Array, c_char, addressof
from typing import cast, Optional

from mwcapture.libmwcapture import mw_capture, mwcap_video_buffer_info, mwcap_video_frame_info, mw_video_signal_status, \
    MW_SUCCEEDED, mw_video_capture_status, mw_device_time, MWCAP_VIDEO_DEINTERLACE_BLEND, \
    MWCAP_VIDEO_ASPECT_RATIO_CROPPING, MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN, MWCAP_VIDEO_QUANTIZATION_UNKNOWN, \
    MWCAP_VIDEO_SATURATION_UNKNOWN
from pymagewell.pro_capture_device.device_status import TransferStatus, SignalStatus, SignalState, OnDeviceBufferStatus, \
    FrameStatus
from pymagewell.events.events import RegisterableEvent, SignalChangeEvent, FrameBufferingEvent, \
    FrameBufferedEvent, FrameTransferCompleteEvent, TransferCompleteEvent, PartialFrameTransferCompleteEvent, TimerEvent
from pymagewell.events.notification import Notification
from pymagewell.pro_capture_device.device_settings import TransferMode, ProCaptureSettings
from pymagewell.pro_capture_device.pro_capture_device_impl import ProCaptureDeviceImpl
from pymagewell.pro_capture_device.device_interface import ProCaptureEvents


class ProCaptureDevice(ProCaptureDeviceImpl, mw_capture):
    """ A ProCapture hardware device. Inherits from the mw_capture class provided by Magewell's python library.

    ProCaptureDevice is responsible for constructing and registering events with the Magewell driver. It also provides
     methods for accessing information about the video source connected to the device."""

    def __init__(self, settings: ProCaptureSettings):
        """ transfer_mode determines which events the device will raise to trigger a ProCaptureController to start
        transfer. n_lines_per_chunk sets the number lines after which a transfer will be triggered when
        transfer_mode is set to LowLatency."""
        ProCaptureDeviceImpl.__init__(self, settings)
        mw_capture.__init__(self)

        self.mw_capture_init_instance()
        self.mw_refresh_device()
        self._channel = create_channel(self)
        self._timer = FrameTimer(self, self._channel, self._register_timer_event(TimerEvent()))

        self._signal_change_event = cast(SignalChangeEvent, self._register_event(SignalChangeEvent()))

        self._frame_buffered_event = FrameBufferedEvent()
        self._frame_buffering_event = FrameBufferingEvent()

        if self._settings.transfer_mode == TransferMode.NORMAL:
            self._frame_buffered_event = cast(FrameBufferedEvent, self._register_event(self._frame_buffered_event))
            self._transfer_complete_event: TransferCompleteEvent = FrameTransferCompleteEvent()

        elif self._settings.transfer_mode == TransferMode.LOW_LATENCY:
            self._frame_buffering_event = cast(FrameBufferingEvent, self._register_event(self._frame_buffering_event))
            self._transfer_complete_event = PartialFrameTransferCompleteEvent()

        elif self._settings.transfer_mode.TIMER:
            self._transfer_complete_event = FrameTransferCompleteEvent()

    @property
    def events(self) -> ProCaptureEvents:
        return ProCaptureEvents(
            transfer_complete=self._transfer_complete_event,
            signal_change=self._signal_change_event,
            frame_buffered=self._frame_buffered_event,
            frame_buffering=self._frame_buffering_event,
            timer_event=self._timer.event
        )

    def _register_event(self, event: RegisterableEvent) -> RegisterableEvent:
        notification_handle = self.mw_register_notify(self._channel, event.win32_event, event.registration_token)
        event.register(Notification(notification_handle, self._channel))
        return event

    def _register_timer_event(self, event: TimerEvent) -> TimerEvent:
        """ The FrameTimer class handles constructing TimerEvents and registering them here."""
        notification_handle = self.mw_register_timer(self._channel, event.win32_event)
        event.register(Notification(notification_handle, self._channel))
        return event

    def schedule_timer_event(self) -> None:
        self._timer.schedule_timer_event(self._get_device_time())

    @property
    def buffer_status(self) -> OnDeviceBufferStatus:
        buffer_info = mwcap_video_buffer_info()
        self.mw_get_video_buffer_info(self._channel, buffer_info)
        return OnDeviceBufferStatus.from_mwcap_video_buffer_info(buffer_info)

    @property
    def frame_status(self) -> FrameStatus:
        frame_info = mwcap_video_frame_info()
        self.mw_get_video_frame_info(self._channel, self.buffer_status.last_buffered_frame_index, frame_info)
        return FrameStatus.from_mwcap_video_frame_info(frame_info)

    @property
    def signal_status(self) -> SignalStatus:
        mw_signal_status = mw_video_signal_status()
        self.mw_get_video_signal_status(self._channel, mw_signal_status)
        return SignalStatus.from_mw_video_signal_status(mw_signal_status)

    def start_grabbing(self) -> None:
        """ Starts the hardware acquiring frames"""
        start_capture_result = self.mw_start_video_capture(self._channel, self.events.transfer_complete.win32_event)
        if start_capture_result != MW_SUCCEEDED:
            raise IOError(f"Start capture failed (error code {start_capture_result}).")
        # Check status of input signal
        if self.signal_status.state == SignalState.NONE:
            print("Input signal status: None")
        elif self.signal_status.state == SignalState.UNSUPPORTED:
            print("Input signal status: Unsupported")
        elif self.signal_status.state == SignalState.LOCKING:
            print("Input signal status: Locking")
        elif self.signal_status.state == SignalState.LOCKED:
            print("Input signal status: Locked")

        # Exit if signal not locked
        if self.signal_status.state != SignalState.LOCKED:
            self.mw_stop_video_capture(self._channel)
            self.shutdown()
            raise IOError('Signal not locked.')

    def stop_grabbing(self) -> None:
        self.mw_stop_video_capture(self._channel)

    @property
    def transfer_status(self) -> TransferStatus:
        """ Used to find out if a full frame has been transferred, or how many lines have been transferred, among other
        things."""
        mw_capture_status = mw_video_capture_status()
        self.mw_get_video_capture_status(self._channel, mw_capture_status)
        return TransferStatus.from_mw_video_capture_status(mw_capture_status)

    def _get_device_time(self) -> mw_device_time:
        """ Read a timestamp from the device."""
        time = mw_device_time()
        result = self.mw_get_device_time(self._channel, time)
        if result != MW_SUCCEEDED:
            raise IOError("Failed to read time from device")
        else:
            return time

    def start_a_frame_transfer(self, frame_buffer: Array[c_char]) -> None:
        """ Start the transfer of lines from the device to a buffer in PC memory."""
        in_low_latency_mode = self.transfer_mode == TransferMode.LOW_LATENCY
        notify_size = self._settings.num_lines_per_chunk if in_low_latency_mode else 0
        result = self.mw_capture_video_frame_to_virtual_address_ex(
            hchannel=self._channel,
            iframe=self.buffer_status.last_buffered_frame_index,
            pbframe=addressof(frame_buffer),
            cbframe=self._settings.image_size_in_bytes,
            cbstride=self._settings.min_stride,
            bbottomup=False,  # this is True in the C++ example, but false in python example,
            pvcontext=0,
            dwfourcc=self._settings.color_format,  # color format of captured frames
            cx=self._settings.dimensions.cols,
            cy=self._settings.dimensions.rows,
            dwprocessswitchs=0,
            cypartialnotify=notify_size,
            hosdimage=0,
            posdrects=0,
            cosdrects=0,
            scontrast=100,
            sbrightness=0,
            ssaturation=100,
            shue=0,
            deinterlacemode=MWCAP_VIDEO_DEINTERLACE_BLEND,
            aspectratioconvertmode=MWCAP_VIDEO_ASPECT_RATIO_CROPPING,
            prectsrc=0,  # 0 in C++ example, but configured using CLIP settings in python example,
            prectdest=0,
            naspectx=0,
            naspecty=0,
            colorformat=MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN,
            quantrange=MWCAP_VIDEO_QUANTIZATION_UNKNOWN,
            satrange=MWCAP_VIDEO_SATURATION_UNKNOWN
        )
        if result != MW_SUCCEEDED:
            print(f"Frame grab failed with error code {result}")
            return None

    def shutdown(self) -> None:
        self._timer.shutdown()
        self._signal_change_event.destroy()
        self._transfer_complete_event.destroy()
        self._frame_buffered_event.destroy()
        self._frame_buffering_event.destroy()

        self.mw_close_channel(self._channel)
        self.mw_capture_exit_instance()


def create_channel(capturer: mw_capture) -> int:
    t_path = create_unicode_buffer(128)
    capturer.mw_get_device_path(0, t_path)
    return capturer.mw_open_channel_by_path(t_path)


class FrameTimer:
    """ If the devices transfer mode it "Timer", this class is used to generate events triggering the transfer of frames
    from the device."""
    def __init__(self, device: ProCaptureDevice, channel: int, event: TimerEvent):
        self._device = device
        self._channel = channel
        self._frame_expire_time: Optional[mw_device_time] = None
        self._timer_event = event

    @property
    def event(self) -> TimerEvent:
        return self._timer_event

    def schedule_timer_event(self, device_time_now: mw_device_time):

        if self._frame_expire_time is None:
            self._frame_expire_time = device_time_now
        self._frame_expire_time.m_ll_device_time.value += int(1e3 * self._device.signal_status.frame_period_s)

        if self._timer_event.is_registered:
            result = self._device.mw_schedule_timer(self._channel, self._timer_event.notification,
                                                    self._frame_expire_time.m_ll_device_time)
        else:
            raise IOError("Timer event not registered with device.")
        if result != MW_SUCCEEDED:
            raise IOError("Failed to schedule frame timer")

    def shutdown(self) -> None:
        self._timer_event.destroy()

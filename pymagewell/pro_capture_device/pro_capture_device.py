from ctypes import create_unicode_buffer, Array, c_char, addressof
from dataclasses import dataclass
from typing import cast

from mwcapture.libmwcapture import mw_capture, mwcap_video_buffer_info, mwcap_video_frame_info, mw_video_signal_status, \
    MW_SUCCEEDED, mw_video_capture_status, mw_device_time, MWCAP_VIDEO_DEINTERLACE_BLEND, \
    MWCAP_VIDEO_ASPECT_RATIO_CROPPING, MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN, MWCAP_VIDEO_QUANTIZATION_UNKNOWN, \
    MWCAP_VIDEO_SATURATION_UNKNOWN
from pymagewell.pro_capture_device.device_status import TransferStatus, SignalStatus, SignalState, OnDeviceBufferStatus, \
    FrameStatus
from pymagewell.events.events import RegisterableEvent, SignalChangeEvent, FrameBufferingEvent, \
    FrameBufferedEvent, FrameTransferCompleteEvent, TransferCompleteEvent, PartialFrameTransferCompleteEvent, TimerEvent
from pymagewell.events.notification import Notification
from pymagewell.pro_capture_device.device_settings import TransferMode, ProCaptureSettings, ImageSizeInPixels


@dataclass
class FrameProperties:
    dimensions: ImageSizeInPixels
    size_in_bytes: int


class ProCaptureDevice(mw_capture):
    """ A ProCapture hardware device. Inherits from the mw_capture class provided by Magewell's python library.

    ProCaptureDevice is responsible for constructing and registering events with the Magewell driver. It also provides
     methods for accessing information about the video source connected to the device."""

    def __init__(self, settings: ProCaptureSettings):
        """ transfer_mode determines which events the device will raise to trigger a ProCaptureController to start
        transfer. n_lines_per_chunk sets the number lines after which a transfer will be triggered when
        transfer_mode is set to LowLatency."""
        super(ProCaptureDevice, self).__init__()
        self._settings = settings
        self.mw_capture_init_instance()
        self.mw_refresh_device()
        self._channel = create_channel(self)

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
    def num_lines_per_chunk(self) -> int:
        return self._settings.num_lines_per_chunk

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
    def buffer_status(self) -> OnDeviceBufferStatus:
        buffer_info = mwcap_video_buffer_info()
        self.mw_get_video_buffer_info(self.channel, buffer_info)
        return OnDeviceBufferStatus.from_mwcap_video_buffer_info(buffer_info)

    @property
    def frame_status(self) -> FrameStatus:
        frame_info = mwcap_video_frame_info()
        self.mw_get_video_frame_info(self.channel, self.buffer_status.last_buffered_frame_index, frame_info)
        return FrameStatus.from_mwcap_video_frame_info(frame_info)

    @property
    def signal_status(self) -> SignalStatus:
        mw_signal_status = mw_video_signal_status()
        self.mw_get_video_signal_status(self.channel, mw_signal_status)
        return SignalStatus.from_mw_video_signal_status(mw_signal_status)

    def start_grabbing(self) -> None:
        """ Starts the hardware acquiring frames"""
        start_capture_result = self.mw_start_video_capture(self.channel, self.transfer_complete_event.win32_event)
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
            self.mw_stop_video_capture(self.channel)
            self.shutdown()
            raise IOError('Signal not locked.')

    def stop(self) -> None:
        self.mw_stop_video_capture(self.channel)

    @property
    def fps(self) -> float:
        if self.signal_status.interlaced:
            fps = 2e7 / self.signal_status.frame_period_s
        else:
            fps = 1e7 / self.signal_status.frame_period_s
        return fps

    def print_signal_info(self) -> None:
        print(f"Input signal resolution: {self.signal_status.image_dimensions.cols} by "
              f"{self.signal_status.image_dimensions.rows}")
        print(f"Input signal FPS: {self.fps}")
        print(f"Input signal interlaced: {self.signal_status.interlaced}")
        print(f"Input signal frame segmented: {self.signal_status.interlaced}")

    @property
    def transfer_status(self) -> TransferStatus:
        """ Used to find out if a full frame has been transferred, or how many lines have been transferred, among other
        things."""
        mw_capture_status = mw_video_capture_status()
        self.mw_get_video_capture_status(self.channel, mw_capture_status)
        return TransferStatus.from_mw_video_capture_status(mw_capture_status)

    def get_device_time(self) -> mw_device_time:
        """ Read a timestamp from the device."""
        time = mw_device_time()
        result = self.mw_get_device_time(self.channel, time)
        if result != MW_SUCCEEDED:
            raise IOError("Failed to read time from device")
        else:
            return time

    def start_a_frame_transfer(self, frame_buffer: Array[c_char]) -> None:
        """ Start the transfer of lines from the device to a buffer in PC memory."""
        in_low_latency_mode = self.transfer_mode == TransferMode.LOW_LATENCY
        notify_size = self.num_lines_per_chunk if in_low_latency_mode else 0
        result = self.mw_capture_video_frame_to_virtual_address_ex(
            hchannel=self.channel,
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

import time
from ctypes import create_string_buffer, addressof, string_at
from functools import singledispatchmethod
from typing import Optional

import win32event

from mwcapture.libmwcapture import MWCAP_VIDEO_DEINTERLACE_BLEND, MWCAP_VIDEO_ASPECT_RATIO_CROPPING, \
    MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN, MWCAP_VIDEO_QUANTIZATION_UNKNOWN, MWCAP_VIDEO_SATURATION_UNKNOWN, MW_SUCCEEDED, \
    mwcap_video_frame_info
from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.events.events import SignalChangeEvent, Event, TimerEvent, FrameBufferedEvent, FrameBufferingEvent
from pymagewell.video_frame import VideoFrame
from pymagewell.settings import VideoSettings, GrabMode


class FrameGrabber:
    """ Controls the transfer of frames from ProCapture device to the PC."""

    def __init__(self, device: ProCaptureDevice, settings: VideoSettings):
        self._device = device
        self._settings = settings
        self._timer = FrameTimer(self._device)
        self._frame_buffer = create_string_buffer(3840*2160*4)
        self._device.start()

    def wait_and_grab(self, timeout_ms: int = 2000) -> VideoFrame:
        """ Wait for a frame to be ready for transfer, and then transfer it."""
        if self._settings.grab_mode == GrabMode.TIMER:
            self._timer.schedule_timer_event()
        event = self._wait_for_event(timeout_ms=timeout_ms)
        frame = self._handle_event(event)
        if frame is None:
            return self.wait_and_grab()
        else:
            return frame

    def _wait_for_event(self, timeout_ms: int) -> Event:
        """ Wait for events to be raised by the driver, and return the raised event."""
        if self._settings.grab_mode == GrabMode.TIMER:
            grab_event: Event = self._timer.event
        elif self._settings.grab_mode == GrabMode.NORMAL:
            grab_event = self._device.frame_buffered_event
        elif self._settings.grab_mode == GrabMode.LOW_LATENCY:
            grab_event = self._device.frame_buffering_event
        else:
            raise NotImplementedError("Invalid grab mode.")

        events_to_wait_for = [grab_event, self._device.signal_change_event]
        win32_events_to_wait_for = tuple([event.win32_event for event in events_to_wait_for])
        result = win32event.WaitForMultipleObjects(win32_events_to_wait_for, False, timeout_ms)
        if result == 258:
            self.shutdown()
            raise IOError("Error: wait timed out")
        elif result == win32event.WAIT_OBJECT_0 + 0:
            return events_to_wait_for[0]
        elif result == win32event.WAIT_OBJECT_0 + 1:
            return events_to_wait_for[1]
        else:
            raise IOError(f"Wait for event failed: error code {result}")

    @singledispatchmethod
    def _handle_event(self, event: Event) -> Optional[VideoFrame]:
        """ Handle a raised event, including transferring a frame if the event means one is ready."""
        raise NotImplementedError()

    @_handle_event.register
    def _(self, event: TimerEvent) -> Optional[VideoFrame]:
        """ If timer event received, then whole frame is on device. This method transfers it to a buffer in PC memory,
        makes a copy, marks the buffer memory as free and then returns the copy."""
        self._grab_frame()
        self._wait_for_transfer_to_complete(timeout_ms=2000)
        if not self._is_whole_frame_transferred:  # this marks the buffer memory as free
            raise IOError("Only part of frame has been acquired")
        return self._format_frame()

    @_handle_event.register
    def _(self, event: FrameBufferedEvent) -> Optional[VideoFrame]:
        """ If FrameBufferedEvent event received, then whole frame is on device. This method transfers it to a buffer in
        PC memory, makes a copy, marks the buffer memory as free and then returns the copy."""
        self._grab_frame()
        self._wait_for_transfer_to_complete(timeout_ms=2000)
        if not self._is_whole_frame_transferred:  # this marks the buffer memory as free
            raise IOError("Only part of frame has been acquired")
        return self._format_frame()

    @_handle_event.register
    def _(self, event: FrameBufferingEvent) -> Optional[VideoFrame]:
        """ If FrameBufferingEvent event received, then a frame has started to be acquired by the card. This method
        starts the transfer of the available lines to a buffer in PC memory while the acquisition is still happening.
         It then waits until all lines have been received (this query also frees the memory), copies the buffer contents
         and returns the copy."""
        self._grab_frame()
        self._wait_for_transfer_to_complete(timeout_ms=2000)
        t = time.perf_counter()
        while self._num_lines_transferred < self._settings.dimensions.y and (time.perf_counter() - t) < 1:
            # this marks the buffer memory as free
            pass

        return self._format_frame()

    @_handle_event.register
    def _(self, event: SignalChangeEvent) -> None:
        """ If a SignalChangeEvent is received, then the source signal has changed and no frame is available."""
        print("Frame grabber signal change detected")

    def _grab_frame(self) -> None:
        """ Start the transfer of lines from the device to a buffer in PC memory."""
        in_low_latency_mode = self._settings.grab_mode == GrabMode.LOW_LATENCY
        notify_size = self._settings.low_latency_mode_notify_size if in_low_latency_mode else 0
        result = self._device.mw_capture_video_frame_to_virtual_address_ex(
            hchannel=self._device.channel,
            iframe=self._device.buffer_info.iNewestBufferedFullFrame,
            pbframe=addressof(self._frame_buffer),
            cbframe=self._settings.image_size,
            cbstride=self._settings.min_stride,
            bbottomup=False,  # this is True in the C++ example, but false in python example,
            pvcontext=0,
            dwfourcc=self._settings.color_format,  # color format of captured frames
            cx=self._settings.dimensions.x,
            cy=self._settings.dimensions.y,
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

    @property
    def _is_whole_frame_transferred(self) -> bool:
        """ This reading of the capture status apparently "frees memory source" """
        return self._device.capture_status.bFrameCompleted

    @property
    def _num_lines_transferred(self) -> int:
        """ This reading of the capture status apparently "frees memory source" """
        return int(self._device.capture_status.cyCompleted)

    def _format_frame(self) -> VideoFrame:
        """ Copy the contents of the transfer buffer, and return it as a VideoFrame."""
        t = self._get_frame_timestamp(self._device.frame_info)
        # Copy the acquired frame
        string_buffer = string_at(self._frame_buffer, self._settings.image_size)
        frame = VideoFrame(string_buffer, dimensions=self._settings.dimensions, timestamp=t)
        return frame

    def _wait_for_transfer_to_complete(self, timeout_ms: int) -> None:
        """ Waits until a whole frame (or chunk of a frame in low latency mode) has been transferred to the buffer in
        PC memory."""
        result = win32event.WaitForSingleObject(self._device.transfer_complete_event.win32_event, timeout_ms)
        if result == 258:
            self.shutdown()
            raise IOError("Error: wait timed out")

    def _get_frame_timestamp(self, frame_info: mwcap_video_frame_info) -> int:
        time_now = self._device.get_device_time()
        if self._device.signal_status.bInterlaced:
            total_time = time_now.m_ll_device_time.value - frame_info.allFieldBufferedTimes[1]
        else:
            total_time = time_now.m_ll_device_time.value - frame_info.allFieldBufferedTimes[0]
        return total_time

    def shutdown(self) -> None:
        self._device.stop()
        self._device.shutdown()
        self._timer.shutdown()


class FrameTimer:
    def __init__(self, device: ProCaptureDevice):
        self._device = device
        self._frame_expire_time = self._device.get_device_time()
        self._timer_event = self._device.register_timer_event(TimerEvent())

    @property
    def event(self) -> TimerEvent:
        return self._timer_event

    def schedule_timer_event(self):
        self._frame_expire_time.m_ll_device_time.value += self._device.signal_status.dwFrameDuration
        if self._timer_event.is_registered:
            result = self._device.mw_schedule_timer(self._device.channel, self._timer_event.notification,
                                                    self._frame_expire_time.m_ll_device_time)
        else:
            raise IOError("Timer event not registered with device.")
        if result != MW_SUCCEEDED:
            raise IOError("Failed to schedule frame timer")

    def shutdown(self) -> None:
        self._timer_event.destroy()

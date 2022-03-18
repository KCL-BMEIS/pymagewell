import time
from ctypes import create_string_buffer, addressof, string_at
from functools import singledispatchmethod
from typing import Optional

import win32event

from mwcapture.libmwcapture import MWCAP_VIDEO_DEINTERLACE_BLEND, MWCAP_VIDEO_ASPECT_RATIO_CROPPING, \
    MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN, MWCAP_VIDEO_QUANTIZATION_UNKNOWN, MWCAP_VIDEO_SATURATION_UNKNOWN, MW_SUCCEEDED, \
    mwcap_video_frame_info, mw_device_time
from pymagewell.device import Device
from pymagewell.event import SignalChangeEvent, Event, TimerEvent, FrameBufferedEvent, FrameBufferingEvent
from pymagewell.frame import Frame
from pymagewell.settings import VideoSettings, GrabMode


class FrameGrabber:

    def __init__(self, device: Device, settings: VideoSettings):

        self._device = device
        self._settings = settings
        self._timer = FrameTimer(self._device)
        self._frame_buffer = create_string_buffer(3840*2160*4)
        self._device.start()

    def wait_and_grab(self) -> Frame:
        self._timer.schedule_timer_event()
        frame = self._wait_for_event(timeout_ms=2000)
        if frame is None:
            return self.wait_and_grab()
        else:
            return frame

    def _wait_for_event(self, timeout_ms: int) -> Optional[Frame]:

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
            return self._handle_event(events_to_wait_for[0])
        elif result == win32event.WAIT_OBJECT_0 + 1:
            return self._handle_event(events_to_wait_for[1])
        else:
            raise IOError(f"Wait for event failed: error code {result}")

    @singledispatchmethod
    def _handle_event(self, event: Event) -> Optional[Frame]:
        raise NotImplementedError()

    @_handle_event.register
    def _(self, event: TimerEvent) -> Optional[Frame]:
        self._grab_frame()
        self._wait_for_capture_to_complete(timeout_ms=2000)
        if not self._is_whole_frame_acquired:
            raise IOError("Only part of frame has been acquired")
        return self._format_frame()

    @_handle_event.register
    def _(self, event: FrameBufferedEvent) -> Optional[Frame]:
        self._grab_frame()
        self._wait_for_capture_to_complete(timeout_ms=2000)
        if not self._is_whole_frame_acquired:
            raise IOError("Only part of frame has been acquired")
        return self._format_frame()

    @_handle_event.register
    def _(self, event: FrameBufferingEvent) -> Optional[Frame]:
        self._grab_frame()
        self._wait_for_capture_to_complete(timeout_ms=2000)
        poll_count = 0
        while not self._is_whole_frame_acquired:
            time.sleep(1e-3)
            poll_count += 1
            if poll_count > 100:
                raise IOError("Timed out while polling for low latency frame.")
        print(f'Polled {poll_count} times')
        return self._format_frame()

    @_handle_event.register
    def _(self, event: SignalChangeEvent) -> None:
        print("Signal change detected")

    def _grab_frame(self) -> None:
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
            cypartialnotify=64 if self._settings.grab_mode == GrabMode.LOW_LATENCY else 0,
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
    def _is_whole_frame_acquired(self) -> bool:
        return self._device.capture_status.bFrameCompleted

    def _format_frame(self) -> Frame:
        t = self._get_frame_timestamp(self._device.frame_info)
        string_buffer = string_at(self._frame_buffer, self._settings.image_size)
        frame = Frame(string_buffer, dimensions=self._settings.dimensions, timestamp=t)
        return frame

    def _wait_for_capture_to_complete(self, timeout_ms: int) -> None:
        result = win32event.WaitForSingleObject(self._device.capture_event.win32_event, timeout_ms)
        if result == 258:
            self.shutdown()
            raise IOError("Error: wait timed out")

    def _get_frame_timestamp(self, frame_info: mwcap_video_frame_info) -> int:
        time_now = get_device_time(self._device)
        if self._device.signal_status.bInterlaced:
            total_time = time_now.m_ll_device_time.value - frame_info.allFieldBufferedTimes[1]
        else:
            total_time = time_now.m_ll_device_time.value - frame_info.allFieldBufferedTimes[0]
        return total_time

    def shutdown(self) -> None:
        self._device.mw_stop_video_capture(self._device.channel)
        self._device.shutdown()
        self._timer.shutdown()


class FrameTimer:
    def __init__(self, device: Device):
        self._device = device
        self._frame_expire_time = get_device_time(self._device)
        self._timer_event = TimerEvent()
        self._timer_notification = self._device.mw_register_timer(self._device.channel, self._timer_event.win32_event)

    @property
    def event(self) -> TimerEvent:
        return self._timer_event

    def schedule_timer_event(self):
        self._frame_expire_time.m_ll_device_time.value += self._device.signal_status.dwFrameDuration
        result = self._device.mw_schedule_timer(self._device.channel, self._timer_notification,
                                                self._frame_expire_time.m_ll_device_time)
        if result != MW_SUCCEEDED:
            raise IOError("Failed to schedule frame timer")

    def shutdown(self) -> None:
        self._timer_event.destroy()


def get_device_time(device: Device) -> mw_device_time:
    time = mw_device_time()
    result = device.mw_get_device_time(device.channel, time)
    if result != MW_SUCCEEDED:
        raise IOError("Failed to read time from device")
    else:
        return time

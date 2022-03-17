from ctypes import create_string_buffer, addressof, string_at
from functools import singledispatchmethod
from typing import Optional

import win32event
from PIL import Image

from mwcapture.libmwcapture import MWCAP_VIDEO_DEINTERLACE_BLEND, MWCAP_VIDEO_ASPECT_RATIO_CROPPING, \
    MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN, MWCAP_VIDEO_QUANTIZATION_UNKNOWN, MWCAP_VIDEO_SATURATION_UNKNOWN, MW_SUCCEEDED, \
    mwcap_video_frame_info, mw_device_time
from pymagewell.device import Device
from pymagewell.event import SignalChangeEvent, CaptureEvent, Event, TimerEvent
from pymagewell.frame import Frame
from pymagewell.settings import VideoSettings


class FrameGrabber:

    def __init__(self, device: Device, settings: VideoSettings):

        self._device = device
        self._settings = settings
        self._signal_change_event = SignalChangeEvent(self._device)
        self._capture_event = CaptureEvent(self._device)
        self._timer = FrameTimer(self._device)
        self._frame_buffer = create_string_buffer(3840*2160*4)
        self._device.start(self._capture_event.win32_event)

    def wait_and_grab(self) -> Frame:
        self._timer.schedule_timer_event()
        frame = self._wait_for_frame_or_signal_change(timeout_ms=2000)
        if frame is None:
            return self.wait_and_grab()
        else:
            return frame

    def _wait_for_frame_or_signal_change(self, timeout_ms: int) -> Optional[Frame]:
        win32_events = (self._timer.event.win32_event, self._signal_change_event.win32_event)
        result = win32event.WaitForMultipleObjects(win32_events, False, timeout_ms)
        if result == 258:
            self.shutdown()
            raise IOError("Error: wait timed out")
        elif result == win32event.WAIT_OBJECT_0 + 0:
            return self._handle_event(self._timer.event)
        elif result == win32event.WAIT_OBJECT_0 + 1:
            return self._handle_event(self._signal_change_event)
        else:
            raise IOError(f"Wait for event failed: error code {result}")

    @singledispatchmethod
    def _handle_event(self, event: Event) -> Optional[Frame]:
        raise NotImplementedError()

    @_handle_event.register
    def _(self, event: TimerEvent) -> Optional[Frame]:
        return self._grab_frame()

    @_handle_event.register
    def _(self, event: SignalChangeEvent) -> None:
        print("Signal change detected")

    def _grab_frame(self) -> Optional[Frame]:
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
            cypartialnotify=0,
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
        self._wait_for_capture_to_complete(timeout_ms=2000)

        if not self._device.capture_status.bFrameCompleted:
            raise IOError(f"Capture status says frame is not fully acquired yet")

        t = self._get_frame_timestamp(self._device.frame_info)
        string_buffer = string_at(self._frame_buffer, self._settings.image_size)
        frame = Frame(string_buffer, dimensions=self._settings.dimensions, timestamp=t)
        return frame

    def _wait_for_capture_to_complete(self, timeout_ms: int) -> None:
        result = win32event.WaitForSingleObject(self._capture_event.win32_event, timeout_ms)
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
        self._timer.shutdown()
        self._signal_change_event.destroy()
        self._capture_event.destroy()


class FrameTimer:
    def __init__(self, device: Device):
        self._device = device
        self._frame_expire_time = get_device_time(self._device)
        self._timer_event = TimerEvent(self._device)

    @property
    def event(self) -> TimerEvent:
        return self._timer_event

    def schedule_timer_event(self):
        self._frame_expire_time.m_ll_device_time.value += self._device.signal_status.dwFrameDuration
        result = self._device.mw_schedule_timer(self._device.channel, self._timer_event.registered_event,
                                                self._frame_expire_time.m_ll_device_time)
        if result != MW_SUCCEEDED:
            raise IOError("Failed to schedule frame timer")

    def shutdown(self) -> None:
        self._timer_event.destroy()


def get_device_time(device: Device) -> Optional[mw_device_time]:
    time = mw_device_time()
    result = device.mw_get_device_time(device.channel, time)
    if result != MW_SUCCEEDED:
        raise IOError("Failed to read time from device")
    else:
        return time
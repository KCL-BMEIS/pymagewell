""" This file was translated from the cpp example CaptureByInput.cpp"""
from copy import copy
from ctypes import create_unicode_buffer, create_string_buffer, addressof, string_at
from dataclasses import dataclass
from typing import Any, List, Optional

from PIL import Image
from win32 import win32api, win32event

from mwcapture.libmwcapture import mw_capture, fourcc_calc_min_stride, fourcc_calc_image_size, \
    MW_SUCCEEDED, mwcap_video_buffer_info, mwcap_video_frame_info, mw_video_signal_status, MWCAP_VIDEO_SIGNAL_NONE, \
    MWCAP_VIDEO_SIGNAL_UNSUPPORTED, MWCAP_VIDEO_SIGNAL_LOCKED, MWCAP_VIDEO_SIGNAL_LOCKING, \
    MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE, mw_notify_status, MWCAP_VIDEO_DEINTERLACE_BLEND, \
    MWCAP_VIDEO_ASPECT_RATIO_CROPPING, MWCAP_VIDEO_SATURATION_UNKNOWN, MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN, \
    MWCAP_VIDEO_QUANTIZATION_UNKNOWN, mw_video_capture_status, mw_device_time, MWFOURCC_NV12, MWFOURCC_YUY2, \
    MWFOURCC_RGB24

NUM_FRAMES_TO_CAPTURE = 5

@dataclass
class Dimensions:
    x: int
    y: int


@dataclass
class VideoSettings:
    color_format: int = MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN
    quantisation_range: int = MWCAP_VIDEO_QUANTIZATION_UNKNOWN
    saturation_range: int = MWCAP_VIDEO_SATURATION_UNKNOWN
    dimensions: Dimensions = Dimensions(1920, 1080)
    fourcc: int = MWFOURCC_RGB24  # Color format of captured video frames.

    @property
    def min_stride(self) -> int:
        return fourcc_calc_min_stride(self.fourcc, self.dimensions.x, 4)  # last arg is 2 in capture.py line 80

    @property
    def image_size(self) -> int:
        if self.fourcc == MWFOURCC_NV12:
            return self.dimensions.x * self.dimensions.y * 2  # copied from line 223 of capture.py
        else:
            return fourcc_calc_image_size(self.fourcc, self.dimensions.x, self.dimensions.y, self.min_stride)


def shutdown(capturer: mw_capture, channel: int, events: List[Any]) -> None:
    capturer.mw_close_channel(channel)
    for event in events:
        win32api.CloseHandle(int(event))
    capturer.mw_capture_exit_instance()


def get_device_time(channel: int) -> Optional[mw_device_time]:
    t_ll_begin = mw_device_time()
    t_ret = capturer.mw_get_device_time(channel, t_ll_begin)
    if t_ret != MW_SUCCEEDED:
        return None
    else:
        return t_ll_begin


def add_time_to_a_device_time(device_time: mw_device_time, time_to_add: int) -> mw_device_time:
    device_time.m_ll_device_time.value += time_to_add
    return device_time


if __name__ == '__main__':

    video_settings = VideoSettings()

    # Create device
    capturer = mw_capture()
    capturer.mw_capture_init_instance()
    capturer.mw_refresh_device()

    # Create channel
    t_path = create_unicode_buffer(128)
    capturer.mw_get_device_path(0, t_path)
    channel = capturer.mw_open_channel_by_path(t_path)

    # Create events
    capture_event = win32event.CreateEvent(None, False, False, None)
    notify_event = win32event.CreateEvent(None, False, False, None)
    timer_event = win32event.CreateEvent(None, False, False, None)

    # Configure timer
    start_time = get_device_time(channel)
    frame_expire_time = copy(start_time)


    # Start capture
    start_capture_result = capturer.mw_start_video_capture(channel, capture_event)
    if start_capture_result != MW_SUCCEEDED:
        raise IOError(f"Start capture failed (error code {start_capture_result}).")

    # Create empty buffer info object then write to it
    buffer_info = mwcap_video_buffer_info()
    capturer.mw_get_video_buffer_info(channel, buffer_info)

    # Create empty frame info object then write to it
    frame_info = mwcap_video_frame_info()
    capturer.mw_get_video_frame_info(channel, buffer_info.iNewestBufferedFullFrame, frame_info)

    # Create empty signal status object then write to it
    signal_status = mw_video_signal_status()
    capturer.mw_get_video_signal_status(channel, signal_status)

    # Check status of input signal
    if signal_status.state == MWCAP_VIDEO_SIGNAL_NONE:
        print("Input signal status: None")
    elif signal_status.state == MWCAP_VIDEO_SIGNAL_UNSUPPORTED:
        print("Input signal status: Unsupported")
    elif signal_status.state == MWCAP_VIDEO_SIGNAL_LOCKING:
        print("Input signal status: Locking")
    elif signal_status.state == MWCAP_VIDEO_SIGNAL_LOCKED:
        print("Input signal status: Locked")

    # Exit if signal not locked
    if signal_status.state != MWCAP_VIDEO_SIGNAL_LOCKED:
        capturer.mw_stop_video_capture(channel)
        shutdown(capturer, channel, [capture_event, notify_event])
        raise IOError('Signal not locked.')

    # Print properties of input signal
    print(f"Input signal resolution: {signal_status.cx} by {signal_status.cy}")
    if signal_status.bInterlaced:
        fps = 2e7 / signal_status.dwFrameDuration
    else:
        fps = 1e7 / signal_status.dwFrameDuration
    print(f"Input signal FPS: {fps}")
    print(f"Input signal interlaced: {signal_status.bInterlaced}")
    print(f"Input signal frame segmented: {signal_status.bSegmentedFrame}")

    # Register notification event
    # this is MWCAP_NOTIFY_VIDEO_FRAME_BUFFERED in the C++ example, but for soem reason that constant is
    # not defined in libmwcapture.py, so using MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE (like in capture.py)
    registered_notifier = capturer.mw_register_notify(channel, notify_event, MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE)
    if registered_notifier == 0:
        capturer.mw_stop_video_capture(channel)
        shutdown(capturer, channel, [capture_event, notify_event])
        raise IOError('Register Notify error.')

    # Register timer
    registered_timer = capturer.mw_register_timer(channel, timer_event)

    # Capture frames
    print(f"Starting to capturing {NUM_FRAMES_TO_CAPTURE} frames at {fps} Hz")
    stop_flag: bool = False
    frame_buffer = create_string_buffer(3840*2160*4)

    images = []

    for i in range(NUM_FRAMES_TO_CAPTURE):
        if stop_flag:
            break

        frame_expire_time = add_time_to_a_device_time(frame_expire_time, signal_status.dwFrameDuration)
        time_now = get_device_time(channel)
        ret = capturer.mw_schedule_timer(channel, registered_timer, frame_expire_time.m_ll_device_time)
        if ret != MW_SUCCEEDED:
            continue

        # Wait for timer or change notification and catch timeout response
        notify_events = (timer_event, notify_event)
        t_wait_ret = win32event.WaitForMultipleObjects(notify_events, False, 2000)  # win32event.INFINITE)
        if t_wait_ret == 258:
            print("Error: wait notify timeout")
            break
        elif t_wait_ret == win32event.WAIT_OBJECT_0 + 0:
            print("Timer event")

            # Create notification status and write the status to it
            # Skip this frame if could not get notification status
            status = mw_notify_status()
            res = capturer.mw_get_notify_status(channel, registered_notifier, status)
            if res != MW_SUCCEEDED:
                continue

            # Get buffer info, skip this frame if can't
            res = capturer.mw_get_video_buffer_info(channel, buffer_info)
            if res != MW_SUCCEEDED:
                continue

            # Get frame info, skip this frame id can't
            res = capturer.mw_get_video_frame_info(channel, buffer_info.iNewestBufferedFullFrame, frame_info)
            if res != MW_SUCCEEDED:
                continue

            # # if detected signal change, skip this frame
            # if (status.m_ll_notify_status & MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE) == 0:
            #     print("Detected signal change")
            #     continue

            # Capture a frame, skip frame if capture fails
            res = capturer.mw_capture_video_frame_to_virtual_address_ex(
                hchannel=channel,
                iframe=buffer_info.iNewestBufferedFullFrame,
                pbframe=addressof(frame_buffer),
                cbframe=video_settings.image_size,
                cbstride=video_settings.min_stride,
                bbottomup=False,  # this is True in the C++ example, but false in capture.py,
                pvcontext=0,  # This is 0 in both C++ example and capture.py
                dwfourcc=video_settings.fourcc,  # color format of captured frames
                cx=video_settings.dimensions.x,
                cy=video_settings.dimensions.y,
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
                prectsrc=0,  # 0 in C++ example, but configured using CLIP settings in capture.py,
                prectdest=0,
                naspectx=0,
                naspecty=0,
                colorformat=video_settings.color_format,
                quantrange=video_settings.quantisation_range,
                satrange=video_settings.saturation_range
            )
            if res != MW_SUCCEEDED:
                continue

            # Wait for capture event and catch timeout response
            win32event.WaitForSingleObject(capture_event, win32event.INFINITE)  # wait time is 1000 in C++ example

            # Read capture status
            capture_status = mw_video_capture_status()
            capturer.mw_get_video_capture_status(channel, capture_status)

            # Get capture time (latency?)
            time_now = mw_device_time()
            capturer.mw_get_device_time(channel, time_now)
            if signal_status.bInterlaced:
                total_time = time_now.m_ll_device_time.value - frame_info.allFieldBufferedTimes[1]
            else:
                total_time = time_now.m_ll_device_time.value - frame_info.allFieldBufferedTimes[0]

            print(f"Captured frame of size {len(frame_buffer)}.")
            print(f"Total time was {total_time}.")
        elif t_wait_ret == win32event.WAIT_OBJECT_0 + 1:
            print("Signal change detected")
        else:
            continue

        t_str_buf = string_at(frame_buffer, video_settings.image_size)
        images.append(Image.frombuffer(mode="RGB",
                                       size=(video_settings.dimensions.x, video_settings.dimensions.y),
                                       data=t_str_buf))

    # Shutdown
    capturer.mw_unregister_notify(channel, registered_notifier)
    capturer.mw_stop_video_capture(channel)
    shutdown(capturer, channel, [capture_event, notify_event])
    capture_event = 0
    notify_event = 0

    for image in images:
        image.show()

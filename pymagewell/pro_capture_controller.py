import time
from ctypes import create_string_buffer, string_at
from functools import singledispatchmethod
from typing import Optional

import win32event

from mwcapture.libmwcapture import MW_SUCCEEDED, \
    mwcap_video_frame_info
from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.events.events import SignalChangeEvent, Event, TimerEvent, FrameBufferedEvent, FrameBufferingEvent
from pymagewell.video_frame import VideoFrame
from pymagewell.pro_capture_device.device_settings import TransferMode


class ProCaptureController:
    """ Controls the transfer of frames from ProCaptureDevice to the PC."""

    def __init__(self, device: ProCaptureDevice):
        self._device = device
        self._timer = FrameTimer(self._device)
        self._transfer_buffer = create_string_buffer(3840 * 2160 * 4)
        self._device.start_grabbing()

    def transfer_when_ready(self, timeout_ms: int = 2000) -> VideoFrame:
        """ Wait for a frame to be ready for transfer, and then transfer it."""
        if self._device.transfer_mode == TransferMode.TIMER:
            self._timer.schedule_timer_event()
        event = self._wait_for_event(timeout_ms=timeout_ms)
        frame = self._handle_event(event)
        if frame is None:
            return self.transfer_when_ready()
        else:
            return frame

    def _wait_for_event(self, timeout_ms: int) -> Event:
        """ Wait for events to be raised by the ProCaptureDevice or Timer, and return the raised event."""
        if self._device.transfer_mode == TransferMode.TIMER:
            grab_event: Event = self._timer.event
        elif self._device.transfer_mode == TransferMode.NORMAL:
            grab_event = self._device.frame_buffered_event
        elif self._device.transfer_mode == TransferMode.LOW_LATENCY:
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
        self._device.start_a_frame_transfer(self._transfer_buffer)
        self._wait_for_transfer_to_complete(timeout_ms=2000)
        if not self._device.transfer_status.whole_frame_transferred:  # this marks the buffer memory as free
            raise IOError("Only part of frame has been acquired")
        return self._format_frame()

    @_handle_event.register
    def _(self, event: FrameBufferedEvent) -> Optional[VideoFrame]:
        """ If FrameBufferedEvent event received, then whole frame is on device. This method transfers it to a buffer in
        PC memory, makes a copy, marks the buffer memory as free and then returns the copy."""
        self._device.start_a_frame_transfer(self._transfer_buffer)
        self._wait_for_transfer_to_complete(timeout_ms=2000)
        if not self._device.transfer_status.whole_frame_transferred:  # this marks the buffer memory as free
            raise IOError("Only part of frame has been acquired")
        return self._format_frame()

    @_handle_event.register
    def _(self, event: FrameBufferingEvent) -> Optional[VideoFrame]:
        """ If FrameBufferingEvent event received, then a frame has started to be acquired by the card. This method
        starts the transfer of the available lines to a buffer in PC memory while the acquisition is still happening.
         It then waits until all lines have been received (this query also frees the memory), copies the buffer contents
         and returns the copy."""
        self._device.start_a_frame_transfer(self._transfer_buffer)
        self._wait_for_transfer_to_complete(timeout_ms=2000)
        t = time.perf_counter()
        while self._device.transfer_status.num_lines_transferred < self._device.frame_dimensions.rows and (
                time.perf_counter() - t) < 1:
            # this marks the buffer memory as free
            pass

        return self._format_frame()

    @_handle_event.register
    def _(self, event: SignalChangeEvent) -> None:
        """ If a SignalChangeEvent is received, then the source signal has changed and no frame is available."""
        print("Frame grabber signal change detected")

    def _format_frame(self) -> VideoFrame:
        """ Copy the contents of the transfer buffer, and return it as a VideoFrame."""
        t = self._device.frame_status.top_frame_time_code
        # Copy the acquired frame
        string_buffer = string_at(self._transfer_buffer, self._device.frame_properties.size_in_bytes)
        frame = VideoFrame(string_buffer, dimensions=self._device.frame_properties.dimensions, timestamp=t)
        return frame

    def _wait_for_transfer_to_complete(self, timeout_ms: int) -> None:
        """ Waits until a whole frame (or chunk of a frame in low latency mode) has been transferred to the buffer in
        PC memory."""
        result = win32event.WaitForSingleObject(self._device.transfer_complete_event.win32_event, timeout_ms)
        if result == 258:
            self.shutdown()
            raise IOError("Error: wait timed out")

    def shutdown(self) -> None:
        self._device.stop()
        self._device.shutdown()
        self._timer.shutdown()


class FrameTimer:
    """ If the devices transfer mode it "Timer", this class is used to generate events triggering the transfer of frames
    from the device."""
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

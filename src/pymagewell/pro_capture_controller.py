import logging
import time
from ctypes import create_string_buffer, string_at
from datetime import datetime
from functools import singledispatchmethod
from typing import Optional

from pymagewell.events.event_base import wait_for_events, wait_for_event
from pymagewell.events.device_events import (
    SignalChangeEvent,
    Event,
    TimerEvent,
    FrameBufferedEvent,
    FrameBufferingEvent,
)
from pymagewell.pro_capture_device.device_interface import ProCaptureDeviceInterface
from pymagewell.exceptions import ProCaptureError, WaitForEventTimeout
from pymagewell.video_frame import VideoFrame, VideoFrameTimestamps
from pymagewell.pro_capture_device.device_settings import TransferMode

logger = logging.getLogger(__name__)


class ProCaptureController:
    """ProCaptureController controls the transfer of frames from a ProCaptureDevice or MockProCaptureDevice to a PC."""

    def __init__(self, device: ProCaptureDeviceInterface):
        """
        Args:
            device (ProCaptureDeviceInterface): The implementation of ProCaptureDeviceInterface to use for frame
              transfer. ProCaptureDevice or MockProCaptureDevice are both valid implementations.
        """
        self._device = device
        self._transfer_buffer = create_string_buffer(3840 * 2160 * 4)
        self._device.start_grabbing()

    def transfer_when_ready(self, timeout_ms: int = 2000) -> VideoFrame:
        """transfer_when_ready wait for the device to be ready to start transferring, transfers it and returns it.

        This method will block until the frame has been transferred or the timeout has been reached.

        In TransferMode.TIMER and TransferMode.NORMAL, frame transfer will start after a whole frame has been grabbed
          by the device. In TransferMode.LOW_LATENCY, frame transfer will start after a frame has started to be
          buffered onto the device.
        """
        if self._device.transfer_mode == TransferMode.TIMER:
            self._device.schedule_timer_event()
        event = self._wait_for_event(timeout_ms=timeout_ms)
        frame = self._handle_event(event)
        if frame is None:
            return self.transfer_when_ready()
        else:
            return frame

    def _wait_for_event(self, timeout_ms: int) -> Event:
        """Wait for events to be raised by the ProCaptureDevice or Timer, and return the raised event."""
        if self._device.transfer_mode == TransferMode.TIMER:
            grab_event: Event = self._device.events.timer_event
        elif self._device.transfer_mode == TransferMode.NORMAL:
            grab_event = self._device.events.frame_buffered
        elif self._device.transfer_mode == TransferMode.LOW_LATENCY:
            grab_event = self._device.events.frame_buffering
        else:
            raise NotImplementedError("Invalid grab mode.")

        events_to_wait_for = [grab_event, self._device.events.signal_change]
        try:
            event_that_occurred = wait_for_events(events_to_wait_for, timeout_ms=timeout_ms)
        except WaitForEventTimeout as e:
            self.shutdown()
            raise e
        return event_that_occurred

    @singledispatchmethod
    def _handle_event(self, event: Event) -> Optional[VideoFrame]:
        """Handle a raised event, including transferring a frame if the event means one is ready."""
        raise NotImplementedError()

    @_handle_event.register
    def _(self, event: TimerEvent) -> Optional[VideoFrame]:
        """If timer event received, then whole frame is on device. Only subscribed to in TIMER mode. This method
        transfers the frame to a buffer in PC memory, makes a copy, marks the buffer memory as free and then returns
        the copy."""
        transfer_started_timestamp = self._device.start_a_frame_transfer(self._transfer_buffer)
        buffering_started_timestamp = self._device.frame_info.buffering_start_time
        transfer_complete_timestamp = self._wait_for_frame_or_chunk_transfer_to_complete(timeout_ms=2000)
        buffering_complete_timestamp = self._device.frame_info.buffering_complete_time
        if not self._device.transfer_status.whole_frame_transferred:  # this marks the buffer memory as free
            raise ProCaptureError("Only part of frame has been acquired")
        return self._format_frame(
            timestamps=VideoFrameTimestamps(
                transfer_started=transfer_started_timestamp,
                transfer_complete=transfer_complete_timestamp,
                buffering_started=buffering_started_timestamp,
                buffering_complete=buffering_complete_timestamp,
            )
        )

    @_handle_event.register
    def _(self, event: FrameBufferedEvent) -> Optional[VideoFrame]:
        """If FrameBufferedEvent event received, then whole frame is on device. This event is only subscribed to in
        NORMAL mode. This method transfers it to a buffer in PC memory, makes a copy, marks the buffer memory as free
        and then returns the copy."""
        transfer_started_timestamp = self._device.start_a_frame_transfer(self._transfer_buffer)
        transfer_complete_timestamp = self._wait_for_frame_or_chunk_transfer_to_complete(timeout_ms=2000)
        buffering_started_timestamp = self._device.frame_info.buffering_start_time
        buffering_complete_timestamp = self._device.frame_info.buffering_complete_time
        if not self._device.transfer_status.whole_frame_transferred:  # this marks the buffer memory as free
            raise ProCaptureError("Only part of frame has been acquired")
        return self._format_frame(
            timestamps=VideoFrameTimestamps(
                transfer_started=transfer_started_timestamp,
                transfer_complete=transfer_complete_timestamp,
                buffering_started=buffering_started_timestamp,
                buffering_complete=buffering_complete_timestamp,
            )
        )

    @_handle_event.register
    def _(self, event: FrameBufferingEvent) -> Optional[VideoFrame]:
        """If FrameBufferingEvent event received, then a frame has started to be acquired by the card. This event is
        only subscribed to in LOW_LATENCY mode. This method starts the transfer of the available lines to a buffer in
        PC memory while the acquisition is still happening. It then waits until all lines have been received (this query
        also frees the memory), copies the buffer contents and returns the copy."""
        transfer_started_timestamp = self._device.start_a_frame_transfer(self._transfer_buffer)
        buffering_started_timestamp = self._device.frame_info.buffering_start_time
        self._wait_for_frame_or_chunk_transfer_to_complete(timeout_ms=2000)
        wait_start_t = time.perf_counter()
        while (
            self._device.transfer_status.num_lines_transferred < self._device.frame_properties.dimensions.rows
            and (time.perf_counter() - wait_start_t) < 1
        ):
            pass
        transfer_complete_timestamp = datetime.now()
        buffering_complete_timestamp = self._device.frame_info.buffering_complete_time

        return self._format_frame(
            timestamps=VideoFrameTimestamps(
                transfer_started=transfer_started_timestamp,
                transfer_complete=transfer_complete_timestamp,
                buffering_started=buffering_started_timestamp,
                buffering_complete=buffering_complete_timestamp,
            )
        )

    @_handle_event.register
    def _(self, event: SignalChangeEvent) -> None:
        """If a SignalChangeEvent is received, then the source signal has changed and no frame is available."""
        logger.info("Frame grabber signal change detected")

    def _format_frame(self, timestamps: VideoFrameTimestamps) -> VideoFrame:
        """Copy the contents of the transfer buffer, and return it as a VideoFrame."""
        # Copy the acquired frame
        string_buffer = string_at(self._transfer_buffer, self._device.frame_properties.size_in_bytes)
        frame = VideoFrame(
            string_buffer,
            dimensions=self._device.frame_properties.dimensions,
            timestamps=timestamps,
        )
        return frame

    def _wait_for_frame_or_chunk_transfer_to_complete(self, timeout_ms: int) -> datetime:
        """Waits until a whole frame (or chunk of a frame in low latency mode) has been transferred to the buffer in
        PC memory."""
        try:
            wait_for_event(self._device.events.transfer_complete, timeout_ms=timeout_ms)
            return datetime.now()
        except WaitForEventTimeout as e:
            self.shutdown()
            raise e

    def shutdown(self) -> None:
        """Shuts down the frame grabber device."""
        self._device.stop_grabbing()
        self._device.shutdown()

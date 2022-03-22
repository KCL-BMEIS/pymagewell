from ctypes import Array, c_char
from threading import Thread
from time import monotonic, sleep
from typing import Optional

import win32event
from numpy import random

from pymagewell.events.events import TransferCompleteEvent, SignalChangeEvent, FrameBufferedEvent, FrameBufferingEvent, \
    TimerEvent
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, ImageSizeInPixels, AspectRatio, \
    FrameTimeCode, ImageCoordinateInPixels
from pymagewell.pro_capture_device.device_status import TransferStatus, SignalStatus, FrameStatus, OnDeviceBufferStatus, \
    FrameState, SignalState
from pymagewell.pro_capture_device.pro_capture_device_impl import ProCaptureDeviceImpl
from pymagewell.pro_capture_device.device_interface import ProCaptureEvents

MOCK_RESOLUTION = ImageSizeInPixels(cols=1920, rows=1080)
MOCK_ASPECT_RATIO = AspectRatio(hor=16, ver=9)
MOCK_FRAME_RATE_HZ = 60.0


class MockProCaptureDevice(ProCaptureDeviceImpl):
    def __init__(self, settings: ProCaptureSettings):
        super().__init__(settings)
        self._is_grabbing = False
        self._events = ProCaptureEvents(
            transfer_complete=TransferCompleteEvent(),
            signal_change=SignalChangeEvent(),
            frame_buffered=FrameBufferedEvent(),
            frame_buffering=FrameBufferingEvent(),
            timer_event=TimerEvent()
        )
        self._mock_timer = MockTimer(self._events.timer_event, MOCK_FRAME_RATE_HZ)

    @property
    def events(self) -> ProCaptureEvents:
        return self._events

    def schedule_timer_event(self) -> None:
        self._mock_timer.schedule_event()

    @property
    def buffer_status(self) -> OnDeviceBufferStatus:
        return OnDeviceBufferStatus(
            buffer_size_in_frames=1,
            num_chunks_in_buffer=1,
            buffering_field_index=1,
            last_buffered_field_index=1,
            last_buffered_frame_index=1,
            num_fully_buffered_frames=1,
            num_chunks_being_buffered=1
        )

    @property
    def frame_status(self) -> FrameStatus:
        now_time_code = FrameTimeCode.now(frame_period_s=self.signal_status.frame_period_s)
        return FrameStatus(
            state=FrameState.BUFFERED,
            interlaced=False,
            segmented=False,
            dimensions=MOCK_RESOLUTION,
            aspect_ratio=MOCK_ASPECT_RATIO,
            top_frame_time_code=now_time_code,
            bottom_frame_time_code=now_time_code
        )

    @property
    def signal_status(self) -> SignalStatus:
        return SignalStatus(
            state=SignalState.LOCKED,
            start_position=ImageCoordinateInPixels(row=0, col=0),
            image_dimensions=MOCK_RESOLUTION,
            total_dimensions=MOCK_RESOLUTION,
            interlaced=False,
            frame_period_s=1/MOCK_FRAME_RATE_HZ,
            aspect_ratio=MOCK_ASPECT_RATIO,
            segmented=False,
        )

    @property
    def transfer_status(self) -> TransferStatus:
        return TransferStatus(
            whole_frame_transferred=True,
            num_lines_transferred=MOCK_RESOLUTION.rows,
            num_lines_transferred_previously=MOCK_RESOLUTION.rows,
            frame_index=0
        )

    def start_grabbing(self) -> None:
        self._is_grabbing = True

    def stop_grabbing(self) -> None:
        self._is_grabbing = False

    def start_a_frame_transfer(self, frame_buffer: Array[c_char]) -> None:
        frame_buffer = random.rand(MOCK_RESOLUTION.rows, MOCK_RESOLUTION.cols)
        win32event.SetEvent(self.events.transfer_complete.win32_event)

    def shutdown(self) -> None:
        self._is_grabbing = False


class MockTimer:

    def __init__(self, timer_event: TimerEvent, rate_hz: float):
        self._last_event_time: Optional[float] = None
        self._timer_event_thread = Thread(target=self._wait_and_generate)
        self._rate_hz = rate_hz
        self._timer_event = timer_event

    def schedule_event(self) -> None:
        self._timer_event_thread = Thread(target=self._wait_and_generate)
        self._timer_event_thread.start()

    def _wait_and_generate(self):
        if self._last_event_time is not None:
            time_since_last_event = monotonic() - self._last_event_time
            time_until_next_event = (1.0 / self._rate_hz) - time_since_last_event
            if time_until_next_event > 0:
                sleep(time_until_next_event)
        win32event.SetEvent(self._timer_event.win32_event)




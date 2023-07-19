import logging
from ctypes import Array, c_char
from datetime import datetime
from operator import mod
from threading import Thread
from time import monotonic, sleep
from typing import List, Optional

from cv2 import circle, FONT_HERSHEY_SIMPLEX, putText, LINE_AA
from numpy import uint8, zeros
from numpy.typing import NDArray

from pymagewell.conversion import FFMPEG
from pymagewell.events.device_events import (
    TransferCompleteEvent,
    SignalChangeEvent,
    FrameBufferedEvent,
    FrameBufferingEvent,
    TimerEvent,
)
from pymagewell.events.notification import Notification
from pymagewell.pro_capture_device.device_interface import ProCaptureEvents
from pymagewell.pro_capture_device.device_settings import (
    ColourFormat,
    ProCaptureSettings,
    ImageSizeInPixels,
    AspectRatio,
    ImageCoordinateInPixels,
    TransferMode,
)
from pymagewell.pro_capture_device.device_status import (
    TransferStatus,
    SignalStatus,
    FrameInfo,
    OnDeviceBufferStatus,
    FrameState,
    SignalState,
)
from pymagewell.pro_capture_device.pro_capture_device_impl import ProCaptureDeviceImpl

logger = logging.getLogger(__name__)


MOCK_RESOLUTION = ImageSizeInPixels(cols=1920, rows=1080)
MOCK_ASPECT_RATIO = AspectRatio(hor=16, ver=9)
MOCK_FRAME_RATE_HZ = 2

MOCK_FRAME_FONT_SIZE = 1
MOCK_FRAME_LINE_WIDTH = 1
NUM_TEST_FRAMES = 10


class MockProCaptureDevice(ProCaptureDeviceImpl):
    """MockProCaptureDevice is intended to be used during testing, development and CI in the absence of a hardware frame
    grabber or Magewell Windows SDK. Does not require Magewell driver or hardware.

    Only TransferMode.Timer is supported.

    The class generates test frames. The frame rate is limited to 2 frames per second because copying the mock frames
    to a provided PC transfer buffer takes a surprisingly long time (~0.11s).

    It's recommended to use ColourFormat.RGB24 only. You can use some other formats if you have ffmpeg installed, but
    this is quite slow."""

    def __init__(self, settings: ProCaptureSettings):
        """
        Args:
            settings (ProCaptureSettings): The settings to use for the mock device. settings.transfer_mode must be
              set to TransferMode.Timer.
        """
        if settings.transfer_mode != TransferMode.TIMER:
            raise ValueError("MockProCaptureDevice only works in Timer transfer mode.")
        super().__init__(settings)
        self._is_grabbing = False
        self._events = ProCaptureEvents(
            transfer_complete=TransferCompleteEvent(),
            signal_change=SignalChangeEvent(),
            frame_buffered=FrameBufferedEvent(),
            frame_buffering=FrameBufferingEvent(),
            timer_event=TimerEvent(),
        )
        self._events.signal_change.register(Notification(0, 0))
        self._events.timer_event.register(Notification(0, 0))

        self._mock_timer = _MockTimer(self._events.timer_event, MOCK_FRAME_RATE_HZ)

        self._frame_counter: int = 0
        mock_frames_np_arrays = [create_mock_frame() for _ in range(NUM_TEST_FRAMES)]
        for i, frame in enumerate(mock_frames_np_arrays):
            putText(
                frame,
                str(i),
                (frame.shape[1] // 2, frame.shape[0] // 2),
                FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                1,
                LINE_AA,
            )
        self._mock_frames: List[bytes] = []
        if self.frame_properties.format == ColourFormat.RGB24:
            self._mock_frames = [frame.tobytes() for frame in mock_frames_np_arrays]
        else:
            ffmpeg = FFMPEG("FFMPEG is required to use Mock mode with any colour format other than RGB24.")
            self._mock_frames = [
                ffmpeg.encode_rgb24_array(frame, self.frame_properties.format) for frame in mock_frames_np_arrays
            ]

    @property
    def events(self) -> ProCaptureEvents:
        """events property
        Returns:
            A `ProCaptureEvents` object containing handles to the events generated by the device during frame grabbing.
        """
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
            num_chunks_being_buffered=1,
        )

    @property
    def frame_info(self) -> FrameInfo:
        return FrameInfo(
            state=FrameState.BUFFERED,
            interlaced=False,
            segmented=False,
            dimensions=MOCK_RESOLUTION,
            aspect_ratio=MOCK_ASPECT_RATIO,
            buffering_start_time=datetime.now(),
            buffering_complete_time=datetime.now(),
        )

    @property
    def signal_status(self) -> SignalStatus:
        return SignalStatus(
            state=SignalState.LOCKED,
            start_position=ImageCoordinateInPixels(row=0, col=0),
            image_dimensions=MOCK_RESOLUTION,
            total_dimensions=MOCK_RESOLUTION,
            interlaced=False,
            frame_period_s=1 / MOCK_FRAME_RATE_HZ,
            aspect_ratio=MOCK_ASPECT_RATIO,
            segmented=False,
        )

    @property
    def transfer_status(self) -> TransferStatus:
        return TransferStatus(
            whole_frame_transferred=True,
            num_lines_transferred=MOCK_RESOLUTION.rows,
            num_lines_transferred_previously=MOCK_RESOLUTION.rows,
            frame_index=0,
        )

    def start_grabbing(self) -> None:
        self._is_grabbing = True

    def stop_grabbing(self) -> None:
        self._is_grabbing = False

    def start_a_frame_transfer(self, frame_buffer: Array[c_char]) -> datetime:
        """start_a_frame_transfer immediately writes a mock frame to the provided buffer.
        Args:
            frame_buffer (Array[c_char]): The buffer to write the mock frame to.
        Returns:
            The time (datetime.datetime) the frame transfer was completed.
        """
        frame_buffer[: self.frame_properties.size_in_bytes] = self._mock_frames[  # type: ignore
            self._frame_counter % NUM_TEST_FRAMES
        ]
        self.events.transfer_complete.set()
        self._frame_counter += 1
        return datetime.now()

    def shutdown(self) -> None:
        self._is_grabbing = False


def create_mock_frame() -> NDArray[uint8]:
    """Creates a mock frame in RGB24 format as a NumPy array. Used by MockProCaptureDevice."""
    rgb_frame: NDArray[uint8] = zeros((MOCK_RESOLUTION.rows, MOCK_RESOLUTION.cols, 3), dtype=uint8)

    white_fit_width_radius = MOCK_RESOLUTION.cols // 2
    circle(rgb_frame, (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2), white_fit_width_radius, (255, 255, 255))
    putText(
        rgb_frame,
        "White",
        (MOCK_RESOLUTION.cols // 2 - white_fit_width_radius, MOCK_RESOLUTION.rows // 2),
        FONT_HERSHEY_SIMPLEX,
        MOCK_FRAME_FONT_SIZE,
        (255, 255, 255),
        MOCK_FRAME_LINE_WIDTH,
        LINE_AA,
    )

    white_fit_height_radius = MOCK_RESOLUTION.rows // 2
    circle(rgb_frame, (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2), white_fit_height_radius, (255, 255, 255))
    putText(
        rgb_frame,
        "White",
        (MOCK_RESOLUTION.cols // 2 - white_fit_height_radius, MOCK_RESOLUTION.rows // 2),
        FONT_HERSHEY_SIMPLEX,
        MOCK_FRAME_FONT_SIZE,
        (255, 255, 255),
        MOCK_FRAME_LINE_WIDTH,
        LINE_AA,
    )

    ch1_radius = MOCK_RESOLUTION.rows // 4
    circle(rgb_frame, (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2), ch1_radius, (255, 0, 0))
    putText(
        rgb_frame,
        "red",
        (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2 - ch1_radius),
        FONT_HERSHEY_SIMPLEX,
        MOCK_FRAME_FONT_SIZE,
        (255, 0, 0),
        MOCK_FRAME_LINE_WIDTH,
        LINE_AA,
    )

    ch2_radius = MOCK_RESOLUTION.rows // 6
    circle(rgb_frame, (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2), ch2_radius, (0, 255, 0))
    putText(
        rgb_frame,
        "green",
        (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2 - ch2_radius),
        FONT_HERSHEY_SIMPLEX,
        MOCK_FRAME_FONT_SIZE,
        (0, 255, 0),
        MOCK_FRAME_LINE_WIDTH,
        LINE_AA,
    )

    ch3_radius = MOCK_RESOLUTION.rows // 8
    circle(rgb_frame, (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2), ch3_radius, (0, 0, 255))
    putText(
        rgb_frame,
        "blue",
        (MOCK_RESOLUTION.cols // 2, MOCK_RESOLUTION.rows // 2 - ch3_radius),
        FONT_HERSHEY_SIMPLEX,
        MOCK_FRAME_FONT_SIZE,
        (0, 0, 255),
        MOCK_FRAME_LINE_WIDTH,
        LINE_AA,
    )

    return rgb_frame


class _MockTimer:
    def __init__(self, timer_event: TimerEvent, rate_hz: float):
        self._last_event_time: Optional[float] = None
        self._timer_event_thread = Thread(target=self._wait_and_generate)
        self._rate_hz = rate_hz
        self._timer_event = timer_event
        self._event_counter = 0

    def schedule_event(self) -> None:
        self._timer_event_thread = Thread(target=self._wait_and_generate)
        self._timer_event_thread.start()

    def _wait_and_generate(self) -> None:
        if self._last_event_time is not None:
            time_since_last_event = monotonic() - self._last_event_time
            time_until_next_event = (1.0 / self._rate_hz) - time_since_last_event
            if time_until_next_event > 0:
                sleep(time_until_next_event)
            elif mod(self._event_counter, 10) == 0:
                logger.warning(
                    f"Mock frame rate is {1 / time_since_last_event:.3f} Hz, "
                    f"which is lower than the requested {self._rate_hz} Hz."
                )
        self._last_event_time = monotonic()
        self._timer_event.set()
        self._event_counter += 1

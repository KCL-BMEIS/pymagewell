import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from mwcapture.libmwcapture import fourcc_calc_min_stride, MWFOURCC_NV12, fourcc_calc_image_size, \
    MWFOURCC_BGR24, mwcap_smpte_timecode


@dataclass
class ImageCoordinateInPixels:
    row: int
    col: int


@dataclass
class ImageSizeInPixels:
    cols: int
    rows: int


@dataclass
class AspectRatio:
    hor: int
    ver: int


class TransferMode(Enum):
    TIMER = 0
    """ Transferred are triggered by a timer event from the driver"""
    NORMAL = 1
    """ Transfers are triggered by a notification received from the device when a frame has been grabbed"""
    LOW_LATENCY = 2
    """ Transfers are triggered by a notification received from the device when a chunk of a frame has been grabbed"""


@dataclass
class FrameTimeCode:
    hour: int
    minute: int
    second: int
    frame: int

    @classmethod
    def from_mwcap_smpte_timecode(cls, tc: mwcap_smpte_timecode) -> 'FrameTimeCode':
        return FrameTimeCode(
            hour=int(tc[0]),
            minute=int(tc[1]),
            second=int(tc[2]),
            frame=int(tc[3])
        )

    @classmethod
    def now(cls, frame_period_s: float) -> 'FrameTimeCode':
        microseconds_per_frame = frame_period_s * 1e6
        now = datetime.now()
        return FrameTimeCode(
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            frame=int(round(now.microsecond / microseconds_per_frame))
        )

    def as_datetime(self, frame_period_s: float) -> datetime:
        microseconds_per_frame = frame_period_s * 1e6
        now = datetime.now()
        return datetime(year=now.year, month=now.month, day=now.day, hour=self.hour, minute=self.minute,
                        second=self.second, microsecond=int(self.frame * microseconds_per_frame))


@dataclass
class ProCaptureSettings:
    dimensions: ImageSizeInPixels = ImageSizeInPixels(1920, 1080)
    color_format: int = MWFOURCC_BGR24  # Color format of captured video frames.
    transfer_mode: TransferMode = TransferMode.NORMAL
    num_lines_per_chunk: int = 64

    def __post_init__(self) -> None:
        check_valid_chunk_size(self.num_lines_per_chunk)

    @property
    def min_stride(self) -> int:
        return fourcc_calc_min_stride(self.color_format, self.dimensions.cols, 2)

    @property
    def image_size_in_bytes(self) -> int:
        if self.color_format == MWFOURCC_NV12:
            return self.dimensions.cols * self.dimensions.rows * 2  # copied from line 223 of capture.py
        else:
            return fourcc_calc_image_size(self.color_format, self.dimensions.cols, self.dimensions.rows, self.min_stride)


def check_valid_chunk_size(n_lines_per_chunk: int) -> None:
    if n_lines_per_chunk < 64:
        raise ValueError('Minimum number of lines per chunk is 64.')
    elif round(math.log2(n_lines_per_chunk)) != math.log2(n_lines_per_chunk):
        raise ValueError('Number of lines per chunk must be a power of 2.')

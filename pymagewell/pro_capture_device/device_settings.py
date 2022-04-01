import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import cast

from mwcapture.libmwcapture import (
    fourcc_calc_min_stride,
    MWFOURCC_NV12,
    fourcc_calc_image_size,
    MWFOURCC_BGR24,
    mwcap_smpte_timecode,
    MWFOURCC_UNK,
    MWFOURCC_GREY,
    MWFOURCC_Y800,
    MWFOURCC_BGRA,
    MWFOURCC_Y8,
    MWFOURCC_Y16,
    MWFOURCC_RGB15,
    MWFOURCC_RGB16,
    MWFOURCC_RGB24,
    MWFOURCC_RGBA,
    MWFOURCC_ARGB,
    MWFOURCC_BGR15,
    MWFOURCC_BGR16,
    MWFOURCC_ABGR,
    MWFOURCC_NV16,
    MWFOURCC_NV61,
    MWFOURCC_I422,
    MWFOURCC_YV16,
    MWFOURCC_YUY2,
    MWFOURCC_YUYV,
    MWFOURCC_UYVY,
    MWFOURCC_BGR10,
    MWFOURCC_RGB10,
    MWFOURCC_V410,
    MWFOURCC_Y410,
    MWFOURCC_V210,
    MWFOURCC_V408,
    MWFOURCC_UYVA,
    MWFOURCC_AYUV,
    MWFOURCC_V308,
    MWFOURCC_IYU2,
    MWFOURCC_P210,
    MWFOURCC_P010,
    MWFOURCC_NV21,
    MWFOURCC_YV12,
    MWFOURCC_IYUV,
    MWFOURCC_I420,
    MWFOURCC_VYUY,
    MWFOURCC_YVYU,
    MWFOURCC_VYUA,
)

DEVICE_CLOCK_TICK_PERIOD_IN_SECONDS = 1e-7


class ColourFormat(Enum):
    """ Enumeration of the supported colour formats. """
    UNK = MWFOURCC_UNK
    GREY = MWFOURCC_GREY
    Y800 = MWFOURCC_Y800
    Y8 = MWFOURCC_Y8
    Y16 = MWFOURCC_Y16
    RGB15 = MWFOURCC_RGB15
    RGB16 = MWFOURCC_RGB16
    RGB24 = MWFOURCC_RGB24
    RGBA = MWFOURCC_RGBA
    ARGB = MWFOURCC_ARGB
    BGR15 = MWFOURCC_BGR15
    BGR16 = MWFOURCC_BGR16
    BGR24 = MWFOURCC_BGR24
    BGRA = MWFOURCC_BGRA
    ABGR = MWFOURCC_ABGR
    MNV16 = MWFOURCC_NV16
    NV61 = MWFOURCC_NV61
    I422 = MWFOURCC_I422
    YV16 = MWFOURCC_YV16
    YUY2 = MWFOURCC_YUY2
    YUYV = MWFOURCC_YUYV
    UYVY = MWFOURCC_UYVY
    YVYU = MWFOURCC_YVYU
    VYUY = MWFOURCC_VYUY
    I420 = MWFOURCC_I420
    IYUV = MWFOURCC_IYUV
    NV12 = MWFOURCC_NV12
    YV12 = MWFOURCC_YV12
    NV21 = MWFOURCC_NV21
    P010 = MWFOURCC_P010
    P210 = MWFOURCC_P210
    IYU2 = MWFOURCC_IYU2
    V308 = MWFOURCC_V308
    AYUV = MWFOURCC_AYUV
    UYVA = MWFOURCC_UYVA
    V408 = MWFOURCC_V408
    VYUA = MWFOURCC_VYUA
    V210 = MWFOURCC_V210
    Y410 = MWFOURCC_Y410
    V410 = MWFOURCC_V410
    RGB10 = MWFOURCC_RGB10
    BGR10 = MWFOURCC_BGR10


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
    """ Enumeration of the supported methods for triggering the transfer of frames to the PC. """
    TIMER = 0
    """ Transferred are triggered by a software timer event, allowing arbitrary frame rates. This is the only mode
        supported by MockProCaptureDevice. """
    NORMAL = 1
    """ Transfers are triggered by a notification received from the device when a whole frame has been received, and
    therefore grabbing happens at the source frame rate."""
    LOW_LATENCY = 2
    """ Transfers are triggered by a notification received from the device when the first chunk of a frame has been
    received. Grabbing happens at the source frame rate, but with a lower latency."""


@dataclass
class FrameTimeCode:
    hour: int
    minute: int
    second: int
    frame: int

    @classmethod
    def from_mwcap_smpte_timecode(cls, tc: mwcap_smpte_timecode) -> "FrameTimeCode":
        return FrameTimeCode(
            hour=int(tc[0]),  # type: ignore
            minute=int(tc[1]),  # type: ignore
            second=int(tc[2]),  # type: ignore
            frame=int(tc[3]),  # type: ignore
        )

    @classmethod
    def now(cls, frame_period_s: float) -> "FrameTimeCode":
        microseconds_per_frame = frame_period_s * 1e6
        now = datetime.now()
        return FrameTimeCode(
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            frame=int(round(now.microsecond / microseconds_per_frame)),
        )

    def as_datetime(self, frame_period_s: float) -> datetime:
        microseconds_per_frame = frame_period_s * 1e6
        now = datetime.now()
        return datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=int(self.frame * microseconds_per_frame),
        )


@dataclass
class ProCaptureSettings:
    """ Settings for the ProCapture device. """
    dimensions: ImageSizeInPixels = ImageSizeInPixels(1920, 1080)
    """The dimensions of the frames to be acquired in pixels."""
    color_format: ColourFormat = ColourFormat.BGR24
    """The colour format of the frames to be acquired."""
    transfer_mode: TransferMode = TransferMode.NORMAL
    """The method to use for transferring frames from the device to the PC. See `TransferMode` for details."""
    num_lines_per_chunk: int = 64
    """The number of lines of a frame to transfer at a time (for `TransferMode.LOW_LATENCY` transfers)."""

    def __post_init__(self) -> None:
        _check_valid_chunk_size(self.num_lines_per_chunk)

    @property
    def min_stride(self) -> int:
        return cast(int, fourcc_calc_min_stride(self.color_format.value, self.dimensions.cols, 2))  # type: ignore

    @property
    def image_size_in_bytes(self) -> int:
        if self.color_format == ColourFormat.NV12:
            return self.dimensions.cols * self.dimensions.rows * 2  # copied from line 223 of capture.py
        else:
            return cast(
                int,
                fourcc_calc_image_size(  # type: ignore
                    self.color_format,
                    self.dimensions.cols,
                    self.dimensions.rows,
                    self.min_stride,
                ),
            )


def _check_valid_chunk_size(n_lines_per_chunk: int) -> None:
    if n_lines_per_chunk < 64:
        raise ValueError("Minimum number of lines per chunk is 64.")
    elif round(math.log2(n_lines_per_chunk)) != math.log2(n_lines_per_chunk):
        raise ValueError("Number of lines per chunk must be a power of 2.")

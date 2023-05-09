import math
import struct
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import cast

from numpy import floor, uint16, uint8

from mwcapture.libmwcapture import (
    fourcc_calc_min_stride,
    MWFOURCC_NV12,
    fourcc_calc_image_size,
    MWFOURCC_BGR24,
    fourcc_get_bpp,
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
    """Enumeration of the supported colour formats."""

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
    NV16 = MWFOURCC_NV16
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

    @property
    def fourcc_string(self) -> str:
        return struct.pack("<I", self.value).decode("utf-8")

    @property
    def bits_per_pixel(self) -> int:
        return cast(int, fourcc_get_bpp(self.value))  # type: ignore

    @property
    def num_channels(self) -> int:
        if self in [ColourFormat.Y8, ColourFormat.Y16, ColourFormat.Y800, ColourFormat.GREY]:
            return 1
        elif "A" in self.fourcc_string:
            return 4
        else:
            return 3

    @property
    def is_rgb_type(self) -> bool:
        return {"R", "G", "B"}.issubset(set(list(self.name)))

    def as_ffmpeg_pixel_format(self) -> str:
        return ffmpeg_pixel_formats[self]

    @property
    def pixel_dtype(self) -> type:
        bits_per_sample_per_channel = int(floor(self.bits_per_pixel / self.num_channels))
        if bits_per_sample_per_channel <= 8:
            return uint8
        elif bits_per_sample_per_channel <= 16:
            return uint16
        else:
            raise ValueError("ColourFormat has unrecognised structure.")


ffmpeg_pixel_formats = {
    ColourFormat.UNK: "0",
    ColourFormat.GREY: "gray",  # no conversion required
    ColourFormat.Y800: "gray8",  # no conversion required
    ColourFormat.Y8: "gray8",  # no conversion required
    ColourFormat.Y16: "gray16le",  # no conversion required
    ColourFormat.RGB15: "rgb555le",  # done manually
    ColourFormat.RGB16: "rgb565le",  # done manually
    ColourFormat.RGB24: "rgb24",  # no conversion required
    ColourFormat.RGBA: "rgba",
    ColourFormat.ARGB: "argb",
    ColourFormat.BGR15: "bgr555le",  # done manually
    ColourFormat.BGR16: "bgr565le",  # done manually
    ColourFormat.BGR24: "bgr24",  # no conversion required
    ColourFormat.BGRA: "bgra",
    ColourFormat.ABGR: "abgr",
    ColourFormat.NV16: "nv16",
    ColourFormat.NV61: "nv61",
    ColourFormat.I422: "yuv422p",  # broken
    ColourFormat.YV16: "yuv422p",  # broken
    ColourFormat.YUY2: "yuyv422",  # needs conversion
    ColourFormat.YUYV: "yuyv422",  # needs conversion
    ColourFormat.UYVY: "uyvy422",  # needs conversion
    ColourFormat.YVYU: "yvyu422",  # needs conversion
    ColourFormat.VYUY: "vyuy422",  # broken
    ColourFormat.I420: "yuv420p",  # broken
    ColourFormat.IYUV: "yuv420p",  # broken
    ColourFormat.NV12: "nv12",  # broken
    ColourFormat.YV12: "yuv420p",  # broken
    ColourFormat.NV21: "nv21",  # broken
    ColourFormat.P010: "p010le",  # broken
    ColourFormat.P210: "p210le",  # broken
    ColourFormat.IYU2: "yuva422p",  # needs conversion
    ColourFormat.V308: "rgb48le",  # broken
    ColourFormat.AYUV: "yuva444p",  # needs conversion
    ColourFormat.UYVA: "yuva444p",  # needs conversion
    ColourFormat.V408: "yuva444p16le",  # broken
    ColourFormat.VYUA: "yuva444p16le",  # broken
    ColourFormat.V210: "v210",  # broken
    ColourFormat.Y410: "yuva444p10le",  # broken
    ColourFormat.V410: "yuva444p10le",  # broken
    ColourFormat.RGB10: "x2rgb10le",  # needs conversion
    ColourFormat.BGR10: "x2bgr10le",  # needs conversion
}


@dataclass
class ImageCoordinateInPixels:
    row: int
    col: int


@dataclass(frozen=True)
class ImageSizeInPixels:
    cols: int
    rows: int


@dataclass(frozen=True)
class AspectRatio:
    hor: int
    ver: int


class TransferMode(Enum):
    """Enumeration of the supported methods for triggering the transfer of frames to the PC."""

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
    """Settings for the ProCapture device."""

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

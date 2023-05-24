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


class ColourSpace(Enum):
    GREY = 0
    RGB = 1
    YUV = 2
    UNKNOWN = 3


class RGBChannelOrder(Enum):
    RGB = 0
    BGR = 1


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
    def has_alpha_channel(self) -> bool:
        return "A" in self.fourcc_string

    @property
    def num_channels(self) -> int:
        if self in [ColourFormat.Y8, ColourFormat.Y16, ColourFormat.Y800, ColourFormat.GREY]:
            return 1
        elif self.has_alpha_channel:
            return 4
        else:
            return 3

    @property
    def colour_space(self) -> ColourSpace:
        if self == ColourFormat.UNK:
            return ColourSpace.UNKNOWN
        elif self in [ColourFormat.GREY, ColourFormat.Y800, ColourFormat.Y8, ColourFormat.Y16]:
            return ColourSpace.GREY
        elif self in [
            ColourFormat.RGB24,
            ColourFormat.RGB10,
            ColourFormat.RGB15,
            ColourFormat.RGB16,
            ColourFormat.ARGB,
            ColourFormat.RGBA,
            ColourFormat.BGR24,
            ColourFormat.BGR10,
            ColourFormat.BGR15,
            ColourFormat.BGR16,
            ColourFormat.ABGR,
            ColourFormat.BGRA,
        ]:
            return ColourSpace.RGB
        else:
            return ColourSpace.YUV

    def channel_order(self) -> RGBChannelOrder:
        if self.colour_space != ColourSpace.RGB:
            raise NotImplementedError("Channel order property only implemented for RGB colour formats")
        if self in [
            ColourFormat.RGB24,
            ColourFormat.ARGB,
            ColourFormat.RGBA,
            ColourFormat.RGB15,
            ColourFormat.RGB16,
            ColourFormat.RGB10,
        ]:
            return RGBChannelOrder.RGB
        elif self in [
            ColourFormat.BGR24,
            ColourFormat.ABGR,
            ColourFormat.BGRA,
            ColourFormat.BGR15,
            ColourFormat.BGR16,
            ColourFormat.BGR10,
        ]:
            return RGBChannelOrder.BGR
        else:
            raise NotImplementedError(f"Channel order property not implemented for colour format {self}.")

    @property
    def alpha_channel_index(self) -> int:
        if not self.has_alpha_channel:
            raise ValueError(f"Colour format {self} does not have an alpha channel")
        alpha_index = self.fourcc_string.find("A")
        if alpha_index == -1:
            raise ValueError(f"Could not find index of alpha channel for colour format {self}")
        return alpha_index

    def as_ffmpeg_pixel_format(self) -> str:
        if self == ColourFormat.UNK:
            raise ValueError("Colour format not known")
        return ffmpeg_pixel_formats[self]

    @property
    def pixel_dtype(self) -> type:
        if self == ColourFormat.UNK:
            raise ValueError("Colour format not known")
        bits_per_sample_per_channel = int(floor(self.bits_per_pixel / self.num_channels))
        if bits_per_sample_per_channel <= 8:
            return uint8
        elif bits_per_sample_per_channel <= 16:
            return uint16
        else:
            raise ValueError("ColourFormat has unrecognised structure.")


ffmpeg_pixel_formats = {
    ColourFormat.UNK: "0",
    ColourFormat.GREY: "gray",
    ColourFormat.Y800: "gray",
    ColourFormat.Y8: "gray",
    ColourFormat.Y16: "gray16le",
    ColourFormat.RGB15: "rgb555le",
    ColourFormat.RGB16: "rgb565le",
    ColourFormat.RGB24: "rgb24",
    ColourFormat.RGBA: "rgba",
    ColourFormat.ARGB: "argb",
    ColourFormat.BGR15: "bgr555le",
    ColourFormat.BGR16: "bgr565le",
    ColourFormat.BGR24: "bgr24",
    ColourFormat.BGRA: "bgra",
    ColourFormat.ABGR: "abgr",
    ColourFormat.NV16: "nv16",
    ColourFormat.NV61: "nv61",
    ColourFormat.I422: "yuv422p",
    ColourFormat.YV16: "yuv422p",
    ColourFormat.YUY2: "yuyv422",
    ColourFormat.YUYV: "yuyv422",
    ColourFormat.UYVY: "uyvy422",
    ColourFormat.YVYU: "yvyu422",
    ColourFormat.VYUY: "vyuy422",
    ColourFormat.I420: "yuv420p",
    ColourFormat.IYUV: "yuv420p",
    ColourFormat.NV12: "nv12",
    ColourFormat.YV12: "yuv420p",
    ColourFormat.NV21: "nv21",
    ColourFormat.P010: "p010le",
    ColourFormat.P210: "p210le",
    ColourFormat.IYU2: "yuva422p",
    ColourFormat.V308: "rgb48le",
    ColourFormat.AYUV: "yuva444p",
    ColourFormat.UYVA: "yuva444p",
    ColourFormat.V408: "yuva444p16le",
    ColourFormat.VYUA: "yuva444p16le",
    ColourFormat.V210: "v210",
    ColourFormat.Y410: "yuva444p10le",
    ColourFormat.V410: "yuva444p10le",
    ColourFormat.RGB10: "x2rgb10le",
    ColourFormat.BGR10: "x2bgr10le",
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

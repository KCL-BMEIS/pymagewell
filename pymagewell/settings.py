from dataclasses import dataclass
from enum import Enum

from mwcapture.libmwcapture import fourcc_calc_min_stride, MWFOURCC_NV12, fourcc_calc_image_size, \
    MWFOURCC_BGR24


@dataclass
class Dimensions:
    x: int
    y: int


class TransferMode(Enum):
    TIMER = 0
    """ Transferred are triggered by a timer event from the driver"""
    NORMAL = 1
    """ Transfers are triggered by a notification received from the device when a frame has been grabbed"""
    LOW_LATENCY = 2
    """ Transfers are triggered by a notification received from the device when a partial frame has been grabber"""


@dataclass
class VideoSettings:
    dimensions: Dimensions = Dimensions(1920, 1080)
    color_format: int = MWFOURCC_BGR24  # Color format of captured video frames.

    @property
    def min_stride(self) -> int:
        return fourcc_calc_min_stride(self.color_format, self.dimensions.x, 2)

    @property
    def image_size(self) -> int:
        if self.color_format == MWFOURCC_NV12:
            return self.dimensions.x * self.dimensions.y * 2  # copied from line 223 of capture.py
        else:
            return fourcc_calc_image_size(self.color_format, self.dimensions.x, self.dimensions.y, self.min_stride)

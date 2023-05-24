from dataclasses import dataclass
from datetime import datetime
from typing import Union

from numpy import uint16, uint8
from numpy.typing import NDArray

from pymagewell.pro_capture_device.device_settings import (
    ColourFormat,
    ImageSizeInPixels,
)


@dataclass
class VideoFrameTimestamps:
    buffering_started: datetime
    buffering_complete: datetime
    transfer_started: datetime
    transfer_complete: datetime


@dataclass
class VideoFrame:
    string_buffer: bytes
    dimensions: ImageSizeInPixels
    timestamps: VideoFrameTimestamps
    format: ColourFormat

    def as_array(self) -> NDArray[Union[uint8, uint16]]:
        pass

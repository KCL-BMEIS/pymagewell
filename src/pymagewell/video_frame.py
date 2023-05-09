from dataclasses import dataclass
from datetime import datetime
from typing import Union

from cv2 import imdecode
from numpy import floor, uint16, uint8, frombuffer
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
        # Create array with correct dtype
        arr: NDArray[Union[uint8, uint16]] = frombuffer(
            self.string_buffer, dtype=_choose_numpy_dtype_from_colour_format(self.format)
        )
        # Fill it with the frame using correct fourcc code
        frame: NDArray[Union[uint8, uint16]] = imdecode(arr, self.format.value)
        return frame


def _choose_numpy_dtype_from_colour_format(colour_format: ColourFormat) -> type:
    bits_per_sample_per_channel = int(floor(colour_format.bits_per_pixel / colour_format.num_channels))
    if bits_per_sample_per_channel <= 8:
        return uint8
    elif bits_per_sample_per_channel <= 16:
        return uint16
    else:
        raise ValueError("ColourFormat has unrecognised structure.")

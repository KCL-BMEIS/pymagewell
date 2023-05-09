from dataclasses import dataclass
from datetime import datetime
from typing import Union

from numpy import uint16, uint8
from numpy.typing import NDArray

from pymagewell.conversion import bytes_to_grey_array, bytes_to_rgb_array, bytes_to_yuv_array, check_if_ffmpeg_available
from pymagewell.exceptions import FFMPEGNotAvailable
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
        if self.format.is_rgb_type:
            return self.as_rgb_array()
        elif self.format.num_channels == 1:
            return self.as_grey_array()
        else:
            return self.as_yuv_array()

    def as_grey_array(self) -> NDArray[Union[uint8, uint16]]:
        try:
            return bytes_to_grey_array(self.string_buffer, self.dimensions, self.format)
        except FFMPEGNotAvailable:
            raise FFMPEGNotAvailable(
                f"Cannot convert from {self.format.name} to GREY numpy array without "
                f"ffmpeg installed. You can access the bytes yourself (VideoFrame.string_buffer "
                f"or use ColourFormat.RGB24."
            )

    def as_rgb_array(self) -> NDArray[Union[uint8, uint16]]:
        try:
            return bytes_to_rgb_array(self.string_buffer, self.dimensions, self.format)
        except FFMPEGNotAvailable:
            raise FFMPEGNotAvailable(
                f"Cannot convert from {self.format.name} to RGB numpy array without "
                f"ffmpeg installed. You can access the bytes yourself (VideoFrame.string_buffer "
                f"or use ColourFormat.RGB24."
            )

    def as_yuv_array(self) -> NDArray[Union[uint8, uint16]]:
        check_if_ffmpeg_available(
            "Cannot convert YUV ColourFormats without ffmpeg installed. You can access the bytes"
            " yourself (VideoFrame.string_buffer or use ColourFormat.RGB24."
        )
        return bytes_to_yuv_array(self.string_buffer, self.dimensions, self.format)

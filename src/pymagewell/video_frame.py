from dataclasses import dataclass
from datetime import datetime

from numpy import uint8, frombuffer
from numpy.typing import NDArray

from pymagewell.pro_capture_device.device_settings import (
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

    def as_array(self) -> NDArray[uint8]:
        # frame = cast(NDArray[uint8], imdecode(frombuffer(self.string_buffer, dtype=uint8), IMREAD_COLOR))
        # frame = resize(frame, (self.dimensions.rows, self.dimensions.cols))
        # return frame
        numpy_image = frombuffer(self.string_buffer, dtype=uint8, count=self.dimensions.cols * self.dimensions.rows * 3)
        numpy_image.resize((self.dimensions.rows, self.dimensions.cols, 3))
        return numpy_image

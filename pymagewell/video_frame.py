from dataclasses import dataclass
from datetime import datetime
from typing import cast

from cv2 import imdecode, IMREAD_COLOR
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
        return cast(NDArray[uint8], imdecode(frombuffer(self.string_buffer, uint8), IMREAD_COLOR))

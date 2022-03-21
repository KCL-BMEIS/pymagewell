from dataclasses import dataclass

from PIL import Image
from numpy import array, uint8
from numpy.typing import NDArray

from pymagewell.pro_capture_device.device_settings import ImageSizeInPixels, FrameTimeCode


@dataclass
class VideoFrame:
    string_buffer: bytes
    dimensions: ImageSizeInPixels
    timestamp: FrameTimeCode

    def as_pillow_image(self) -> Image.Image:
        return Image.frombuffer(mode="RGB",  # it's actually BGR but pillow doesn't support this
                                size=(self.dimensions.cols, self.dimensions.rows),
                                data=self.string_buffer)

    def as_array(self) -> NDArray[uint8]:
        return array(self.as_pillow_image())

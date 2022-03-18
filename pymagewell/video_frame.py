from dataclasses import dataclass

from PIL import Image
from numpy import array, uint8
from numpy.typing import NDArray

from pymagewell.settings import Dimensions


@dataclass
class VideoFrame:
    string_buffer: bytes
    dimensions: Dimensions
    timestamp: int

    def as_pillow_image(self) -> Image.Image:
        return Image.frombuffer(mode="RGB",  # it's actually BGR but pillow doesn't support this
                                size=(self.dimensions.x, self.dimensions.y),
                                data=self.string_buffer)

    def as_array(self) -> NDArray[uint8]:
        return array(self.as_pillow_image())

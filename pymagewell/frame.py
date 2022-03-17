from dataclasses import dataclass

from PIL import Image

from pymagewell.settings import Dimensions


@dataclass
class Frame:
    string_buffer: bytes
    dimensions: Dimensions
    timestamp: int

    def as_image(self) -> Image.Image:
        return Image.frombuffer(mode="RGB",
                                size=(self.dimensions.x, self.dimensions.y),
                                data=self.string_buffer)

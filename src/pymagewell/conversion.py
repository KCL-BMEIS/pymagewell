import logging
import subprocess
from enum import Enum
from typing import Tuple, Union

from numpy import delete, frombuffer, insert, stack, uint16, uint32, uint8
from numpy.typing import NDArray

from pymagewell.pro_capture_device.device_settings import ColourFormat, ColourSpace, ImageSizeInPixels, RGBChannelOrder
from pymagewell.exceptions import FFMPEGNotAvailable


logger = logging.getLogger(__name__)


class FFMPEG:
    def __init__(self, failure_message: str = "") -> None:
        try:
            self._executable = "ffmpeg"
            check_if_ffmpeg_available(self._executable, failure_message)
        except FFMPEGNotAvailable:
            self._executable = "C:/ffmpeg/bin/ffmpeg"
            check_if_ffmpeg_available(self._executable, failure_message)

    def execute_ffmpeg_command(self, cmd: str, input_bytes: bytes) -> bytes:
        cmd = self._executable + " " + cmd
        proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(input=input_bytes)
        if proc.returncode != 0:
            raise Exception(f"ffmpeg command failed with return code {proc.returncode}: {stderr.decode('utf-8')}")
        return stdout

    def transcode_image_bytes(
        self, image_bytes: bytes, image_size: ImageSizeInPixels, current_format: str, desired_format: str
    ) -> bytes:
        if current_format == desired_format:
            return image_bytes
        dimensions_str = f"{image_size.cols}x{image_size.rows}"
        cmd = (
            f"-y -f rawvideo -s {dimensions_str} -pix_fmt {current_format} -i - "
            f"-an -vcodec rawvideo -f rawvideo -pix_fmt {desired_format} -"
        )
        return self.execute_ffmpeg_command(cmd, image_bytes)

    def encode_rgb24_array(self, image: NDArray[uint8], to_format: ColourFormat) -> bytes:
        """Use ffmpeg to convert an RGB24 numpy array to bytes representing a different pixel format. For use generating
        mock frames in mock mode."""
        image_bytes = image.tobytes()
        dimensions = ImageSizeInPixels(rows=image.shape[0], cols=image.shape[1])
        if to_format in [ColourFormat.UNK, ColourFormat.NV16, ColourFormat.NV61, ColourFormat.VYUY, ColourFormat.V210]:
            raise NotImplementedError(f"Encoding to {to_format} bytes has not been implemented.")
        desired_format = to_format.as_ffmpeg_pixel_format()
        return self.transcode_image_bytes(image_bytes, dimensions, "rgb24", desired_format)


def check_if_ffmpeg_available(executable: str, message: str = "") -> None:
    try:
        subprocess.run([executable, "-version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise FFMPEGNotAvailable(message)


class AlphaChannelLocation(Enum):
    LAST = -1
    FIRST = 0
    IGNORE = 2


def convert_grey_bytes_to_array(
    image_bytes: bytes, image_size: ImageSizeInPixels, colour_format: ColourFormat
) -> NDArray[Union[uint8, uint16]]:
    if colour_format.colour_space != ColourSpace.GREY:
        raise NotImplementedError(f"Conversion of {colour_format} frames to grey numpy arrays not implemented.")
    return convert_unpacked_bytes_to_array(
        image_bytes, image_size, colour_format.num_channels, colour_format.pixel_dtype
    )


def convert_rgb_bytes_to_array(
    image_bytes: bytes,
    image_size: ImageSizeInPixels,
    colour_format: ColourFormat,
    output_channel_order: RGBChannelOrder,
    output_alpha_location: AlphaChannelLocation,
) -> NDArray[Union[uint8, uint16]]:

    if colour_format in [
        ColourFormat.BGRA,
        ColourFormat.ABGR,
        ColourFormat.RGBA,
        ColourFormat.ARGB,
        ColourFormat.RGB24,
        ColourFormat.BGR24,
    ]:
        image_array: NDArray[Union[uint8, uint16]] = convert_unpacked_bytes_to_array(
            image_bytes, image_size, colour_format.num_channels, colour_format.pixel_dtype
        )
    elif colour_format in [ColourFormat.RGB15, ColourFormat.BGR15]:
        image_array = convert_rgb15_rgb16_to_array(image_bytes, image_size, bits_per_channel=(5, 5, 5))
    elif colour_format in [ColourFormat.RGB16, ColourFormat.BGR16]:
        image_array = convert_rgb15_rgb16_to_array(image_bytes, image_size, bits_per_channel=(5, 6, 5))
    elif colour_format in [ColourFormat.RGB10, ColourFormat.BGR10]:
        image_array = convert_rgb10_to_array(image_bytes, image_size)
    else:
        raise NotImplementedError(f"Conversion of {colour_format} frames to RGB NumPy arrays not implemented")

    if colour_format.has_alpha_channel:
        alpha_channel: NDArray[Union[uint8, uint16]] = image_array[:, :, colour_format.alpha_channel_index]
        colour_channels: NDArray[Union[uint8, uint16]] = delete(image_array, colour_format.alpha_channel_index, axis=2)
    else:
        colour_channels = image_array

    if colour_format.channel_order() != output_channel_order:
        colour_channels = colour_channels[:, :, ::-1]

    if colour_format.has_alpha_channel and output_alpha_location != AlphaChannelLocation.IGNORE:
        constructed_image_array = insert(colour_channels, output_alpha_location.value, alpha_channel, axis=2)
    else:
        constructed_image_array = colour_channels
    return constructed_image_array


def convert_unpacked_bytes_to_array(
    image_bytes: bytes, image_size: ImageSizeInPixels, num_channels: int, dtype: type
) -> NDArray[Union[uint8, uint16]]:
    if dtype not in [uint8, uint16]:
        raise ValueError(f"dtype must be uint8 or uint16, not {dtype}")
    numpy_image: NDArray[Union[uint8, uint16]] = frombuffer(
        image_bytes, dtype=dtype, count=image_size.cols * image_size.rows * num_channels
    )
    numpy_image.resize((image_size.rows, image_size.cols, num_channels))
    return numpy_image


def convert_rgb15_rgb16_to_array(
    image_bytes: bytes, image_size: ImageSizeInPixels, bits_per_channel: Tuple[int, int, int]
) -> NDArray[uint8]:
    # Convert the bytes to a numpy array of uint16
    image: NDArray[uint16] = frombuffer(image_bytes, dtype=uint16)

    # Reshape the array to match the image dimensions
    image = image.reshape((image_size.rows, image_size.cols))

    # Extract the red, green, and blue channels
    red_bits, green_bits, blue_bits = bits_per_channel
    red_shift = green_bits + blue_bits
    green_shift = blue_bits
    red = (image & (((1 << red_bits) - 1) << red_shift)) >> red_shift
    green = (image & (((1 << green_bits) - 1) << green_shift)) >> green_shift
    blue = image & ((1 << blue_bits) - 1)

    # Scale up the channels from the specified bits per channel to 8 bits
    red = (red << (8 - red_bits)) | (red >> (2 * red_bits - 8))
    green = (green << (8 - green_bits)) | (green >> (2 * green_bits - 8))
    blue = (blue << (8 - blue_bits)) | (blue >> (2 * blue_bits - 8))

    # Reshape the channels to match the image dimensions
    red = red.reshape((image_size.rows, image_size.cols))
    green = green.reshape((image_size.rows, image_size.cols))
    blue = blue.reshape((image_size.rows, image_size.cols))

    # Stack the channels to form the final RGB image
    rgb_image = stack((red, green, blue), axis=-1)
    rgb_image_uint8: NDArray[uint8] = rgb_image.astype(uint8)
    return rgb_image_uint8


def convert_rgb10_to_array(image_bytes: bytes, image_size: ImageSizeInPixels) -> NDArray[uint16]:
    # Calculate the number of pixels
    num_pixels = image_size.rows * image_size.cols

    # Calculate the number of bytes required for RGB10 data
    num_bytes = num_pixels * 4  # Each pixel requires 4 bytes (10 bits for each channel + 2 padding bits)

    # Convert the bytes to a numpy array of uint32
    image: NDArray[uint32] = frombuffer(image_bytes[:num_bytes], dtype=uint32)

    # Reshape the array to match the image dimensions
    image = image.reshape((image_size.rows, image_size.cols))

    # Extract the red, green, and blue channels
    red = (image >> 20) & 0x3FF
    green = (image >> 10) & 0x3FF
    blue = image & 0x3FF

    # Scale up the channels from 10 bits to 16 bits
    red = (red << 6) | (red >> 4)
    green = (green << 6) | (green >> 4)
    blue = (blue << 6) | (blue >> 4)

    # Reshape the channels to match the image dimensions
    red = red.reshape((image_size.rows, image_size.cols))
    green = green.reshape((image_size.rows, image_size.cols))
    blue = blue.reshape((image_size.rows, image_size.cols))

    # Stack the channels to form the final RGB image
    rgb_image = stack((red, green, blue), axis=-1)
    rgb_image_uint16: NDArray[uint16] = rgb_image.astype(uint16)

    return rgb_image_uint16

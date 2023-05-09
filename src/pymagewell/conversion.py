import logging
import subprocess
from typing import Tuple, Union

import numba
import numpy as np
from cv2 import COLOR_YUV2BGR_I420, COLOR_YUV2BGR_IYUV, COLOR_YUV2BGR_NV12, COLOR_YUV2RGB_UYVY, cvtColor
from numpy import uint16, uint8
from numpy.typing import NDArray

from pymagewell.pro_capture_device.device_settings import ColourFormat, ImageSizeInPixels
from pymagewell.exceptions import FFMPEGNotAvailable


logger = logging.getLogger(__name__)


def check_if_ffmpeg_available(message: str = "") -> None:
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise FFMPEGNotAvailable(message)


def execute_ffmpeg_command(cmd: str, input_bytes: bytes) -> bytes:
    check_if_ffmpeg_available()
    proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=input_bytes)
    if proc.returncode != 0:
        raise Exception(f"ffmpeg command failed with return code {proc.returncode}: {stderr.decode('utf-8')}")
    return stdout


def transcode_image_bytes(
    image_bytes: bytes, image_size: ImageSizeInPixels, current_format: str, desired_format: str
) -> bytes:
    if current_format == desired_format:
        return image_bytes
    dimensions_str = f"{image_size.cols}x{image_size.rows}"
    cmd = (
        f"ffmpeg -y -f rawvideo -s {dimensions_str} -pix_fmt {current_format} -i - "
        f"-an -vcodec rawvideo -f rawvideo -pix_fmt {desired_format} -"
    )
    return execute_ffmpeg_command(cmd, image_bytes)


def bytes_to_yuv_array(
    image_bytes: bytes, image_size: ImageSizeInPixels, current_format: ColourFormat
) -> NDArray[Union[uint8, uint16]]:

    if current_format.pixel_dtype == uint8:
        bytes_per_pixel_per_channel = 1
    elif current_format.pixel_dtype == uint16:
        bytes_per_pixel_per_channel = 2
    else:
        raise ValueError(
            f"Conversion to numpy for format {current_format} with dtype {current_format.pixel_dtype}" "not supported"
        )

    if current_format not in [ColourFormat.UYVY]:
        if current_format.is_rgb_type:
            logger.warning("Converting an RGB pixel format to YUV - this is slow!")
        if current_format.pixel_dtype == uint8:
            output_format = "yuv444p"
        elif current_format.pixel_dtype == uint16:
            output_format = "yuv444p16le"
        else:
            raise ValueError(
                f"Conversion to numpy for format {current_format} with dtype {current_format.pixel_dtype}" "not supported"
            )

        image_bytes = transcode_image_bytes(image_bytes, image_size, current_format.as_ffmpeg_pixel_format(), output_format)
    plane_length_in_bytes = image_size.rows * image_size.cols * bytes_per_pixel_per_channel

    # Extract the Y, U, and V planes
    y_plane = image_bytes[: plane_length_in_bytes]
    u_plane = image_bytes[plane_length_in_bytes: plane_length_in_bytes * 2]
    v_plane = image_bytes[plane_length_in_bytes * 2 : plane_length_in_bytes * 3]

    # Reshape each plane into a 2D array of the appropriate size
    y_array: NDArray[Union[uint8, uint16]] = np.frombuffer(y_plane, dtype=current_format.pixel_dtype).reshape(
        (image_size.rows, image_size.cols)
    )
    u_array: NDArray[Union[uint8, uint16]] = np.frombuffer(u_plane, dtype=current_format.pixel_dtype).reshape(
        (image_size.rows, image_size.cols)
    )
    v_array: NDArray[Union[uint8, uint16]] = np.frombuffer(v_plane, dtype=current_format.pixel_dtype).reshape(
        (image_size.rows, image_size.cols)
    )

    # Stack the planes together to create a 3D numpy array
    return np.stack((y_array, u_array, v_array), axis=-1)


def bytes_to_grey_array(image_bytes: bytes, image_size: ImageSizeInPixels, current_format: ColourFormat
) -> NDArray[Union[uint8, uint16]]:

    if current_format not in [ColourFormat.GREY, ColourFormat.Y8, ColourFormat.Y800, ColourFormat.Y16]:
        if not current_format.num_channels == 1:
            logger.warning("Converting a non-Grey format to Grey - this is slow!")
        if current_format.pixel_dtype == uint8:
            output_format = "gray"
        elif current_format.pixel_dtype == uint16:
            output_format = "gray16le"
        else:
            raise ValueError(
                f"Conversion to numpy for format {current_format} with dtype {current_format.pixel_dtype}" "not supported"
            )

        image_bytes = transcode_image_bytes(image_bytes, image_size, current_format.as_ffmpeg_pixel_format(), output_format)

    image: NDArray[Union[uint8, uint16]] = np.frombuffer(image_bytes, dtype=current_format.pixel_dtype)
    return image.reshape((image_size.rows, image_size.cols))


def bytes_to_rgb_array(
    image_bytes: bytes, image_size: ImageSizeInPixels, current_format: ColourFormat
) -> NDArray[Union[uint8, uint16]]:

    if current_format not in [ColourFormat.BGR24, ColourFormat.RGB24, ColourFormat.BGR10]:
        if not current_format.is_rgb_type:
            logger.warning("Converting a non-RGB pixel format to RGB - this is slow!")

        if current_format.pixel_dtype == uint8:
            output_format = "rgb24"
        elif current_format.pixel_dtype == uint16:
            output_format = "rgb48le"
        else:
            raise ValueError(
                f"Conversion to numpy for format {current_format} with dtype {current_format.pixel_dtype}" "not supported"
            )

        image_bytes = transcode_image_bytes(image_bytes, image_size, current_format.as_ffmpeg_pixel_format(), output_format)

    image: NDArray[Union[uint8, uint16]] = np.frombuffer(image_bytes, dtype=current_format.pixel_dtype)
    return image.reshape((image_size.rows, image_size.cols, 3))


def encode_rgb24_array(image: NDArray[uint8], to_format: ColourFormat) -> bytes:
    image_bytes = image.tobytes()
    dimensions = ImageSizeInPixels(rows=image.shape[0], cols=image.shape[1])
    desired_format = to_format.as_ffmpeg_pixel_format()
    return transcode_image_bytes(image_bytes, dimensions, "rgb24", desired_format)


def convert_rgb16_to_array(image_bytes: bytes, image_size: ImageSizeInPixels) -> NDArray[uint8]:
    # Convert the bytes to a numpy array of uint16
    image = np.frombuffer(image_bytes, dtype=np.uint16)

    # Reshape the array to match the image dimensions
    image = image.reshape((image_size.rows, image_size.cols))

    # Extract the red, green, and blue channels
    red = (image & 0b1111100000000000) >> 11
    green = (image & 0b0000011111100000) >> 5
    blue = image & 0b0000000000011111

    # Convert the channels to uint8 by scaling them to the range [0, 255]
    red = (red << 3) | (red >> 2)  # Scale up from 5 to 8 bits
    green = (green << 2) | (green >> 4)  # Scale up from 6 to 8 bits
    blue = (blue << 3) | (blue >> 2)  # Scale up from 5 to 8 bits

    # Reshape the channels to match the image dimensions
    red = red.reshape((image_size.rows, image_size.cols))
    green = green.reshape((image_size.rows, image_size.cols))
    blue = blue.reshape((image_size.rows, image_size.cols))

    # Stack the channels to form the final RGB image
    rgb_image = np.stack((red, green, blue), axis=-1)

    return rgb_image.astype(uint8)


def convert_rgb_to_array(image_bytes: bytes, image_size: ImageSizeInPixels, bits_per_channel: Tuple[int, int, int]) -> NDArray[uint8]:
    # Convert the bytes to a numpy array of uint16
    image = np.frombuffer(image_bytes, dtype=np.uint16)

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
    rgb_image = np.stack((red, green, blue), axis=-1)

    return rgb_image.astype(np.uint8)


def convert_rgb10_to_array(image_bytes: bytes, image_size: ImageSizeInPixels) -> NDArray[uint16]:
    # Calculate the number of pixels
    num_pixels = image_size.rows * image_size.cols

    # Calculate the number of bytes required for RGB10 data
    num_bytes = num_pixels * 4  # Each pixel requires 4 bytes (10 bits for each channel + 2 padding bits)

    # Convert the bytes to a numpy array of uint32
    image = np.frombuffer(image_bytes[:num_bytes], dtype=np.uint32)

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
    rgb_image = np.stack((red, green, blue), axis=-1)

    return rgb_image.astype(np.uint16)

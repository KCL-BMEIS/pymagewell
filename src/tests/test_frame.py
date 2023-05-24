from datetime import datetime
from typing import Union

import pytest
from numpy import uint16, uint8, where
from numpy.typing import NDArray

from pymagewell import ColourFormat
from pymagewell.conversion import (
    AlphaChannelLocation,
    check_if_ffmpeg_available,
    encode_rgb24_array,
    transcode_image_bytes,
)
from pymagewell.pro_capture_device.device_settings import ColourSpace, RGBChannelOrder
from pymagewell.pro_capture_device.mock_pro_capture_device import MOCK_RESOLUTION, create_mock_frame
from pymagewell.video_frame import VideoFrame, VideoFrameTimestamps


def _make_frame(test_frame_rgb24_array: NDArray[uint8], colour_format: ColourFormat) -> VideoFrame:
    _frame_timestamps = VideoFrameTimestamps(datetime.now(), datetime.now(), datetime.now(), datetime.now())
    _frame_dimensions = MOCK_RESOLUTION

    if colour_format == ColourFormat.RGB24:
        image_bytes = test_frame_rgb24_array.tobytes()
    else:
        check_if_ffmpeg_available("FFMPEG is required to run frame decode tests.")
        image_bytes = encode_rgb24_array(test_frame_rgb24_array, colour_format)
    frame = VideoFrame(
        string_buffer=image_bytes, dimensions=_frame_dimensions, timestamps=_frame_timestamps, format=colour_format
    )
    return frame


@pytest.mark.parametrize(
    "colour_format", [rgb_format for rgb_format in ColourFormat if rgb_format.colour_space == ColourSpace.RGB]
)
def test_video_frame_rgb_to_array(colour_format: ColourFormat) -> None:
    _test_frame_rgb24_array = create_mock_frame()
    frame = _make_frame(_test_frame_rgb24_array, colour_format)
    _decode_and_compare(frame, _test_frame_rgb24_array)


@pytest.mark.parametrize(
    "colour_format", [rgb_format for rgb_format in ColourFormat if rgb_format.colour_space == ColourSpace.GREY]
)
def test_video_frame_grey_to_array(colour_format: ColourFormat) -> None:
    _test_frame_grey_array = create_mock_frame().sum(axis=2).astype(colour_format.pixel_dtype)
    image_bytes = transcode_image_bytes(
        _test_frame_grey_array.tobytes(),
        image_size=MOCK_RESOLUTION,
        current_format=ColourFormat.GREY.as_ffmpeg_pixel_format(),
        desired_format=colour_format.as_ffmpeg_pixel_format(),
    )
    frame = VideoFrame(
        string_buffer=image_bytes,
        dimensions=MOCK_RESOLUTION,
        timestamps=VideoFrameTimestamps(datetime.now(), datetime.now(), datetime.now(), datetime.now()),
        format=colour_format,
    )
    assert frame.as_array().size == (MOCK_RESOLUTION.rows * MOCK_RESOLUTION.cols)
    _decode_and_compare(frame, _test_frame_grey_array)


def _decode_and_compare(frame: VideoFrame, test_frame_array: NDArray[Union[uint8, uint16]]) -> None:
    frame_array = frame.as_array(channel_order=RGBChannelOrder.RGB, alpha_channel_location=AlphaChannelLocation.IGNORE)
    assert frame_array.size == test_frame_array.size
    num_mismatched_elements = len(where(frame_array.squeeze() != test_frame_array))
    percent_mismatched = 100 * (num_mismatched_elements / frame_array.size)
    assert percent_mismatched < 1.0


@pytest.mark.parametrize(
    "colour_format", [yuv_format for yuv_format in ColourFormat if yuv_format.colour_space == ColourSpace.YUV]
)
def test_video_frame_yuv_to_array(colour_format: ColourFormat) -> None:
    with pytest.raises(NotImplementedError):
        _test_frame_rgb24_array = create_mock_frame()
        frame = _make_frame(_test_frame_rgb24_array, colour_format)
        frame.as_array(channel_order=RGBChannelOrder.RGB, alpha_channel_location=AlphaChannelLocation.IGNORE)

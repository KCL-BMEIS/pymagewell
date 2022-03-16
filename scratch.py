from dataclasses import dataclass
from typing import Tuple

from mwcapture.libmwcapture import mw_capture, MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN, MWCAP_VIDEO_QUANTIZATION_UNKNOWN, \
    MWFOURCC_NV12


@dataclass
class VideoSettings:
    color_format: int = MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN
    quantisation: int = MWCAP_VIDEO_QUANTIZATION_UNKNOWN
    dimensions: Tuple[int, int] = (1920, 1080)
    fourcc: int = MWFOURCC_NV12

capturer = mw_capture()
capturer.mw_capture_init_instance()
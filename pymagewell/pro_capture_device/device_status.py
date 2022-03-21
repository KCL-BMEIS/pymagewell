import datetime
from dataclasses import dataclass
from enum import Enum

from mwcapture.libmwcapture import mw_video_capture_status, mw_video_signal_status, MWCAP_VIDEO_SIGNAL_NONE, \
    MWCAP_VIDEO_SIGNAL_UNSUPPORTED, MWCAP_VIDEO_SIGNAL_LOCKING, MWCAP_VIDEO_SIGNAL_LOCKED, mwcap_video_buffer_info, \
    MWCAP_VIDEO_FRAME_STATE_INITIAL, MWCAP_VIDEO_FRAME_STATE_BUFFERED, MWCAP_VIDEO_FRAME_STATE_F0_BUFFERING, \
    MWCAP_VIDEO_FRAME_STATE_F1_BUFFERING, mwcap_video_frame_info, mwcap_smpte_timecode
from pymagewell.pro_capture_device.device_settings import ImageSizeInPixels, AspectRatio, ImageCoordinateInPixels, \
    FrameTimeCode


class SignalState(Enum):
    NONE = MWCAP_VIDEO_SIGNAL_NONE
    UNSUPPORTED = MWCAP_VIDEO_SIGNAL_UNSUPPORTED
    LOCKING = MWCAP_VIDEO_SIGNAL_LOCKING
    LOCKED = MWCAP_VIDEO_SIGNAL_LOCKED


@dataclass
class SignalStatus:
    state: SignalState
    start_position: ImageCoordinateInPixels
    image_dimensions: ImageSizeInPixels
    total_dimensions: ImageSizeInPixels
    interlaced: bool
    frame_period_s: float
    aspect_ratio: AspectRatio
    segmented: bool

    @classmethod
    def from_mw_video_signal_status(cls, status: mw_video_signal_status) -> 'SignalStatus':
        return SignalStatus(
            state=SignalState(status.state),
            start_position=ImageCoordinateInPixels(col=status.cols, row=status.rows),
            image_dimensions=ImageSizeInPixels(cols=status.cx, rows=status.cy),
            total_dimensions=ImageSizeInPixels(cols=status.cxTotal, rows=status.cyTotal),
            interlaced=bool(status.bInterlaced),
            frame_period_s=float(status.dwFrameDuration),
            aspect_ratio=AspectRatio(ver=status.nAspectY, hor=status.nAspectX),
            segmented=bool(status.bSegmentedFrame)
        )


@dataclass
class TransferStatus:
    frame_index: int
    whole_frame_transferred: bool
    num_lines_transferred: int
    num_lines_transferred_previously: int

    @classmethod
    def from_mw_video_capture_status(cls, status: mw_video_capture_status) -> 'TransferStatus':
        return TransferStatus(
            frame_index=status.iFrame,
            whole_frame_transferred=status.bFrameCompleted,
            num_lines_transferred=status.cyCompleted,
            num_lines_transferred_previously=status.cyCompletedPrev
        )


@dataclass
class OnDeviceBufferStatus:
    buffer_size_in_frames: int
    """Maximum number of frames in on-board cache"""
    num_chunks_being_buffered: int
    """The number of the slices being bufferred. A frame of video data may contain multiple slices."""
    num_chunks_in_buffer: int
    """The sequence number of slices the latest bufferred piece"""
    buffering_field_index: int
    """The sequence number of fields being bufferred"""
    last_buffered_field_index: int
    """The sequence number of the latest bufferred field"""
    last_buffered_frame_index: int
    """The sequence number of the latest bufferred frame"""
    num_fully_buffered_frames: int
    """Number of fully bufferred full frames"""

    @classmethod
    def from_mwcap_video_buffer_info(cls, info: mwcap_video_buffer_info) -> 'OnDeviceBufferStatus':
        return OnDeviceBufferStatus(
            buffer_size_in_frames=info.cMaxFrames,
            num_chunks_being_buffered=info.iNewestBuffering,
            num_chunks_in_buffer=info.iNewestBuffered,
            buffering_field_index=info.iBufferingFieldIndex,
            last_buffered_field_index=info.iBufferedFieldIndex,
            last_buffered_frame_index=info.iNewestBufferedFullFrame,
            num_fully_buffered_frames=info.cBufferedFullFrames
        )


class FrameState(Enum):
    INTIAL = MWCAP_VIDEO_FRAME_STATE_INITIAL
    BUFFERING_TOP_SUBFRAME = MWCAP_VIDEO_FRAME_STATE_F0_BUFFERING
    BUFFERING_BOTTOM_SUBFRAME = MWCAP_VIDEO_FRAME_STATE_F1_BUFFERING
    BUFFERED = MWCAP_VIDEO_FRAME_STATE_BUFFERED


@dataclass
class FrameStatus:
    state: FrameState
    interlaced: bool
    segmented: bool
    dimensions: ImageSizeInPixels
    aspect_ratio: AspectRatio
    top_frame_time_code: FrameTimeCode
    bottom_frame_time_code: FrameTimeCode

    @classmethod
    def from_mwcap_video_frame_info(cls, info: mwcap_video_frame_info) -> 'FrameStatus':
        return FrameStatus(
            state=FrameState(info.state),
            interlaced=bool(info.bInterlaced),
            segmented=bool(info.bSegmentedFrame),
            dimensions=ImageSizeInPixels(cols=info.cx, rows=info.cy),
            aspect_ratio=AspectRatio(hor=info.nAspectX, ver=info.nAspectY),
            top_frame_time_code=FrameTimeCode.from_mwcap_smpte_timecode(info.aSMPTETimeCodes[0:4]),
            bottom_frame_time_code=FrameTimeCode.from_mwcap_smpte_timecode(info.aSMPTETimeCodes[4:])
        )

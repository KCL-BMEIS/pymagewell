import platform
from ctypes import *

MW_V_FOURCC_FMT_NV12 = 25
MW_A_SAMPLE_FMT_S16 = 1
MW_V_CODEC_H264 = 28
MW_V_CODEC_H265 = 174

MW_VENC_FRAME_TYPE_UNKNOWN = 0
MW_VENC_FRAME_TYPE_IDR =1
MW_VENC_FRAME_TYPE_I= 2
MW_VENC_FRAME_TYPE_P= 3
MW_VENC_FRAME_TYPE_B= 4
MW_VENC_FRAME_TYPE_COUNT = 5

class mw_venc_frame_info(Structure):
    _pack_ = 1
    _fields_ = [('frame_type',c_int32),
                ('delay',c_int32),
                ('pts',c_int64)]

mw_encode_callback = CFUNCTYPE(None,py_object,c_void_p,c_int32,c_int32,c_int32,c_int64)

class mw_av_encoder(object):
    def __init__(self):
        super().__init__()
        self.m_lib_av_encoder = 0
        if platform.system()=='Windows':
            t_bits,t_linkage = platform.architecture()
            if t_bits == '64bit':
                self.m_lib_path = "mwcapture\\bin\\x64\\mw_av_encoderd.dll"
            elif t_bits == '32bit':
                self.m_lib_path = "mwcapture\\bin\\x86\\mw_av_encoderd.dll"
            else:
                raise AssertionError("ERROR:Current Source doesn't support %s"%(t_bits))
            try:
                self.m_lib_av_encoder = cdll.LoadLibrary(self.m_lib_path)
            except OSError as identifier:
                raise AssertionError("ERROR:load %s failed - %s\n"%(self.m_lib_path,identifier))
            else:
                self.load_win_funcs()
        else:
            raise AssertionError("ERROR:Current Source doesn't support %s"%(t_bits))

    def load_win_funcs(self):
        self.m_lib_av_encoder.mw_video_encoder_open.restype = c_void_p
        self.m_lib_av_encoder.mw_video_encoder_open.argtypes = [
            c_int32,
            c_int32,
            c_uint32,
            c_int32,
            c_int32,
            c_int32,
            c_int32,
            mw_encode_callback,
            py_object]
        self.m_lib_av_encoder.mw_video_encode_frame.argtypes = [
            c_void_p,
            c_void_p,
            c_int64]
        self.m_lib_av_encoder.mw_video_encoder_close.argtypes= [c_void_p]
        self.m_lib_av_encoder.mw_audio_encoder_open.restype = c_void_p
        self.m_lib_av_encoder.mw_audio_encoder_open.argtypes = [
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32,
            mw_encode_callback,
            py_object]
        self.m_lib_av_encoder.mw_audio_encode_frame.argtypes = [
            c_void_p,
            c_voidp,
            c_uint32,
            c_int64]
        self.m_lib_av_encoder.mw_audio_encoder_close.argtypes = [c_void_p]

    def mw_avenc_init(self):
        if self.m_lib_av_encoder == 0:
            return -1
        self.m_lib_av_encoder.mw_av_encode_init()
        return 0

    def mw_venc_encoder_open(self,
        width,
        height,
        fourcc,
        bitrate,
        fps,
        gopsize,
        ish265,
        callback,
        param):
        if self.m_lib_av_encoder == 0:
            return -1
        return self.m_lib_av_encoder.mw_video_encoder_open(
            width,
            height,
            fourcc,
            bitrate,
            fps,
            gopsize,
            ish265,
            callback,
            param
        )


    def mw_venc_encode_frame(self,hvenc,data,ts):
        if self.m_lib_av_encoder == 0:
            return -1
        return self.m_lib_av_encoder.mw_video_encode_frame(
            hvenc,data,ts)

    def mw_venc_encoder_close(self,hvenc):
        if self.m_lib_av_encoder == 0:
            return -1
        return self.m_lib_av_encoder.mw_video_encoder_close(hvenc)

    def mw_aenc_encoder_open(self,
        channels,
        smaplerate,
        bitspersample,
        bitrate,
        callback,
        param):
        if self.m_lib_av_encoder == 0:
            return -1
        return self.m_lib_av_encoder.mw_audio_encoder_open(
            channels,
            smaplerate,
            bitspersample,
            bitrate,
            callback,
            param
        )

    def mw_aenc_encode_frame(self,aenc,data,datalen,ts):
        if self.m_lib_av_encoder == 0:
            return -1
        return self.m_lib_av_encoder.mw_audio_encode_frame(aenc,data,datalen,ts)

    def mw_aenc_encoder_close(self,aenc):
        if self.m_lib_av_encoder == 0:
            return -1
        return self.m_lib_av_encoder.mw_audio_encoder_close(aenc)
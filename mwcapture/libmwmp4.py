import platform
from ctypes import *

#mw_mp4_status_t;
MW_MP4_STATUS_SUCCESS          = 0
MW_MP4_STATUS_UNEXPECTED_ERROR = 1
MW_MP4_STATUS_INVALID_PARAM    = 2
#mw_mp4_video_type_t
MW_MP4_VIDEO_TYPE_UNKNOWN = 0
MW_MP4_VIDEO_TYPE_H264    = 1
MW_MP4_VIDEO_TYPE_HEVC    = 2
MW_MP4_VIDEO_TYPE_H265    = MW_MP4_VIDEO_TYPE_HEVC
#mw_mp4_h264_parameter_set_t
'''typedef struct _mw_mp4_h264_parameter_set {
    uint8_t*		sps;        // can be nullptr if it's contained in the stream
    int16_t			sps_size;   // can be 0 if it's contained in the stream
    uint8_t*		pps;        // can be nullptr if it's contained in the stream
    int16_t			pps_size;   // can be 0 if it's contained in the stream
} mw_mp4_h264_parameter_set_t;'''

class mw_mp4_h264_parameter_set_t(Structure):
    _pack_ = 1
    _fields_ = [('sps',c_char_p),
               ('sps_size',c_int16),
               ('pps',c_char_p),
               ('pps_size',c_int16),
               ('reserve1',c_char_p),
               ('reserve2',c_int16)]

'''typedef struct _mw_mp4_hevc_parameter_set {
    uint8_t*		sps;            // can be nullptr if it's contained in the stream
    int16_t			sps_size;       // can be 0 if it's contained in the stream
    uint8_t*		pps;            // can be nullptr if it's contained in the stream
    int16_t			pps_size;       // can be 0 if it's contained in the stream
    uint8_t*		vps;            // can be nullptr if it's contained in the stream
    int16_t			vps_size;       // can be 0 if it's contained in the stream
} mw_mp4_hevc_parameter_set_t;'''

class mw_mp4_hevc_parameter_set_t(Structure):
    _pack_ = 1
    _fields_ = [('sps',c_char_p),
               ('sps_size',c_int16),
               ('pps',c_char_p),
               ('pps_size',c_int16),
               ('vps',c_char_p),
               ('vps_size',c_int16)]

'''
typedef struct _mw_mp4_video_info {
    mw_mp4_video_type_t codec_type;
    uint32_t		    timescale;
    uint16_t		    width;
    uint16_t		    height;

    union{
        mw_mp4_h264_parameter_set_t h264;
        mw_mp4_hevc_parameter_set_t hevc;
    };
} mw_mp4_video_info_t;'''

class mw_mp4_h264_info_t(Structure):
    _pack_ = 1
    _fields_ = [('codec_type',c_uint32),
               ('timescale',c_uint32),
               ('width',c_uint16),
               ('height',c_uint16),
               ('h264',mw_mp4_h264_parameter_set_t)]

class mw_mp4_hevc_info_t(Structure):
    _pack_ = 1
    _fields_ = [('codec_type',c_uint32),
               ('timescale',c_uint32),
               ('width',c_uint16),
               ('height',c_uint16),
               ('hevc',mw_mp4_hevc_parameter_set_t)]

#mw_mp4_audio_codec_t
MW_MP4_AUDIO_TYPE_UNKNOWN    = 0
MW_MP4_AUDIO_TYPE_AAC        = 1
MW_MP4_AUDIO_TYPE_ADTS_AAC   = 2


'''typedef struct _mw_mp4_audio_info {
    mw_mp4_audio_codec_t codec_type;
    uint32_t		     timescale;
    uint16_t		     sample_rate; // can be 0 if codec is aac with adts
    uint16_t		     channels; // can be 0 if codec is aac with  adts
    uint8_t			     profile; // can be 0 if codec is aac with  adts
} mw_mp4_audio_info_t;'''

class mw_mp4_audio_info_t(Structure):
    _pack_ = 1
    _fields_ = [('codec_type',c_uint32),
               ('timescale',c_uint32),
               ('sample_rate',c_uint16),
               ('channels',c_uint16),
               ('profile',c_uint8)]

#mw_mp4_subtitle_type_t
MW_MP4_SUBTITLE_TYPE_UNKNOWN = 0
MW_MP4_SUBTITLE_TYPE_CC608   = 1
MW_MP4_SUBTITLE_TYPE_CC708   = 2

'''
typedef struct _mw_mp4_subtitle_info {
    mw_mp4_subtitle_type_t  codec_type;
    uint32_t		        timescale;
} mw_mp4_subtitle_info_t;'''

class mw_mp4_subtitle_info_t(Structure):
    _pack_ = 1
    _fields_ = [('codec_type',c_uint32),
               ('timescale',c_uint32)]

class mw_mp4(object):
    def __init__(self):
        super().__init__()
        self.m_lib_mp4 = 0
        if platform.system() == "Windows":
            t_bits,t_linkage = platform.architecture()
            if t_bits == '64bit':
                self.m_lb_path = "mwcapture\\bin\\x64\\mw_mp4.dll"
            elif t_bits == '32bit':
                self.m_lb_path = "mwcapture\\bin\\x86\\mw_mp4.dll"
            else:
                raise AssertionError("ERROR:unsupported architecture - %s"%(t_bits))
            try:
                self.m_lib_mp4 = cdll.LoadLibrary(self.m_lb_path)
            except OSError as identifier:
                raise AssertionError("ERROR:load %s failed - %s\n"%(self.m_lb_path,identifier))
            else:
                self.load_win_funcs()
        else:
            raise AssertionError("ERROR:Current Source doesn't support %s"%(platform.systerm()))
            

    def load_win_funcs(self):
        self.m_lib_mp4.mw_mp4_open.restype = c_void_p
        self.m_lib_mp4.mw_mp4_open.argtypes=[c_void_p]
        self.m_lib_mp4.mw_mp4_close.argtypes=[c_void_p]
        self.m_lib_mp4.mw_mp4_set_video.argtypes=[c_void_p, c_void_p]
        self.m_lib_mp4.mw_mp4_set_audio.argtypes=[c_void_p, c_void_p]
        self.m_lib_mp4.mw_mp4_set_subtitle.argtypes=[c_void_p, c_void_p]
        self.m_lib_mp4.mw_mp4_write_video.argtypes=[c_void_p, c_void_p, c_int32, c_int64]
        self.m_lib_mp4.mw_mp4_write_audio.argtypes=[c_void_p, c_void_p, c_int32, c_int64]
        self.m_lib_mp4.mw_mp4_write_subtitle.argtypes=[c_void_p, c_void_p, c_int32, c_int64]
        self.m_lib_mp4.mw_mp4_repair.argtypes=[c_void_p, c_bool]

    def mw_mp4_open(self,filename):
        if self.m_lib_mp4 == 0:
            return -1
        t_b_str = filename.encode('utf-8')
        t_adr = create_string_buffer(t_b_str)
        return self.m_lib_mp4.mw_mp4_open(addressof(t_adr))

    def mw_mp4_close(self,handle):
        if self.m_lib_mp4 == 0:
            return -1
        return self.m_lib_mp4.mw_mp4_close(handle)

    def mw_mp4_set_video(self,handle,video_info):
        if self.m_lib_mp4 == 0:
            return -1
        return self.m_lib_mp4.mw_mp4_set_video(handle,video_info)

    def mw_mp4_set_audio(self,handle,audio_info):
        if self.m_lib_mp4 == 0:
            return -1
        return self.m_lib_mp4.mw_mp4_set_audio(handle,audio_info)

    def mw_mp4_write_video(self,handle,data,size,ts):
        if self.m_lib_mp4 == 0:
            return -1
        return self.m_lib_mp4.mw_mp4_write_video(handle,data,size,ts)

    def mw_mp4_write_audio(self,handle,data,size,ts):
        if self.m_lib_mp4 == 0:
            return -1
        return self.m_lib_mp4.mw_mp4_write_audio(handle,data,size,ts)
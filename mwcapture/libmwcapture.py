import os
import platform
from ctypes import *
from pathlib import Path

MW_SUCCEEDED = 0
MW_FAILED = 1
MW_INVALID_PARAMS = 2


def mw_fourcc(str):
    t_val = 0
    i = 0
    for c in str:
        t_num = ord(c)
        t_val += (t_num<<i)
        i+=8
    return t_val

MWFOURCC_UNK   = mw_fourcc('UNKN')
MWFOURCC_GREY  = mw_fourcc('GREY')
MWFOURCC_Y800  = mw_fourcc('Y800')
MWFOURCC_BGRA  = mw_fourcc('BGRA')
MWFOURCC_Y8    = mw_fourcc('Y8  ')
MWFOURCC_Y16   = mw_fourcc('Y16 ')
MWFOURCC_RGB15 = mw_fourcc('RGB5')
MWFOURCC_RGB16 = mw_fourcc('RGB6')
MWFOURCC_RGB24 = mw_fourcc('RGB ')
MWFOURCC_RGBA  = mw_fourcc('RGBA')
MWFOURCC_ARGB  = mw_fourcc('ARGB')
MWFOURCC_BGR15 = mw_fourcc('BGR5')
MWFOURCC_BGR16 = mw_fourcc('BGR6')
MWFOURCC_BGR24 = mw_fourcc('BGR ')
MWFOURCC_BGRA  = mw_fourcc('BGRA')
MWFOURCC_ABGR  = mw_fourcc('ABGR')
MWFOURCC_NV16  = mw_fourcc('NV16')
MWFOURCC_NV61  = mw_fourcc('NV61')
MWFOURCC_I422  = mw_fourcc('I422')
MWFOURCC_YV16  = mw_fourcc('YV16')
MWFOURCC_YUY2  = mw_fourcc('YUY2')
MWFOURCC_YUYV  = mw_fourcc('YUYV')
MWFOURCC_UYVY  = mw_fourcc('UYVY')
MWFOURCC_YVYU  = mw_fourcc('YVYU')
MWFOURCC_VYUY  = mw_fourcc('VYUY')
MWFOURCC_I420  = mw_fourcc('I420')
MWFOURCC_IYUV  = mw_fourcc('IYUV')
MWFOURCC_NV12  = mw_fourcc('NV12')
MWFOURCC_YV12  = mw_fourcc('YV12')
MWFOURCC_NV21  = mw_fourcc('NV21')
MWFOURCC_P010  = mw_fourcc('P010')
MWFOURCC_P210  = mw_fourcc('P210')
MWFOURCC_IYU2  = mw_fourcc('IYU2')
MWFOURCC_V308  = mw_fourcc('V308')
MWFOURCC_AYUV  = mw_fourcc('AYUV')
MWFOURCC_UYVA  = mw_fourcc('UYVA')
MWFOURCC_V408  = mw_fourcc('v408')
MWFOURCC_VYUA  = mw_fourcc('VYUA')
MWFOURCC_V210  = mw_fourcc('v210')
MWFOURCC_Y410  = mw_fourcc('Y410')
MWFOURCC_V410  = mw_fourcc('v410')
MWFOURCC_RGB10 = mw_fourcc('RG10')
MWFOURCC_BGR10 = mw_fourcc('BG10')

def fourcc_is_packed(fourcc):
    if fourcc == MWFOURCC_NV12:
        return False
    
    if fourcc == MWFOURCC_NV21:
        return False

    if fourcc == MWFOURCC_YV12:
        return False

    if fourcc == MWFOURCC_IYUV:
        return False

    if fourcc == MWFOURCC_I420:
        return False

    if fourcc == MWFOURCC_I422:
        return False

    if fourcc == MWFOURCC_YV16:
        return False

    if fourcc == MWFOURCC_NV16:
        return False

    if fourcc == MWFOURCC_NV61:
        return False

    if fourcc == MWFOURCC_P010:
        return False

    if fourcc == MWFOURCC_P210:
        return False

    return True

def fourcc_get_bpp(fourcc):
    if fourcc == MWFOURCC_GREY:
        return 8
    if fourcc == MWFOURCC_Y800:
        return 8
    if fourcc == MWFOURCC_Y8:
        return 8

    if fourcc == MWFOURCC_I420:
        return 12
    if fourcc == MWFOURCC_IYUV:
        return 12
    if fourcc == MWFOURCC_YV12:
        return 12
    if fourcc == MWFOURCC_NV12:
        return 12
    if fourcc == MWFOURCC_NV21:
        return 12
    
    if fourcc == MWFOURCC_Y16:
        return 16
    if fourcc == MWFOURCC_RGB15:
        return 16
    if fourcc == MWFOURCC_BGR15:
        return 16
    if fourcc == MWFOURCC_RGB16:
        return 16
    if fourcc == MWFOURCC_BGR16:
        return 16
    if fourcc == MWFOURCC_YUY2:
        return 16
    if fourcc == MWFOURCC_YUYV:
        return 16
    if fourcc == MWFOURCC_UYVY:
        return 16
    if fourcc == MWFOURCC_YVYU:
        return 16
    if fourcc == MWFOURCC_VYUY:
        return 16
    if fourcc == MWFOURCC_I422:
        return 16
    if fourcc == MWFOURCC_YV16:
        return 16
    if fourcc == MWFOURCC_NV16:
        return 16
    if fourcc == MWFOURCC_NV61:
        return 16

    if (fourcc == MWFOURCC_IYU2 or 
        fourcc == MWFOURCC_V308 or 
        fourcc == MWFOURCC_RGB24 or 
        fourcc == MWFOURCC_BGR24 or 
        fourcc == MWFOURCC_P010 or 
        fourcc == MWFOURCC_V210):
        return 24
    
    if fourcc == MWFOURCC_AYUV:
        return 32
    if fourcc == MWFOURCC_UYVA:
        return 32
    if fourcc == MWFOURCC_V408:
        return 32
    if fourcc == MWFOURCC_VYUA:
        return 32
    if fourcc == MWFOURCC_RGBA:
        return 32
    if fourcc == MWFOURCC_BGRA:
        return 32
    if fourcc == MWFOURCC_ARGB:
        return 32
    if fourcc == MWFOURCC_ABGR:
        return 32
    if fourcc == MWFOURCC_Y410:
        return 32
    if fourcc == MWFOURCC_V410:
        return 32
    if fourcc == MWFOURCC_P210:
        return 32
    if fourcc == MWFOURCC_RGB10:
        return 32
    if fourcc == MWFOURCC_BGR10:
        return 32
    return 0

def fourcc_calc_min_stride(fourcc,cx,algin):
    t_b_packed = fourcc_is_packed(fourcc)
    if t_b_packed == True:
        if fourcc == MWFOURCC_V210:
            cx = (cx+47)//48*48
            cbline = cx*8//3
        else:
            t_n_bpp = fourcc_get_bpp(fourcc)
            cbline = (cx*t_n_bpp)//8
    else:
        if fourcc == MWFOURCC_P010:
            cbline = cx*2
        elif fourcc == MWFOURCC_P210:
            cbline = cx*2
        else:
            cbline = cx
    return (cbline+algin-1)&~(algin-1)

def fourcc_calc_image_size(fourcc,cx,cy,cbstride):
    t_b_packed = fourcc_is_packed(fourcc)
    if t_b_packed == True:
        t_cb_line = 0
        if fourcc == MWFOURCC_V210:
            cx = (cx+47)//48*48
            t_cb_line = cx*8//3
        else:
            t_n_bpp = fourcc_get_bpp(fourcc)
            t_cb_line = (cx*t_n_bpp)//8
        if cbstride < t_cb_line:
            return 0
        return cbstride*cy
    else:
        if cbstride < cx:
            return 0
        
        if (fourcc == MWFOURCC_NV12 or 
            fourcc == MWFOURCC_NV21 or 
            fourcc == MWFOURCC_YV12 or 
            fourcc == MWFOURCC_IYUV or 
            fourcc == MWFOURCC_I420):
            if cbstride&1!=0 or cy&1 !=0:
                return 0
            return cbstride*cy*3//2
        elif (fourcc == MWFOURCC_I422 or 
              fourcc == MWFOURCC_YV16 or 
              fourcc == MWFOURCC_NV16 or 
              fourcc == MWFOURCC_NV61):
            if cbstride&1 != 0:
                return 0
            return cbstride*cy*2
        elif fourcc == MWFOURCC_P010:
            if cbstride&3!=0 or cy&1 !=0:
                return 0
            return cbstride*cy*3//2
        elif fourcc == MWFOURCC_P210:
            if cbstride & 3 != 0:
                return 0
            return cbstride*cy*2
        else:
            return 0

# sdk
MWCAP_AUDIO_SAMPLES_PER_FRAME = 192
MWCAP_AUDIO_MAX_NUM_CHANNELS = 8

MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE = 0x0020
MWCAP_NOTIFY_AUDIO_SIGNAL_CHANGE = 0x0040
MWCAP_NOTIFY_AUDIO_FRAME_BUFFERED = 0x1000

MWCAP_VIDEO_FRAME_ID_NEWEST_BUFFERED = -1

MWCAP_AUDIO_CAPTURE_NODE_DEFAULT = 0

'''
typedef void (*VIDEO_CAPTURE_CALLBACK)(BYTE *pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam);
'''
mw_video_capture_callback = CFUNCTYPE(None,c_void_p,c_int32,c_uint64,py_object)

'''
typedef void (__stdcall *AUDIO_CAPTURE_STDCALL_CALLBACK)(const BYTE * pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam);
'''
mw_audio_capture_callback = CFUNCTYPE(None,c_void_p,c_int32,c_uint64,py_object)

class mw_version(object):
    def __init__(self):
        super().__init__()
        self.m_maj = 0
        self.m_min = 0
        self.m_build = 0

class mw_device_time(object):
    def __init__(self):
        super().__init__()
        self.m_ll_device_time = c_int64(0)

class mw_notify_status(object):
    def __init__(self):
        super().__init__()
        self.m_ll_notify_status = 0

'''
typedef struct _MWCAP_CHANNEL_INFO {		
	WORD											wFamilyID;								///<Product type, refers to #MW_FAMILY_ID
	WORD											wProductID;								///<device ID, refers to  #MWCAP_PRODUCT_ID
	CHAR											chHardwareVersion;						///<Hardware version ID
	BYTE											byFirmwareID;							///<Firmware ID
	DWORD											dwFirmwareVersion;						///<Firmware version
	DWORD											dwDriverVersion;						///<Driver version
	CHAR											szFamilyName[MW_FAMILY_NAME_LEN];		///<Product name
	CHAR											szProductName[MW_PRODUCT_NAME_LEN];		///<Product type
	CHAR											szFirmwareName[MW_FIRMWARE_NAME_LEN];	///<Firmware name
	CHAR											szBoardSerialNo[MW_SERIAL_NO_LEN];		///<Hardware serial number
	BYTE											byBoardIndex;							///<Rotary ID located on the capture card, 0~F.
	BYTE											byChannelIndex;							///<Channel index of the capture card, which starts from 0.
} MWCAP_CHANNEL_INFO;
'''
class mw_cap_channel_info(Structure):
    _pack_ = 1
    _fields_ = [('wFamilyID',c_ushort),
               ('wProductID',c_ushort),
               ('chHardwareVersion',c_char),
               ('byFirmwareID',c_byte),
               ('dwFirmwareVersion',c_ulong),
               ('dwDriverVersion',c_ulong),
               ('szFamilyName',c_char*64),
               ('szProductName',c_char*64),
               ('szFirmwareName',c_char*64),
               ('szBoardSerialNo',c_char*16),
               ('byBoardIndex',c_byte),
               ('byChannelIndex',c_bool)]

'''
typedef enum _MWCAP_VIDEO_SIGNAL_STATE {
	MWCAP_VIDEO_SIGNAL_NONE,																///<No signal
	MWCAP_VIDEO_SIGNAL_UNSUPPORTED,															///<Invalid signal. The capture card detects a signal but can not lock it.
	MWCAP_VIDEO_SIGNAL_LOCKING,																///<Locking signal. The signal is valid, but unlocked.
	MWCAP_VIDEO_SIGNAL_LOCKED																///<Locked signal. The capture card is ready to capture the input signal.
} MWCAP_VIDEO_SIGNAL_STATE;
'''
MWCAP_VIDEO_SIGNAL_NONE = 0
MWCAP_VIDEO_SIGNAL_UNSUPPORTED = 1
MWCAP_VIDEO_SIGNAL_LOCKING = 2
MWCAP_VIDEO_SIGNAL_LOCKED = 3

'''
typedef enum _MWCAP_VIDEO_FRAME_TYPE {
	MWCAP_VIDEO_FRAME_2D							= 0x00,///<2D video frame
	MWCAP_VIDEO_FRAME_3D_TOP_AND_BOTTOM_FULL		= 0x01,///<Top-and-Bottom 3D  video frame at full resolution
	MWCAP_VIDEO_FRAME_3D_TOP_AND_BOTTOM_HALF		= 0x02,///<Top-and-Bottom 3D  video frame at half resolution
	MWCAP_VIDEO_FRAME_3D_SIDE_BY_SIDE_FULL			= 0x03,///<Full side-by-side 3D video frame
	MWCAP_VIDEO_FRAME_3D_SIDE_BY_SIDE_HALF			= 0x04 ///<Half side-by-side 3D video frame
} MWCAP_VIDEO_FRAME_TYPE;
'''
MWCAP_VIDEO_FRAME_2D = 0x00
MWCAP_VIDEO_FRAME_3D_TOP_AND_BOTTOM_FULL = 0x01
MWCAP_VIDEO_FRAME_3D_TOP_AND_BOTTOM_HALF = 0x02
MWCAP_VIDEO_FRAME_3D_SIDE_BY_SIDE_FULL = 0x03
MWCAP_VIDEO_FRAME_3D_SIDE_BY_SIDE_HALF = 0x04

'''
typedef enum _MWCAP_VIDEO_COLOR_FORMAT {         	
	MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN				= 0x00,///<unknown color format
	MWCAP_VIDEO_COLOR_FORMAT_RGB					= 0x01,///<RGB
	MWCAP_VIDEO_COLOR_FORMAT_YUV601					= 0x02,///<YUV601
	MWCAP_VIDEO_COLOR_FORMAT_YUV709					= 0x03,///<YUV709
	MWCAP_VIDEO_COLOR_FORMAT_YUV2020				= 0x04,///<YUV2020
	MWCAP_VIDEO_COLOR_FORMAT_YUV2020C				= 0x05 ///<YUV2020C
} MWCAP_VIDEO_COLOR_FORMAT;	
'''
MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN = 0x00
MWCAP_VIDEO_COLOR_FORMAT_RGB = 0x01
MWCAP_VIDEO_COLOR_FORMAT_YUV601 = 0x02
MWCAP_VIDEO_COLOR_FORMAT_YUV709 = 0x03
MWCAP_VIDEO_COLOR_FORMAT_YUV2020 = 0x04
MWCAP_VIDEO_COLOR_FORMAT_YUV2020C = 0x05

'''
typedef enum _MWCAP_VIDEO_QUANTIZATION_RANGE {			
	MWCAP_VIDEO_QUANTIZATION_UNKNOWN				= 0x00,///<the default quantization range
	MWCAP_VIDEO_QUANTIZATION_FULL					= 0x01,///<Full range, which has 8-bit data. The black-white color range is 0-255/1023/4095/65535.
	MWCAP_VIDEO_QUANTIZATION_LIMITED				= 0x02 ///<Limited range, which has 8-bit data. The black-white color range is 16/64/256/4096-235(240)/940(960)/3760(3840)/60160(61440).
} MWCAP_VIDEO_QUANTIZATION_RANGE;
'''
MWCAP_VIDEO_QUANTIZATION_UNKNOWN = 0x00
MWCAP_VIDEO_QUANTIZATION_FULL = 0x01
MWCAP_VIDEO_QUANTIZATION_LIMITED = 0x02

'''
typedef enum _MWCAP_VIDEO_SATURATION_RANGE {		
	MWCAP_VIDEO_SATURATION_UNKNOWN					= 0x00,///<The default saturation_range range
	MWCAP_VIDEO_SATURATION_FULL						= 0x01,///<Full range, which has 8-bit data. The black-white color range is 0-255/1023/4095/65535
	MWCAP_VIDEO_SATURATION_LIMITED					= 0x02,///<Limited range, which has 8-bit data. The black-white color range is 16/64/256/4096-235(240)/940(960)/3760(3840)/60160(61440)
	MWCAP_VIDEO_SATURATION_EXTENDED_GAMUT			= 0x03 ///<Extended range, which has 8-bit data. The black-white color range is 1/4/16/256-254/1019/4079/65279
} MWCAP_VIDEO_SATURATION_RANGE;	
'''
MWCAP_VIDEO_SATURATION_UNKNOWN = 0x00
MWCAP_VIDEO_SATURATION_FULL = 0x01
MWCAP_VIDEO_SATURATION_LIMITED = 0x02
MWCAP_VIDEO_SATURATION_EXTENDED_GAMUT = 0x03

'''
typedef enum _MWCAP_VIDEO_FRAME_STATE {
	MWCAP_VIDEO_FRAME_STATE_INITIAL,															///<Initial
	MWCAP_VIDEO_FRAME_STATE_F0_BUFFERING,														///<Buffering top subframe
	MWCAP_VIDEO_FRAME_STATE_F1_BUFFERING,														///<Buffering bottom subframe
	MWCAP_VIDEO_FRAME_STATE_BUFFERED															///<Fully bufferred video frame 
} MWCAP_VIDEO_FRAME_STATE;
'''
MWCAP_VIDEO_FRAME_STATE_INITIAL = 0
MWCAP_VIDEO_FRAME_STATE_F0_BUFFERING = 1
MWCAP_VIDEO_FRAME_STATE_F1_BUFFERING = 2
MWCAP_VIDEO_FRAME_STATE_BUFFERED = 3

'''
typedef enum _MWCAP_VIDEO_DEINTERLACE_MODE {
	MWCAP_VIDEO_DEINTERLACE_WEAVE					= 0x00,///<Weave mode
	MWCAP_VIDEO_DEINTERLACE_BLEND					= 0x01,///<Blend mode
	MWCAP_VIDEO_DEINTERLACE_TOP_FIELD				= 0x02,///<Only uses top subframe data
	MWCAP_VIDEO_DEINTERLACE_BOTTOM_FIELD			= 0x03 ///<Only uses bottom subframe data
} MWCAP_VIDEO_DEINTERLACE_MODE;
'''
MWCAP_VIDEO_DEINTERLACE_WEAVE = 0x00
MWCAP_VIDEO_DEINTERLACE_BLEND = 0x01
MWCAP_VIDEO_DEINTERLACE_TOP_FIELD = 0x02
MWCAP_VIDEO_DEINTERLACE_BOTTOM_FIELD = 0x03

'''
typedef enum _MWCAP_VIDEO_ASPECT_RATIO_CONVERT_MODE {
	MWCAP_VIDEO_ASPECT_RATIO_IGNORE					= 0x00,///<Ignore: Ignores the original aspect ratio and stretches to full-screen.
	MWCAP_VIDEO_ASPECT_RATIO_CROPPING				= 0x01,///<Cropping: Expands to full-screen and remove parts of the image when necessary to keep the original aspect ratio.
	MWCAP_VIDEO_ASPECT_RATIO_PADDING				= 0x02 ///<Padding: Fits to screen and add black borders to keep the original aspect ratio.
} MWCAP_VIDEO_ASPECT_RATIO_CONVERT_MODE;
'''
MWCAP_VIDEO_ASPECT_RATIO_IGNORE = 0x00
MWCAP_VIDEO_ASPECT_RATIO_CROPPING = 0x01
MWCAP_VIDEO_ASPECT_RATIO_PADDING = 0x02

'''
typedef enum _MW_FAMILY_ID {
	MW_FAMILY_ID_PRO_CAPTURE					= 0x00,							///<Pro Capture family
	MW_FAMILY_ID_ECO_CAPTURE					= 0x01,							///<Eco Capture family
	MW_FAMILY_ID_USB_CAPTURE					= 0x02							///<USB Capture family
} MW_FAMILY_ID;
'''
MW_FAMILY_ID_PRO_CAPTURE = 0x00
MW_FAMILY_ID_ECO_CAPTURE = 0x01
MW_FAMILY_ID_USB_CAPTURE = 0x02

'''
typedef struct _MWCAP_VIDEO_SIGNAL_STATUS {
	MWCAP_VIDEO_SIGNAL_STATE						state;									///<Defines the accessibility of this video signal
	int												cols;										///<Horizontal start position
	int												rows;										///<Vertical start position
	int												cx;										///<Image width
	int												cy;										///<Image height
	int												cxTotal;								///<Total width
	int												cyTotal;								///<Total height
	BOOLEAN											bInterlaced;							///<Whether the signal is interlaced 
	DWORD											dwFrameDuration;						///<Frame interval of video frame
	int												nAspectX;								///<Width of video ratio
	int												nAspectY;								///<Height of video ratio
	BOOLEAN											bSegmentedFrame;						///<Whether the signal is segmented frame
	MWCAP_VIDEO_FRAME_TYPE							frameType;								///<video frame type
	MWCAP_VIDEO_COLOR_FORMAT						colorFormat;							///<video color format
	MWCAP_VIDEO_QUANTIZATION_RANGE					quantRange;								///<Quantization range
	MWCAP_VIDEO_SATURATION_RANGE					satRange;								///<saturation_range range
} MWCAP_VIDEO_SIGNAL_STATUS;
'''
class mw_video_signal_status(Structure):
    _pack_ = 1
    _fields_ = [('state',c_int32),
                  ('cols',c_int32),
                  ('rows',c_int32),
                  ('cx',c_int32),
                  ('cy',c_int32),
                  ('cxTotal',c_int32),
                  ('cyTotal',c_int32),
                  ('bInterlaced',c_bool),
                  ('dwFrameDuration',c_int32),
                  ('nAspectX',c_int32),
                  ('nAspectY',c_int32),
                  ('bSegmentedFrame',c_bool),
                  ('frameType',c_int32),
                  ('colorFormat',c_int32),
                  ('quantRange',c_int32),
                  ('satRange',c_int32)]

'''
typedef struct _MWCAP_AUDIO_SIGNAL_STATUS {
	WORD											wChannelValid;							///<Valid audio channel mask.The lowest bit indicates whether the 1st and 2nd channels are valid, the second bit indicates whether the 3rd and 4th channels are valid, the third bit indicates whether the 5th and 6th channels are valid, and the fourth bit indicates whether the 7th and 8th channels are valid.
	BOOLEAN											bLPCM;									///<Whether the signal is LPCM
	BYTE											cBitsPerSample;							///<Bit depth of each audio sampling
	DWORD											dwSampleRate;							///<Sample rate
	BOOLEAN											bChannelStatusValid;					///<Whether channel status is valid
	IEC60958_CHANNEL_STATUS							channelStatus;							///<The audio channel status
} MWCAP_AUDIO_SIGNAL_STATUS;
'''
class mw_audio_signal_status(Structure):
    _pack_ = 1
    _fields_ = [('wChannelValid',c_int16),
                ('bLPCM',c_bool),
                ('cBitsPerSample',c_byte),
                ('dwSampleRate',c_int32),
                ('bChannelStatusValid',c_bool),
                ('channelStatus',c_byte*24)]

'''
typedef struct _MWCAP_VIDEO_CAPS {
	DWORD											dwCaps;									///<Capture capability
	WORD											wMaxInputWidth;							///<Max input width
	WORD											wMaxInputHeight;						///<Max input height
	WORD											wMaxOutputWidth;						///<Max output width
	WORD											wMaxOutputHeight;						///<Max output height
} MWCAP_VIDEO_CAPS;
'''
class mw_video_caps(Structure):
    _pack_ = 1
    _fields_ = [('dwCaps',c_int32),
                  ('wMaxInputWidth',c_int16),
                  ('wMaxInputHeight',c_int16),
                  ('wMaxOutputWidth',c_int16),
                  ('wMaxOutputHeight',c_int16)]

'''
typedef struct _MWCAP_VIDEO_CAPTURE_STATUS {
	MWCAP_PTR64										pvContext;																	///<The context of video capture

	BOOLEAN											bPhysicalAddress;															///<Whether to use the physical address to store the capture data 
	union {
		MWCAP_PTR64									pvFrame;																	///<The memory address to store the capture data 
		LARGE_INTEGER								liPhysicalAddress;															///<The physical address to store the capture data
	};

	int												iFrame;																		///<The index of capturing frame
	BOOLEAN											bFrameCompleted;															///<Whether a frame is fully captured
	WORD											cyCompleted;																///<Number of frames captured
	WORD											cyCompletedPrev;															///<Number of frames captured previously
} MWCAP_VIDEO_CAPTURE_STATUS;
'''
class mw_video_capture_status(Structure):
    _pack_ = 1
    _fields_ = [('pvContext',c_int64),           # this need to be experienced
                  ('bPhysicalAddress',c_bool),
                  ('pvFrame',c_uint64),
                  ('iFrame',c_int32),
                  ('bFrameCompleted',c_bool),
                  ('cyCompleted',c_int16),
                  ('cyCompletedPrev',c_int16)]


'''
typedef struct _MWCAP_VIDEO_BUFFER_INFO {
	DWORD											cMaxFrames;									///<Maximum number of frames in on-board cache

	BYTE											iNewestBuffering;							///<The number of the slices being bufferred. A frame of video data may contain multiple slices.
	BYTE											iBufferingFieldIndex;						///<The sequence number of fields being bufferred.

	BYTE											iNewestBuffered;							///<The sequence number of slices the latest bufferred piece.
	BYTE											iBufferedFieldIndex;						///<The sequence number of the latest bufferred field

	BYTE											iNewestBufferedFullFrame;					///<The sequence number of the latest bufferred frame
	DWORD											cBufferedFullFrames;						///<Number of fully bufferred full frames
} MWCAP_VIDEO_BUFFER_INFO;
'''
class mwcap_video_buffer_info(Structure):
    _pack_ = 1
    _fields_ = [('cMaxFrames',c_int32),
                  ('iNewestBuffering',c_byte),
                  ('iBufferingFieldIndex',c_byte),
                  ('iNewestBuffered',c_byte),
                  ('iBufferedFieldIndex',c_byte),
                  ('iNewestBufferedFullFrame',c_byte),
                  ('cBufferedFullFrames',c_int32)]

'''
typedef struct _MWCAP_SMPTE_TIMECODE {
	BYTE 											byFrames;									///<Frames number
	BYTE											bySeconds;									///<Seconds
	BYTE											byMinutes;									///<Minutes
	BYTE											byHours;									///<Hours
} MWCAP_SMPTE_TIMECODE;
'''
class mwcap_smpte_timecode(Structure):
    _pack_ = 1
    _fields_ = [('byFrames',c_byte),
                ('bySeconds',c_byte),
                ('byMinutes',c_byte),
                ('byHours',c_byte)]

'''
typedef struct _MWCAP_VIDEO_FRAME_INFO {
	MWCAP_VIDEO_FRAME_STATE							state;										///<The state of the video framess

	BOOLEAN											bInterlaced;								///<Whether an interlaced signal
	BOOLEAN											bSegmentedFrame;							///<Whether a segmented frame
	BOOLEAN											bTopFieldFirst;								///<Whether the top subframe is in front
	BOOLEAN											bTopFieldInverted;							///<Whether to reverse the top subframe

	int												cx;											///<Width of video frames
	int												cy;											///<Height of video frames
	int												nAspectX;									///<Width of the ratio 
	int												nAspectY;									///<Height of the ratio

	LONGLONG										allFieldStartTimes[2];						///<Start time of capturing top and bottom subframe respectively
	LONGLONG										allFieldBufferedTimes[2];					///<Fully bufferred time of top and bottom frame respectively
	MWCAP_SMPTE_TIMECODE							aSMPTETimeCodes[2];							///<Time code of top and bottom frame respectively
} MWCAP_VIDEO_FRAME_INFO;
'''
class mwcap_video_frame_info(Structure):
    _pack_ = 1
    _fields_ = [('state',c_int32),
                ('bInterlaced',c_bool),
                ('bSegmentedFrame',c_bool),
                ('bTopFieldFirst',c_bool),
                ('bTopFieldInverted',c_bool),
                ('cx',c_int32),
                ('cy',c_int32),
                ('nAspectX',c_int32),
                ('nAspectY',c_int32),
                ('allFieldStartTimes',c_int64*2),
                ('allFieldBufferedTimes',c_int64*2),
                ('aSMPTETimeCodes',c_ubyte*8)] #crnb change from c_ubyte*8

'''
typedef struct _MWCAP_AUDIO_CAPTURE_FRAME {
	DWORD											cFrameCount;																///<Number of bufferred frames
	DWORD											iFrame;																		///<Current frame index
	DWORD											dwSyncCode;																	///<Sync code of audio frame data
	DWORD											dwFlags;																	///<Reserved
	LONGLONG										llTimestamp;																///<The timestamp of audio frame
	DWORD											adwSamples[MWCAP_AUDIO_SAMPLES_PER_FRAME * MWCAP_AUDIO_MAX_NUM_CHANNELS];	///<Audio sample data. Each sample is 32-bit width, and high bit effective. The priority of the path is: Left0, Left1, Left2, Left3, right0, right1, right2, right3
} MWCAP_AUDIO_CAPTURE_FRAME;
'''
class mwcap_audio_capture_frame(Structure):
    _pack_ = 1
    _fields_ = [('cFrameCount',c_int32),
                ('iFrame',c_int32),
                ('dwSyncCode',c_int32),
                ('dwFlags',c_int32),
                ('llTimestamp',c_int64),
                #('adwSamples',c_int32*(192*8))]
                ('adwSamples',c_ubyte*(192*8*4))]

'''
typedef struct _MWCAP_VIDEO_ECO_CAPTURE_OPEN {
	MWCAP_PTR64										hEvent;																///<Handle of capture event

	DWORD											dwFOURCC;															///<Capture format
	WORD											cx;																	///<Width
	WORD											cy;																	///<Height
	LONGLONG										llFrameDuration;													///<Interval, -1 indicates follow format of input source
} MWCAP_VIDEO_ECO_CAPTURE_OPEN;
'''
class mwcap_video_eco_capture_open(Structure):
    _pack_ = 1
    _fields_ = [('hEvent',c_int64),
                ('dwFOURCC',c_int32),
                ('cx',c_int16),
                ('cy',c_int16),
                ('llFrameDuration',c_int64)]

'''
typedef struct _MWCAP_VIDEO_ECO_CAPTURE_FRAME {
	MWCAP_PTR64										pvFrame;															///<The storage address for video capturing
	DWORD											cbFrame;															///<The size of storage for video capturing
	DWORD											cbStride;															///<Width of capture video frame

	BOOLEAN											bBottomUp;															///<Whether to flip
	MWCAP_VIDEO_DEINTERLACE_MODE					deinterlaceMode;													///<DeinterlaceMode

	MWCAP_PTR64										pvContext;															///<Context of ECO 
} MWCAP_VIDEO_ECO_CAPTURE_FRAME;
'''
class mwcap_video_eco_capture_frame(Structure):
    _pack_ = 1
    _fields_ = [('pvFrame',c_int64),
                ('cbFrame',c_int32),
                ('cbStride',c_int32),
                ('bBottomUp',c_bool),
                ('deinterlaceMode',c_int32),
                ('pvContext',c_int64)]

'''
typedef struct _MWCAP_VIDEO_ECO_CAPTURE_STATUS {
	MWCAP_PTR64										pvContext;															///<frame label for DWORD
	MWCAP_PTR64										pvFrame;															///<Frame data address
	LONGLONG										llTimestamp;														///<Timestamp
} MWCAP_VIDEO_ECO_CAPTURE_STATUS;
'''
class mwcap_video_eco_capture_status(Structure):
    _pack_ = 1
    _fields_ = [('pvContext',c_int64),
                ('pvFrame',c_int64),
                ('llTimestamp',c_int64)]


'''
typedef struct tagRECT
{
    LONG    left;
    LONG    top;
    LONG    right;
    LONG    bottom;
} RECT, *PRECT, NEAR *NPRECT, FAR *LPRECT;
'''
class mw_rect(Structure):
    _pack_ = 1
    _fields_ = [('left',c_int32),
                ('top',c_int32),
                ('right',c_int32),
                ('bottom',c_int32)]

class mw_capture(object):
    def __init__(self):
        super().__init__()
        self.m_lib_mw_capture = 0
        t_bits,t_linkage = platform.architecture()
        if platform.system() == "Windows":
            if t_bits == '64bit':
                self.m_lib_path = str(Path(os.path.abspath(__file__)).parent.joinpath("bin/x64/LibMWCapture.dll"))
            elif t_bits == '32bit':
                self.m_lib_path = str(Path(os.path.abspath(__file__)).parent.joinpath("bin/x86/LibMWCapture.dll"))
            else:
                raise AssertionError("ERROR:unsupported architecture - %s\n"%(t_bits))
            try:
                self.m_lib_mw_capture = cdll.LoadLibrary(self.m_lib_path)
            except OSError as identifier:
                raise AssertionError("ERROR:load %s failed - %s\n"%(self.m_lib_path,identifier))
            else:
                self.load_win_funcs()
        elif platform.system() == "Linux":
            raise AssertionError("ERROR:Current Source dosen't support linux")
        else:
            raise AssertionError("ERROR:Current Source doesn't support %s"%(platform.system()))
    
    def load_win_funcs(self):
        self.m_lib_mw_capture.MWOpenChannelByPath.restype= c_void_p
        self.m_lib_mw_capture.MWCloseChannel.argtypes=[c_void_p]
        self.m_lib_mw_capture.MWCreateVideoCapture.restype = c_void_p
        self.m_lib_mw_capture.MWCreateVideoCapture.argtypes=[
            c_void_p,
            c_int32,
            c_int32,
            c_int32,
            c_int32,
            mw_video_capture_callback,
            py_object]
        self.m_lib_mw_capture.MWDestoryVideoCapture.argtypes = [c_void_p]
        self.m_lib_mw_capture.MWCreateAudioCapture.restype = c_void_p
        self.m_lib_mw_capture.MWCreateAudioCapture.argtypes = [
            c_void_p,
            c_int32,
            c_int32,
            c_int16,
            c_int16,
            mw_audio_capture_callback,
            py_object]
        self.m_lib_mw_capture.MWDestoryAudioCapture.argtypes = [c_void_p]
        self.m_lib_mw_capture.MWGetVideoSignalStatus.argtypes = [
            c_void_p,
            POINTER(mw_video_signal_status)]
        self.m_lib_mw_capture.MWGetAudioSignalStatus.argtypes = [
            c_void_p,
            POINTER(mw_audio_signal_status)]
        self.m_lib_mw_capture.MWGetVideoCaps.argtypes = [
            c_void_p,
            POINTER(mw_video_caps)]
        self.m_lib_mw_capture.MWStartVideoCapture.argtypes = [
            c_void_p,
            c_void_p]
        self.m_lib_mw_capture.MWRegisterNotify.restype = c_int64
        self.m_lib_mw_capture.MWRegisterNotify.argtypes = [
            c_void_p,
            c_void_p,
            c_int64]
        self.m_lib_mw_capture.MWRegisterTimer.restype = c_int64
        self.m_lib_mw_capture.MWRegisterTimer.argtypes = [
            c_void_p,
            c_void_p]
        self.m_lib_mw_capture.MWGetDeviceTime.argtypes = [
            c_void_p,
            POINTER(c_int64)]
        self.m_lib_mw_capture.MWPinVideoBuffer.argtypes = [
            c_void_p,
            c_void_p,
            c_int32]
        self.m_lib_mw_capture.MWScheduleTimer.argtypes = [
            c_void_p,
            c_int64,
            c_int64]
        self.m_lib_mw_capture.MWGetVideoBufferInfo.argtypes = [
            c_void_p,
            POINTER(mwcap_video_buffer_info)]
        self.m_lib_mw_capture.MWGetVideoFrameInfo.argtypes = [
            c_void_p,
            c_byte,
            POINTER(mwcap_video_frame_info)]
        self.m_lib_mw_capture.MWCaptureVideoFrameToVirtualAddressEx.argtypes = [
            c_void_p,    # HCHANNEL 						hChannel
            c_int32,    # int							iFrame
            c_void_p,    # LPBYTE							pbFrame
            c_int32,    # DWORD							cbFrame
            c_int32,    # DWORD							cbStride
            c_bool,     # BOOLEAN							bBottomUp
            c_int64,    # MWCAP_PTR64						pvContext
            c_int32,    # DWORD							dwFOURCC
            c_int32,    # int								cx
            c_int32,    # int								cy
            c_int32,    # DWORD							dwProcessSwitchs
            c_int32,    # int								cyParitalNotify
            c_int64,    # HOSD							hOSDImage
            c_void_p,    # const RECT *					pOSDRects
            c_int32,    # int								cOSDRects
            c_int16,    # SHORT							sContrast
            c_int16,    # SHORT							sBrightness
            c_int16,    # SHORT							sSaturation
            c_int16,    # SHORT							sHue
            c_int32,    # MWCAP_VIDEO_DEINTERLACE_MODE			deinterlaceMode
            c_int32,    # MWCAP_VIDEO_ASPECT_RATIO_CONVERT_MODE	aspectRatioConvertMode
            c_void_p,    # const RECT *							pRectSrc
            c_void_p,    # const RECT *							pRectDest
            c_int32,    # int										nAspectX
            c_int32,    # int										nAspectY
            c_int32,    # MWCAP_VIDEO_COLOR_FORMAT				colorFormat
            c_int32,    # MWCAP_VIDEO_QUANTIZATION_RANGE			quantRange
            c_int32     # MWCAP_VIDEO_SATURATION_RANGE			satRange
        ]
        self.m_lib_mw_capture.MWUnpinVideoBuffer.argtypes = [
            c_void_p,
            c_void_p]
        self.m_lib_mw_capture.MWUnregisterNotify.argtypes = [
            c_void_p,
            c_int64]
        self.m_lib_mw_capture.MWUnregisterTimer.argtypes = [
            c_void_p,
            c_int64]
        self.m_lib_mw_capture.MWStopVideoCapture.argtypes = [c_void_p]
        self.m_lib_mw_capture.MWGetChannelInfo.argtypes = [
            c_void_p,
            POINTER(mw_cap_channel_info)]
        self.m_lib_mw_capture.MWGetVideoCaptureStatus.argtypes = [
            c_void_p,
            POINTER(mw_video_capture_status)]
        self.m_lib_mw_capture.MWStartAudioCapture.argtypes = [c_void_p]
        self.m_lib_mw_capture.MWGetNotifyStatus.argtypes = [
            c_void_p,
            c_int64,
            POINTER(c_int64)]
        self.m_lib_mw_capture.MWCaptureAudioFrame.argtypes = [
            c_void_p,
            POINTER(mwcap_audio_capture_frame)]
        self.m_lib_mw_capture.MWStopAudioCapture.argtypes = [c_void_p]
        self.m_lib_mw_capture.MWStartVideoEcoCapture.argtypes = [
            c_void_p,
            POINTER(mwcap_video_eco_capture_open)]
        self.m_lib_mw_capture.MWGetVideoEcoCaptureStatus.argtypes = [
            c_void_p,
            POINTER(mwcap_video_eco_capture_status)]
        self.m_lib_mw_capture.MWCaptureSetVideoEcoFrame.argtypes = [
            c_void_p,
            c_void_p]
        self.m_lib_mw_capture.MWStopVideoEcoCapture.argtypes = [c_void_p]
        

    def mw_capture_init_instance(self):
        if self.m_lib_mw_capture == 0:
            return False
        return (self.m_lib_mw_capture.MWCaptureInitInstance())

    def mw_capture_exit_instance(self):
        if self.m_lib_mw_capture == 0:
            return
        self.m_lib_mw_capture.MWCaptureExitInstance()

    def mw_get_version(self,version):
        if self.m_lib_mw_capture == 0:
            return
        t_maj = c_byte(0)
        t_min = c_byte(0)
        t_build = c_ushort(0)
        t_ret = 0
        t_ret = self.m_lib_mw_capture.MWGetVersion(
            byref(t_maj),
            byref(t_min),
            byref(t_build))
        print("version %d-%d-%d" %(
            t_maj.value,
            t_min.value,
            t_build.value
        ))
        version.m_maj = t_maj.value
        version.m_min = t_maj.value
        version.m_build = t_build.value
        return t_ret

    def mw_refresh_device(self):
        if self.m_lib_mw_capture == 0:
            return
        self.m_lib_mw_capture.MWRefreshDevice()
    
    def mw_get_channel_count(self):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetChannelCount()

    def mw_get_channel_info_by_index(self,index,channelinfo):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetChannelInfoByIndex(index,byref(channelinfo))

    def mw_get_channel_info(self,hchannel,channelinfo):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetChannelInfo(hchannel,byref(channelinfo))

    def mw_get_device_path(self,index,path):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetDevicePath(index,byref(path))

    def mw_open_channel_by_path(self,path):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWOpenChannelByPath(byref(path))

    def mw_close_channel(self,hchannel):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWCloseChannel(hchannel)
    '''
    HANDLE
    LIBMWCAPTURE_API
    MWCreateVideoCapture(
	    HCHANNEL 						hChannel,
	    int								nWidth,
	    int								nHeight,
	    int								nFourcc,
	    int								nFrameDuration,
	    VIDEO_CAPTURE_CALLBACK			callback,
	    void*							pParam
	)
    '''
    def mw_create_video_capture(
        self,
        hchannel,
        t_n_width,
        t_n_height,
        t_n_fourcc,
        t_n_frame_duration,
        video_callback,
        p_param):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWCreateVideoCapture(
            hchannel,
            t_n_width,
            t_n_height,
            t_n_fourcc,
            t_n_frame_duration,
            video_callback,
            p_param)

    def mw_destory_video_capture(self,hvideo):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWDestoryVideoCapture(hvideo)

    '''
    HANDLE
    LIBMWCAPTURE_API
    MWCreateAudioCapture(
	HCHANNEL						hChannel,
	MWCAP_AUDIO_CAPTURE_NODE        captureNode,
	DWORD							dwSamplesPerSec,
	WORD							wBitsPerSample,
	WORD							wChannels,
	AUDIO_CAPTURE_CALLBACK			callback,
	void*							pParam
	);
    '''
    def mw_create_audio_capture(
        self,
        hchannel,
        capture_node,
        samples_per_sec,
        bits_per_sample,
        channels,
        audio_callback,
        p_param):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWCreateAudioCapture(
            hchannel,
            capture_node,
            samples_per_sec,
            bits_per_sample,
            channels,
            audio_callback,
            p_param
        )

    def mw_destory_audio_capture(self,haudio):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWDestoryAudioCapture(haudio)

    def mw_get_video_signal_status(self,hchannel,videosignalstaus):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetVideoSignalStatus(hchannel,byref(videosignalstaus))

    def mw_get_audio_signal_status(self,hchannel,audiosignalstatus):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetAudioSignalStatus(hchannel,byref(audiosignalstatus))

    def mw_get_video_caps(self,hchannel,videocaps):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetVideoCaps(hchannel,byref(videocaps))

    def mw_start_video_capture(self,hchannel,captureevent):
        if self.m_lib_mw_capture == 0:
            return -1
        # return self.m_lib_mw_capture.MWStartVideoCapture(hchannel,captureevent)
        t_ptr = int(captureevent)
        return self.m_lib_mw_capture.MWStartVideoCapture(hchannel,c_void_p(t_ptr))

    def mw_register_notify(self,hchannel,notifyevent,enablebits):
        if self.m_lib_mw_capture == 0:
            return -1
        # return self.m_lib_mw_capture.MWRegisterNotify(hchannel,notifyevent,enablebits)
        t_ptr = int(notifyevent)
        return self.m_lib_mw_capture.MWRegisterNotify(hchannel,c_void_p(t_ptr),enablebits)

    def mw_register_timer(self,hchannel,timerevent):
        if self.m_lib_mw_capture == 0:
            return -1
        # return self.m_lib_mw_capture.MWRegisterTimer(hchannel,timerevent)
        t_ptr = int(timerevent)
        return self.m_lib_mw_capture.MWRegisterTimer(hchannel,c_void_p(t_ptr))

    def mw_get_device_time(self,hchannel,devicetime):
        if self.m_lib_mw_capture == 0:
            return -1
        t_time = c_int64(0)
        t_ret = self.m_lib_mw_capture.MWGetDeviceTime(hchannel,byref(t_time))
        devicetime.m_ll_device_time = t_time
        return t_ret

    def mw_pin_video_buffer(self,hchannel,buffer,framesize):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWPinVideoBuffer(hchannel,buffer,framesize)

    def mw_schedule_timer(self,hchannel,timernotify,expiretime):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWScheduleTimer(hchannel,timernotify,expiretime)

    def mw_get_video_buffer_info(self, hchannel, videobufferinfo):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetVideoBufferInfo(hchannel,byref(videobufferinfo))

    def mw_get_video_frame_info(self, hchannel, t_index, t_videoframeinfo):
        if self.m_lib_mw_capture == 0:
            return -1
        t_ret = self.m_lib_mw_capture.MWGetVideoFrameInfo(hchannel,t_index,t_videoframeinfo)
        return t_ret

    def mw_capture_video_frame_to_virtual_address_ex(
        self,
        hchannel,
        iframe,
        pbframe,
        cbframe,
        cbstride,
        bbottomup,
        pvcontext,
        dwfourcc,
        cx,
        cy,
        dwprocessswitchs,
        cypartialnotify,
        hosdimage,
        posdrects,
        cosdrects,
        scontrast,
        sbrightness,
        ssaturation,
        shue,
        deinterlacemode,
        aspectratioconvertmode,
        prectsrc,
        prectdest,
        naspectx,
        naspecty,
        colorformat,
        quantrange,
        satrange
        ):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWCaptureVideoFrameToVirtualAddressEx(
            hchannel,
            iframe,
            pbframe,
            cbframe,
            cbstride,
            bbottomup,
            pvcontext,
            dwfourcc,
            cx,
            cy,
            dwprocessswitchs,
            cypartialnotify,
            hosdimage,
            posdrects,
            cosdrects,
            scontrast,
            sbrightness,
            ssaturation,
            shue,
            deinterlacemode,
            aspectratioconvertmode,
            prectsrc,
            prectdest,
            naspectx,
            naspecty,
            colorformat,
            quantrange,
            satrange
        )

    def mw_unpin_video_buffer(self,hchannel,buffer):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWUnpinVideoBuffer(hchannel,buffer)

    def mw_unregister_notify(self,hchannel,hnotify):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWUnregisterNotify(hchannel,hnotify)

    def mw_unregister_timer(self,hchannel,htimer):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWUnregisterTimer(hchannel,htimer)

    def mw_stop_video_capture(self,hchannel):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWStopVideoCapture(hchannel)

    def mw_get_video_capture_status(self,hchannel,video_capture_status):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetVideoCaptureStatus(hchannel,byref(video_capture_status))

    def mw_start_audio_capture(self,hchannel):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWStartAudioCapture(hchannel)

    def mw_get_notify_status(self,hchannel,hnotify,status):
        if self.m_lib_mw_capture == 0:
            return -1
        t_ull_status = c_int64(0)
        t_ret = self.m_lib_mw_capture.MWGetNotifyStatus(hchannel,hnotify,byref(t_ull_status))
        status.m_ll_notify_status = t_ull_status.value
        return t_ret

    def mw_capture_audio_frame(self,hchannel,audioframe):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWCaptureAudioFrame(hchannel,byref(audioframe))

    def mw_stop_audio_capture(self,hchannel):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWStopAudioCapture(hchannel)

    def mw_start_video_eco_capture(self,hchannel,ecocaptureopen):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWStartVideoEcoCapture(hchannel,byref(ecocaptureopen))

    def mw_get_video_eco_capture_status(self,hchannel,capturestatus):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWGetVideoEcoCaptureStatus(hchannel,byref(capturestatus))

    def mwcapture_set_video_eco_frame(self,hchannel,frame):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWCaptureSetVideoEcoFrame(hchannel,frame)

    def mw_stop_video_eco_capture(self,hchannel):
        if self.m_lib_mw_capture == 0:
            return -1
        return self.m_lib_mw_capture.MWStopVideoEcoCapture(hchannel)
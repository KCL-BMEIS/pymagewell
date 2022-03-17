from PyQt5.QtCore import QThread,QObject
from mwcapture.libmwcapture import *
from win32 import win32api,win32event
import threading

class CVideoCaptureThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.m_lib_capture = 0

    def set_capture_lib(self, libcapture):
        self.m_lib_capture = libcapture
        self.m_color_fmt = MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN
        self.m_quant_rng = MWCAP_VIDEO_QUANTIZATION_UNKNOWN
        self.m_h_channel = 0
        self.m_n_cx = 1920
        self.m_n_cy = 1080
        self.m_fourcc = MWFOURCC_YUY2
        self.m_frame_dur = 166667
        self.m_callback = 0
        self.m_caller = 0
        self.m_n_clip = CLIP_NONE
        self.m_h_event_exit = 0
        self.m_b_running = False
        self.m_h_event_capture = 0
        self.m_h_event_notify = 0
        self.m_h_event_timer = 0
        self.m_d_fps = 0

    def set_video_clip(self,clip):
        self.m_n_clip = clip

    def start_video_capture(
        self,
        colorFormat,
        quantRange,
        hchannel,
        cx,
        cy,
        fourcc,
        frameduration,
        callback,
        param,
        clip):
        self.m_color_fmt = colorFormat
        self.m_quant_rng = quantRange
        self.m_h_channel = hchannel
        self.m_n_cx = cx
        self.m_n_cy = cy
        self.m_fourcc = fourcc
        self.m_frame_dur = frameduration
        self.m_callback = callback
        self.m_caller = param
        self.m_n_clip = clip
        self.m_h_event_exit = win32event.CreateEvent(None,False,False,None)
        self.m_b_running = True
        self.start()

    def stop_video_capture(self):
        self.m_b_running = False
        if self.m_h_event_exit != 0:
            win32event.SetEvent(self.m_h_event_exit)
        self.wait()
        if self.m_h_event_exit != 0:
            win32api.CloseHandle(int(self.m_h_event_exit))
            self.m_h_event_exit = 0
        self.m_d_fps = 0.0

    def run(self):
        t_channel_info = mw_cap_channel_info()
        self.m_lib_capture.mw_get_channel_info(self.m_h_channel,t_channel_info)
        if t_channel_info.wFamilyID == MW_FAMILY_ID_PRO_CAPTURE:
            self.video_capture_pro()
        elif t_channel_info.wFamilyID == MW_FAMILY_ID_ECO_CAPTURE:
            self.video_capture_eco()
        else:
            raise AssertionError('ERROR Device')

    def video_capture_pro(self):
        t_cb_stride = fourcc_calc_min_stride(self.m_fourcc,self.m_n_cx,2)
        t_frame_size = fourcc_calc_image_size(self.m_fourcc,self.m_n_cx,self.m_n_cy,t_cb_stride)
        t_buffer = create_string_buffer(3840*2160*4)
        self.m_h_event_capture = win32event.CreateEvent(None,False,False,None)
        self.m_h_event_notify = win32event.CreateEvent(None,False,False,None)
        self.m_h_event_timer = win32event.CreateEvent(None,False,False,None)
        t_ret = MW_SUCCEEDED
        t_b_done = False
        while t_b_done == False:
            t_ret = self.m_lib_capture.mw_start_video_capture(self.m_h_channel, self.m_h_event_capture)
            if t_ret != MW_SUCCEEDED:
                break
            t_h_notify_signal = self.m_lib_capture.mw_register_notify(
                self.m_h_channel,
                self.m_h_event_notify,
                MWCAP_NOTIFY_VIDEO_SIGNAL_CHANGE
            )
            if t_h_notify_signal == 0:
                break
            t_h_notify_timer = self.m_lib_capture.mw_register_timer(
                self.m_h_channel,
                self.m_h_event_timer
            )
            if t_h_notify_timer == 0:
                break
            t_frame_count = 0
            t_ll_begin = mw_device_time()
            t_ret = self.m_lib_capture.mw_get_device_time(
                self.m_h_channel,
                t_ll_begin
            )
            if t_ret != MW_SUCCEEDED:
                break
            t_ll_time_expire = mw_device_time()
            t_ll_time_expire.m_ll_device_time = t_ll_begin.m_ll_device_time
            t_frame_duration = self.m_frame_dur

            t_video_capture_status = mw_video_capture_status()
            t_video_buffer_info = mwcap_video_buffer_info()
            t_video_signal_status = mw_video_signal_status()
            t_video_frame_info = mwcap_video_frame_info()
            t_rc_src = mw_rect()
            t_ll_time_last = mw_device_time()
            t_ll_time_last.m_ll_device_time.value = t_ll_begin.m_ll_device_time.value
            t_ll_time_now = mw_device_time()

            self.m_lib_capture.mw_pin_video_buffer(self.m_h_channel,addressof(t_buffer),t_frame_size)

            while self.m_b_running:
                t_ll_time_expire.m_ll_device_time.value += t_frame_duration
                t_ret = self.m_lib_capture.mw_get_device_time(self.m_h_channel, t_ll_time_now)
                if t_ret != MW_SUCCEEDED:
                    continue
                t_ret = self.m_lib_capture.mw_schedule_timer(self.m_h_channel,t_h_notify_timer,t_ll_time_expire.m_ll_device_time)
                if t_ret != MW_SUCCEEDED:
                    continue
                t_array_event_notify = [self.m_h_event_exit,
                    self.m_h_event_timer,
                    self.m_h_event_notify]
                t_events = tuple(t_array_event_notify)
                t_wait_ret = win32event.WaitForMultipleObjects(t_events, False, win32event.INFINITE)
                print(f"Wait for multiple objects returned: {t_wait_ret}")
                if t_wait_ret == win32event.WAIT_OBJECT_0 + 0:
                    print("Event was EXIT event")
                    break
                elif t_wait_ret == win32event.WAIT_OBJECT_0 + 1:
                    print("Event was TIMER event")
                    t_ret = self.m_lib_capture.mw_get_video_buffer_info(self.m_h_channel,t_video_buffer_info)
                    if t_ret != MW_SUCCEEDED:
                        continue
                    t_ret = self.m_lib_capture.mw_get_video_signal_status(self.m_h_channel,t_video_signal_status)
                    if t_ret != MW_SUCCEEDED:
                        continue
                    t_ret = self.m_lib_capture.mw_get_video_frame_info(
                        self.m_h_channel,
                        t_video_buffer_info.iNewestBufferedFullFrame,
                        t_video_frame_info)
                    if t_ret != MW_SUCCEEDED:
                        continue
                    if self.m_n_clip == CLIP_NONE:
                        t_rc_src.left = 0
                        t_rc_src.top = 0
                        t_rc_src.right = t_video_signal_status.cx
                        t_rc_src.bottom = t_video_signal_status.cy
                    elif self.m_n_clip == CLIP_TOPLEFT:
                        t_rc_src.left = 0
                        t_rc_src.top = 0
                        t_rc_src.right = t_video_signal_status.cx//2
                        t_rc_src.bottom = t_video_signal_status.cy//2
                    elif self.m_n_clip == CLIP_TOPRIGHT:
                        t_rc_src.left = t_video_signal_status.cx//2
                        t_rc_src.top = 0
                        t_rc_src.right = t_video_signal_status.cx
                        t_rc_src.bottom = t_video_signal_status.cy//2
                    elif self.m_n_clip == CLIP_BOTTOMLEFT:
                        t_rc_src.left = 0
                        t_rc_src.top = t_video_signal_status.cy//2
                        t_rc_src.right = t_video_signal_status.cx//2
                        t_rc_src.bottom = t_video_signal_status.cy
                    elif self.m_n_clip == CLIP_BOTTOMRIGHT:
                        t_rc_src.left = t_video_signal_status.cx//2
                        t_rc_src.top = t_video_signal_status.cy//2
                        t_rc_src.right = t_video_signal_status.cx
                        t_rc_src.bottom = t_video_signal_status.cy
                    else:
                        t_rc_src.left = 0
                        t_rc_src.top = 0
                        t_rc_src.right = t_video_signal_status.cx
                        t_rc_src.bottom = t_video_signal_status.cy
                    t_ret = self.m_lib_capture.mw_capture_video_frame_to_virtual_address_ex(
                        self.m_h_channel,
                        MWCAP_VIDEO_FRAME_ID_NEWEST_BUFFERED,
                        addressof(t_buffer),
                        t_frame_size,
                        t_cb_stride,
                        False,
                        0,
                        self.m_fourcc,
                        self.m_n_cx,
                        self.m_n_cy,
                        0,
                        0,
                        0,
                        0,
                        0,
                        100,
                        0,
                        100,
                        0,
                        MWCAP_VIDEO_DEINTERLACE_BLEND,
                        MWCAP_VIDEO_ASPECT_RATIO_IGNORE,
                        addressof(t_rc_src),
                        0,
                        0,
                        0,
                        MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN,
                        MWCAP_VIDEO_QUANTIZATION_UNKNOWN,
                        MWCAP_VIDEO_SATURATION_UNKNOWN
                    )

                    win32event.WaitForSingleObject(self.m_h_event_capture, win32event.INFINITE)
                    self.m_lib_capture.mw_get_device_time(self.m_h_channel, t_ll_time_now)
                    t_ret = self.m_lib_capture.mw_get_video_capture_status(self.m_h_channel,t_video_capture_status)
                    if self.m_callback != 0:
                        t_size = t_frame_size
                        if self.m_fourcc == MWFOURCC_NV12:
                            t_size = self.m_n_cx*self.m_n_cy*2
                        self.m_callback(addressof(t_buffer), t_size, t_ll_time_now.m_ll_device_time.value)  # this function is CAVCaptureWid.video_callback()
                    t_frame_count += 1

                    if t_frame_count%10 == 0:
                        self.m_d_fps = t_frame_count*10000000/(t_ll_time_now.m_ll_device_time.value- t_ll_time_last.m_ll_device_time.value)
                        if t_ll_time_now.m_ll_device_time.value - t_ll_time_last.m_ll_device_time.value > 3000000 :
                            t_ll_time_last.m_ll_device_time.value = t_ll_time_now.m_ll_device_time.value
                            t_frame_count = 0
                elif t_wait_ret == win32event.WAIT_OBJECT_0 + 2:
                    print("Event was NOTIFY event")
                    t_ret = self.m_lib_capture.mw_get_video_signal_status(self.m_h_channel,t_video_signal_status)
                    if t_ret != MW_SUCCEEDED:
                        continue
                    if self.m_callback != 0:
                        print('video signal changed')
            self.m_lib_capture.mw_unpin_video_buffer(self.m_h_channel,addressof(t_buffer))
            t_ret = self.m_lib_capture.mw_unregister_notify(self.m_h_channel,t_h_notify_signal)
            t_ret = self.m_lib_capture.mw_unregister_timer(self.m_h_channel,t_h_notify_timer)
            t_ret = self.m_lib_capture.mw_stop_video_capture(self.m_h_channel)
            t_b_done = True
        win32api.CloseHandle(int(self.m_h_event_capture))
        self.m_h_event_capture = 0
        win32api.CloseHandle(int(self.m_h_event_timer))
        self.m_h_event_timer = 0
        win32api.CloseHandle(int(self.m_h_event_notify))
        self.m_h_event_notify = 0

    def video_capture_eco(self):
        self.m_h_event_capture = win32event.CreateEvent(None,False,False,None)
        self.m_h_event_notify = win32event.CreateEvent(None,False,False,None)
        t_h_notify_signal = self.m_lib_capture.mw_register_notify(
            self.m_h_channel,
            self.m_h_event_notify,
            MWCAP_NOTIFY_AUDIO_SIGNAL_CHANGE)
        t_ret = MW_SUCCEEDED
        t_eco_capture_open = mwcap_video_eco_capture_open()
        t_eco_capture_open.hEvent = self.m_h_event_capture
        t_eco_capture_open.dwFOURCC = self.m_fourcc
        t_eco_capture_open.cx = self.m_n_cx
        t_eco_capture_open.cy = self.m_n_cy
        t_eco_capture_open.llFrameDuration = 166667
        t_capture_status = mwcap_video_eco_capture_status()
        t_video_signal_status = mw_video_signal_status()
        t_ret = self.m_lib_capture.mw_start_video_eco_capture(self.m_h_channel,t_eco_capture_open)
        t_cb_stride = fourcc_calc_min_stride(self.m_fourcc,self.m_n_cx,2)
        t_frame_size = fourcc_calc_image_size(self.m_fourcc,self.m_n_cx,self.m_n_cy,t_cb_stride)
        videoframe = []
        videobuffer = []
        for i in range(3):
            t_video_frame = mwcap_video_eco_capture_frame()
            t_video_buffer = create_string_buffer(3840*2160*4)
            t_video_frame.pvFrame = addressof(t_video_buffer)
            t_video_frame.cbFrame = t_frame_size
            t_video_frame.cbStride = t_cb_stride
            t_video_frame.pvContext = addressof(t_video_frame)
            videobuffer.append(t_video_buffer)
            videoframe.append(t_video_frame)
            t_ret = self.m_lib_capture.mwcapture_set_video_eco_frame(self.m_h_channel,addressof(t_video_frame))
        t_tm_begin = mw_device_time()
        t_ret = self.m_lib_capture.mw_get_device_time(self.m_h_channel,t_tm_begin)
        t_tm_last = mw_device_time()
        t_tm_last.m_ll_device_time.value = t_tm_begin.m_ll_device_time.value
        t_tm_current = mw_device_time()
        t_frame_count = 0
        t_trans_size = t_frame_size
        if self.m_fourcc == MWFOURCC_NV12:
            t_trans_size = self.m_n_cx*self.m_n_cy*2
        while self.m_b_running == True:
            t_array_event_notify = [
                self.m_h_event_exit,
                self.m_h_event_capture,
                self.m_h_event_notify]
            t_events = tuple(t_array_event_notify)
            t_wait_ret = win32event.WaitForMultipleObjects(t_events,False,win32event.INFINITE)
            if t_wait_ret == win32event.WAIT_OBJECT_0:
                break
            elif t_wait_ret == win32event.WAIT_OBJECT_0 + 1:
                while self.m_b_running == True:
                    t_ret = self.m_lib_capture.mw_get_video_eco_capture_status(
                        self.m_h_channel,
                        t_capture_status
                    )
                    if t_ret == MW_FAILED or t_capture_status.pvFrame == 0:
                        break
                    if self.m_callback != 0:
                        self.m_callback(
                            t_capture_status.pvFrame,
                            t_trans_size,
                            t_capture_status.llTimestamp)
                    t_ret = self.m_lib_capture.mwcapture_set_video_eco_frame(
                        self.m_h_channel,
                        t_capture_status.pvContext
                    )
                    t_frame_count += 1
                    self.m_lib_capture.mw_get_device_time(self.m_h_channel,t_tm_current)
                    if t_frame_count%10 == 0:
                        self.m_d_fps = t_frame_count*10000000/(t_tm_current.m_ll_device_time.value-t_tm_last.m_ll_device_time.value)
                        if t_tm_current.m_ll_device_time.value - t_tm_last.m_ll_device_time.value > 30000000:
                            t_tm_last.m_ll_device_time = t_tm_current.m_ll_device_time
                            t_frame_count = 0
            elif t_wait_ret == win32event.WAIT_OBJECT_0 + 2:
                t_ret = self.m_lib_capture.mw_get_video_signal_status(self.m_h_channel,t_video_signal_status)
                if t_ret != MW_SUCCEEDED:
                    continue
        self.m_lib_capture.mw_stop_video_eco_capture(self.m_h_channel)
        win32api.CloseHandle(int(self.m_h_event_capture))
        self.m_h_event_capture = 0
        self.m_lib_capture.mw_unregister_notify(self.m_h_channel,t_h_notify_signal)
        win32api.CloseHandle(int(self.m_h_event_notify))
        self.m_h_event_notify= 0
        
class CAudioCaptureThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.m_lib_capture = 0
        self.m_h_channel = 0
        self.m_callbcak = 0
        self.m_caller = 0
        self.m_h_event_exit = 0
        self.m_b_running = False
        self.m_samples_per_sec = 0

    def set_capture_lib(self,libcapture):
        self.m_lib_capture = libcapture
    
    def start_audio_capture(self,hchannel,callback):
        self.m_h_channel = hchannel
        self.m_callbcak = callback
        self.m_b_running = True
        self.m_h_event_exit = win32event.CreateEvent(None,False,False,None)
        self.start()

    def stop_audio_capture(self):
        self.m_b_running = False
        if self.m_h_event_exit != 0:
            win32event.SetEvent(self.m_h_event_exit)
        self.wait()
        if self.m_h_event_exit != 0:
            win32api.CloseHandle(int(self.m_h_event_exit))
            self.m_h_event_exit = 0

    def run(self):
        t_h_event_audio = win32event.CreateEvent(None,False,False,None)
        t_h_notify_audio = 0
        t_ret = MW_SUCCEEDED
        t_b_done = False
        t_audio_frame = mwcap_audio_capture_frame()
        t_n_buf_size = MWCAP_AUDIO_SAMPLES_PER_FRAME*2*sizeof(c_int16)*4
        t_n_buf_pos = 0
        t_buffer = create_string_buffer(t_n_buf_size)
        while t_b_done == False:
            t_ret = self.m_lib_capture.mw_start_audio_capture(self.m_h_channel)
            if t_ret != MW_SUCCEEDED:
                break
            t_h_notify_audio = self.m_lib_capture.mw_register_notify(
                self.m_h_channel,
                t_h_event_audio,
                MWCAP_NOTIFY_AUDIO_SIGNAL_CHANGE|MWCAP_NOTIFY_AUDIO_FRAME_BUFFERED
            )
            if t_h_notify_audio == 0:
                break
            t_ll_begin = mw_device_time()
            t_ret = self.m_lib_capture.mw_get_device_time(self.m_h_channel,t_ll_begin)
            if t_ret != MW_SUCCEEDED:
                break
            t_dw_sample_count = 0
            t_ll_last = mw_device_time()
            t_ll_last.m_ll_device_time = t_ll_begin.m_ll_device_time
            t_ll_current = mw_device_time()
            while self.m_b_running == True:
                t_array_event_notify = [self.m_h_event_exit,t_h_event_audio]
                t_events = tuple(t_array_event_notify)
                t_wait_ret = win32event.WaitForMultipleObjects(t_events,False,win32event.INFINITE)
                if t_wait_ret == win32event.WAIT_OBJECT_0 + 0:
                    break
                elif t_wait_ret == win32event.WAIT_OBJECT_0 + 1:
                    t_ull_notify_status = mw_notify_status()
                    t_ret = self.m_lib_capture.mw_get_notify_status(
                        self.m_h_channel,
                        t_h_notify_audio,
                        t_ull_notify_status
                    ) 
                    if t_ull_notify_status.m_ll_notify_status& MWCAP_NOTIFY_AUDIO_SIGNAL_CHANGE != 0:
                        t_audio_signal_status = mw_audio_signal_status()
                        t_ret = self.m_lib_capture.mw_get_audio_signal_status(
                            self.m_h_channel,
                            t_audio_signal_status
                        )
                        print('audio signal change')
                    if t_ull_notify_status.m_ll_notify_status& MWCAP_NOTIFY_AUDIO_FRAME_BUFFERED != 0:
                        while t_ret == MW_SUCCEEDED and self.m_b_running == True:
                            t_ret = self.m_lib_capture.mw_capture_audio_frame(self.m_h_channel,t_audio_frame)
                            if t_ret == MW_SUCCEEDED:
                                if self.m_callbcak != 0:
                                    for i in range(MWCAP_AUDIO_SAMPLES_PER_FRAME):
                                        t_pos_0 = i*8*4
                                        t_pos_1 = i*8*4+4*4
                                        t_buffer[t_n_buf_pos + 0] = t_audio_frame.adwSamples[t_pos_0+2]
                                        t_buffer[t_n_buf_pos + 1] = t_audio_frame.adwSamples[t_pos_0+3]
                                        t_buffer[t_n_buf_pos + 2] = t_audio_frame.adwSamples[t_pos_1+2]
                                        t_buffer[t_n_buf_pos + 3] = t_audio_frame.adwSamples[t_pos_1+3]
                                        t_n_buf_pos+=4
                                    self.m_lib_capture.mw_get_device_time(self.m_h_channel,t_ll_current)
                                    if t_n_buf_pos == t_n_buf_size:
                                        self.m_callbcak(addressof(t_buffer),t_n_buf_size,t_ll_current.m_ll_device_time.value)
                                        t_n_buf_pos = 0
                                t_dw_sample_count += MWCAP_AUDIO_SAMPLES_PER_FRAME
                                if t_dw_sample_count >= 48000:
                                    self.m_samples_per_sec = t_dw_sample_count*10000000/(t_ll_current.m_ll_device_time.value - t_ll_last.m_ll_device_time.value)
                                    t_dw_sample_count = 0
                                    t_ll_last.m_ll_device_time = t_ll_current.m_ll_device_time
            
            t_ret = self.m_lib_capture.mw_unregister_notify(self.m_h_channel,t_h_notify_audio)
            t_ret = self.m_lib_capture.mw_stop_audio_capture(self.m_h_channel)
            t_b_done = True
        win32api.CloseHandle(t_h_event_audio)

CLIP_NONE = 0
CLIP_TOPLEFT = 1
CLIP_TOPRIGHT = 2
CLIP_BOTTOMLEFT = 3
CLIP_BOTTOMRIGHT = 4

class CAVCapture(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.m_lib_capture = mw_capture()
        self.m_lib_capture.mw_capture_init_instance()
        self.m_b_video_valid = False
        self.m_b_audio_valid = False
        self.m_h_video_thread = CVideoCaptureThread(self)
        self.m_h_video_thread.set_capture_lib(self.m_lib_capture)
        self.m_h_audio_thread = CAudioCaptureThread(self)
        self.m_h_audio_thread.set_capture_lib(self.m_lib_capture)
        self.m_h_channel = 0
        self.m_d_fps = 0
        self.m_d_samplespersec = 0
        self.avcallback = 0
        self.m_ll_videoframe = 0
        self.m_ll_audioframe = 0
        self.m_b_running = False
        self.m_n_clip = CLIP_NONE
        self.m_valid_index = []
        self.m_dev_name = []
        self.m_cx = 1920
        self.m_cy = 1080
        self.m_color_fmt = MWCAP_VIDEO_COLOR_FORMAT_UNKNOWN
        self.m_quant_rng = MWCAP_VIDEO_QUANTIZATION_UNKNOWN
        self.m_frame_dur = 166667
        self.m_b_lpcm = True
        self.m_bits_per_sample = 16
        self.m_sample_rate = 48000
        self.m_vcallback = 0
        self.m_acallback = 0
        self.m_caller = 0
        self.m_n_clip = CLIP_NONE
        self.m_fourcc = MWFOURCC_YUY2

    def enum_device(self):
        self.m_lib_capture.mw_refresh_device()
        t_n_num = self.m_lib_capture.mw_get_channel_count()
        self.m_valid_index.clear()
        if t_n_num <= 0:
            return
        t_ret = MW_SUCCEEDED
        t_channel_info = mw_cap_channel_info()
        for i in range(t_n_num):
            t_ret = self.m_lib_capture.mw_get_channel_info_by_index(i,t_channel_info)
            if t_ret != MW_SUCCEEDED:
                continue
            if t_channel_info.wFamilyID == MW_FAMILY_ID_USB_CAPTURE:
                continue
            self.m_valid_index.append(i)
            t_cs_name = '%d-%d %s' % (t_channel_info.byBoardIndex,t_channel_info.byChannelIndex,str(t_channel_info.szProductName,encoding='utf-8'))
            self.m_dev_name.append(t_cs_name)

    def get_dev_name(self):
        return self.m_dev_name

    def set_video_clip(self,clip):
        self.m_n_clip = clip
        self.m_h_video_thread.set_video_clip(self.m_n_clip)

    def create(self,
        colorfmt,
        quantrange,
        nindex,
        cx,
        cy,
        fourcc,
        frameduration,
        acallback,
        vcallback,
        bcaptureaudio,
        caller,
        clip):
        self.m_lib_capture = mw_capture()
        t_path = create_unicode_buffer(128)
        self.m_lib_capture.mw_get_device_path(self.m_valid_index[nindex],t_path)
        self.m_acallback = acallback
        self.m_vcallback = vcallback
        self.m_caller = caller
        t_b_done = False
        while t_b_done == False:
            self.m_h_channel = self.m_lib_capture.mw_open_channel_by_path(t_path)
            if self.m_h_channel == 0:
                break
            t_video_signal_status = mw_video_signal_status()
            t_ret = self.m_lib_capture.mw_get_video_signal_status(self.m_h_channel,t_video_signal_status)
            if t_ret != MW_SUCCEEDED:
                break
            t_audio_signal_status = mw_audio_signal_status()
            t_ret = self.m_lib_capture.mw_get_audio_signal_status(self.m_h_channel,t_audio_signal_status)
            if t_ret != MW_SUCCEEDED:
                break
            self.m_b_video_valid = (t_video_signal_status.state == MWCAP_VIDEO_SIGNAL_LOCKED)
            if self.m_b_video_valid == True:
                self.m_cx = t_video_signal_status.cx
                self.m_cy = t_video_signal_status.cy
                self.m_color_fmt = t_video_signal_status.colorFormat
                self.m_quant_rng = t_video_signal_status.quantRange
                self.m_frame_dur = t_video_signal_status.dwFrameDuration
            else:
                t_video_caps = mw_video_caps()
                t_ret = self.m_lib_capture.mw_get_video_caps(self.m_h_channel,t_video_caps)
                self.m_cx = t_video_caps.wMaxOutputWidth if (cx>t_video_caps.wMaxOutputWidth) else cx
                self.m_cy = t_video_caps.wMaxOutputHeight if (cy>t_video_caps.wMaxOutputHeight) else cy
                self.m_color_fmt = colorfmt
                self.m_quant_rng = quantrange
                self.m_frame_dur = frameduration
            self.m_b_audio_valid = True if (t_audio_signal_status.wChannelValid!=0) else False
            self.m_b_lpcm = t_audio_signal_status.bLPCM
            self.m_bits_per_sample = t_audio_signal_status.cBitsPerSample
            self.m_sample_rate = t_audio_signal_status.dwSampleRate
            self.m_n_clip = clip
            self.m_fourcc = fourcc
            self.m_h_video_thread.start_video_capture(
                self.m_color_fmt,
                self.m_quant_rng,
                self.m_h_channel,
                self.m_cx,
                self.m_cy,
                self.m_fourcc,
                self.m_frame_dur,
                self.m_vcallback,
                self.m_caller,
                self.m_n_clip
            )
            if bcaptureaudio == True:
                self.m_h_audio_thread.start_audio_capture(self.m_h_channel,self.m_acallback)
            t_b_done = True

        return t_b_done

    def destroy(self):
        self.m_h_video_thread.stop_video_capture()
        self.m_h_audio_thread.stop_audio_capture()
            
        

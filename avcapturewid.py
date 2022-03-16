from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtWidgets import QMenuBar,QMenu,QAction,QLabel,QStatusBar,QMessageBox,QFileDialog
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtCore import QByteArray,QTimer
from OpenGL.arrays import *
from videorender import *
from audiorender import *
from mwcapture.libmwcapture import *
from capture import *
from mp4filesave import *
# from test_pyav import *
#import pyaudio

class CAVCaptureWid(QtWidgets.QMainWindow):
    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.m_n_ui_select = 0
        self.m_n_capture_index = -1
        self.m_n_cx = 1920
        self.m_n_cy = 1080
        #self.m_fourcc = MWFOURCC_YUY2
        self.m_fourcc = MWFOURCC_NV12
        self.m_frameduration = 166667
        self.m_n_channels = 2
        self.m_n_samplerate = 48000
        self.m_n_bitspersample = 16
        self.m_n_clip = CLIP_NONE
        self.m_dev_name = []
        self.m_capture = CAVCapture()
        self.m_capture.enum_device()
        #self.m_pyaudio = pyaudio.PyAudio()
        self.m_audio_render = CAudioRender(self)
        #self.m_stream = 0
        #self.m_video_callback = mw_video_capture_callback(video_capture_callback)
        #self.m_audio_callback = mw_audio_capture_callback(audio_capture_callback)
        self.m_ptr = py_object(self)
        self.m_mp4_writer = CMWMp4Save()
        self.m_venc_thread = CVenThread()
        self.m_b_record = False
        self.m_timer = QTimer(self)
        self.m_timer.timeout.connect(self.slot_on_timer)
        self.m_timer.start(200)
        self.init_ui()
        
        
    def __del__(self):
        pass

    def init_ui(self):
        self.setWindowTitle('AVCapture')
        self.resize(600,400)
        self.m_video_render = CRenderWid(self)
        self.m_video_render.move(0,0)
        self.m_n_status_bar_height = 20
        self.m_video_render.resize(self.width(),self.height() - self.m_n_status_bar_height)
        self.m_menubar = self.menuBar()
        self.m_statusbar = self.statusBar()
        self.m_menu_file = QMenu('File',self.m_menubar)
        self.m_menubar.addMenu(self.m_menu_file)
        self.m_menu_file_act = []
        self.m_ac_start_record = QAction('Start Record',self.m_menu_file)
        self.m_ac_start_record.setEnabled(False)
        self.m_menu_file.addAction(self.m_ac_start_record)
        self.m_menu_file_act.append(self.m_ac_start_record)
        self.m_ac_stop_record = QAction('Stop Record',self.m_menu_file)
        self.m_ac_stop_record.setEnabled(False)
        self.m_menu_file.addAction(self.m_ac_stop_record)
        self.m_menu_file_act.append(self.m_ac_stop_record)
        self.m_menu_file.addSeparator()
        self.m_ac_clip_none = QAction('No Clip',self.m_menu_file)
        self.m_ac_clip_none.setEnabled(True)
        self.m_ac_clip_none.setCheckable(True)
        self.m_ac_clip_none.setChecked(True)
        self.m_menu_file.addAction(self.m_ac_clip_none)
        self.m_menu_file_act.append(self.m_ac_clip_none)
        self.m_ac_clip_tl = QAction('Top-Left',self.m_menu_file)
        self.m_ac_clip_tl.setEnabled(True)
        self.m_ac_clip_tl.setCheckable(True)
        self.m_ac_clip_tl.setChecked(False)
        self.m_menu_file.addAction(self.m_ac_clip_tl)
        self.m_menu_file_act.append(self.m_ac_clip_tl)
        self.m_ac_clip_tr = QAction('Top-Right',self.m_menu_file)
        self.m_ac_clip_tr.setEnabled(True)
        self.m_ac_clip_tr.setCheckable(True)
        self.m_ac_clip_tr.setChecked(False)
        self.m_menu_file.addAction(self.m_ac_clip_tr)
        self.m_menu_file_act.append(self.m_ac_clip_tr)
        self.m_ac_clip_bl = QAction('Bottom-Left',self.m_menu_file)
        self.m_ac_clip_bl.setEnabled(True)
        self.m_ac_clip_bl.setCheckable(True)
        self.m_ac_clip_bl.setChecked(False)
        self.m_menu_file.addAction(self.m_ac_clip_bl)
        self.m_menu_file_act.append(self.m_ac_clip_bl)
        self.m_ac_clip_br = QAction('Bottom-Right',self.m_menu_file)
        self.m_ac_clip_br.setEnabled(True)
        self.m_ac_clip_br.setCheckable(True)
        self.m_ac_clip_br.setChecked(False)
        self.m_menu_file.addAction(self.m_ac_clip_br)
        self.m_menu_file_act.append(self.m_ac_clip_br)
        self.m_ac_sel_clip = self.m_ac_clip_none
        self.m_n_clip = CLIP_NONE
        self.m_menu_file.addSeparator()
        self.m_ac_exit = QAction('Exit',self.m_menu_file)
        self.m_ac_exit.setEnabled(True)
        self.m_menu_file.addAction(self.m_ac_exit)
        self.m_menu_file_act.append(self.m_ac_exit)
        self.m_menu_file.triggered.connect(self.slot_file_selected)
        self.m_menu_device = QMenu('Device',self.m_menubar)
        t_action = QAction('None')
        self.m_menu_device.addAction(t_action)
        self.m_menu_device_act = []
        self.m_menu_device_act.append(t_action)
        self.m_menubar.addMenu(self.m_menu_device)
        t_action.setCheckable(True)
        t_action.setChecked(True)
        self.m_menu_device.triggered.connect(self.slot_device_selected)
        t_dev_name = self.m_capture.get_dev_name()
        for t_name in t_dev_name:
            t_action = QAction(t_name)
            self.m_menu_device_act.append(t_action)
            self.m_menu_device.addAction(t_action)
            t_action.setCheckable(True)
        self.m_menu_view = QMenu('View',self.m_menubar)
        self.m_ac_status = QAction('Status Bar',self.m_menu_view)
        self.m_menu_view.addAction(self.m_ac_status)
        self.m_ac_status.setEnabled(True)
        self.m_ac_status.setCheckable(True)
        self.m_ac_status.setChecked(True)
        self.m_b_status_bar = True
        self.m_menubar.addMenu(self.m_menu_view)
        self.m_ac_status.triggered.connect(self.slot_on_view)
        self.m_menu_help = QMenu('Help',self.m_menubar)
        self.m_ac_help = QAction('About AVCapture ...')
        self.m_menu_help.addAction(self.m_ac_help)
        self.m_ac_help.setEnabled(True)
        self.m_ac_help.triggered.connect(self.slot_on_help)
        self.m_menubar.addMenu(self.m_menu_help)

    def resizeEvent(self, event):
        if self.m_b_status_bar == True:
            self.m_video_render.resize(self.width(),self.height()-self.m_n_status_bar_height)
        else:
            self.m_video_render.resize(self.width(),self.height())
        pass

    def closeEvent(self,event):
        self.m_capture.destroy()
        self.m_audio_render.close_audio_render()

    def slot_file_selected(self,action):
        if action == self.m_ac_start_record:
            t_filename,t_filetype = QFileDialog.getSaveFileName(self, "Save File","avcapturepy","MP4 (*.mp4)");
            if t_filename=='':
                return
            t_ret = self.m_mp4_writer.create_mp4(
                t_filename,
                self.m_n_cx,
                self.m_n_cy,
                self.m_frameduration,
                self.m_n_channels,
                self.m_n_samplerate,
                self.m_n_bitspersample,
                64000)
            if t_ret != 0:
                return
            self.m_b_record = True
            self.m_venc_thread.start_enc(self.m_mp4_writer)
            self.m_menu_device.setEnabled(False)
            self.m_ac_start_record.setEnabled(False)
            self.m_ac_stop_record.setEnabled(True)
            return
        if action == self.m_ac_stop_record:
            self.m_b_record = False
            self.m_venc_thread.stop_enc()
            self.m_mp4_writer.destory_mp4()
            self.m_menu_device.setEnabled(True)
            self.m_ac_start_record.setEnabled(True)
            self.m_ac_stop_record.setEnabled(False)
            return
        if action == self.m_ac_clip_none:
            if action == self.m_ac_sel_clip:
                self.m_ac_sel_clip.setChecked(True)
                return
            self.m_n_clip = CLIP_NONE
            self.m_ac_sel_clip.setChecked(False)
            self.m_ac_sel_clip = action
            self.m_capture.set_video_clip(self.m_n_clip)
        if action == self.m_ac_clip_tl:
            if action == self.m_ac_sel_clip:
                self.m_ac_sel_clip.setChecked(True)
                return
            self.m_n_clip = CLIP_TOPLEFT
            self.m_ac_sel_clip.setChecked(False)
            self.m_ac_sel_clip = action
            self.m_capture.set_video_clip(self.m_n_clip)
        if action == self.m_ac_clip_tr:
            if action == self.m_ac_sel_clip:
                self.m_ac_sel_clip.setChecked(True)
                return
            self.m_n_clip = CLIP_TOPRIGHT
            self.m_ac_sel_clip.setChecked(False)
            self.m_ac_sel_clip = action
            self.m_capture.set_video_clip(self.m_n_clip)
        if action == self.m_ac_clip_bl:
            if action == self.m_ac_sel_clip:
                self.m_ac_sel_clip.setChecked(True)
                return
            self.m_n_clip = CLIP_BOTTOMLEFT
            self.m_ac_sel_clip.setChecked(False)
            self.m_capture.set_video_clip(self.m_n_clip)
            self.m_ac_sel_clip = action
        if action == self.m_ac_clip_br:
            if action == self.m_ac_sel_clip:
                self.m_ac_sel_clip.setChecked(True)
                return
            self.m_n_clip = CLIP_BOTTOMRIGHT
            self.m_ac_sel_clip.setChecked(False)
            self.m_ac_sel_clip = action
            self.m_capture.set_video_clip(self.m_n_clip)
        if action == self.m_ac_exit:
            self.close()

    def slot_device_selected(self,action):
        t_n_index = 0
        t_select_index = 0
        for t_action in self.m_menu_device_act:
            if action == t_action:
                t_select_index = t_n_index
            else:
                if t_action.isChecked():
                    t_action.setChecked(False)
            t_n_index +=1
        if t_select_index == self.m_n_ui_select:
            action.setChecked(True)
            return
        if self.m_n_ui_select != 0:
            self.m_capture.destroy()
            self.m_audio_render.close_audio_render()
            self.m_n_capture_index = -1
            self.m_ac_start_record.setEnabled(False)
            self.m_ac_stop_record.setEnabled(False)
        if t_select_index == 0:
            self.m_n_ui_select = 0
            self.m_video_render.set_black()
            return
        t_n_capture_index = t_select_index - 1
        self.m_video_render.open_render(self.m_fourcc,self.m_n_cx,self.m_n_cy)
        self.m_audio_render.open_audio_render(2,16,48000)
        t_b_ret = self.m_capture.create(
            MWCAP_VIDEO_COLOR_FORMAT_YUV601,
            MWCAP_VIDEO_QUANTIZATION_FULL,
            t_n_capture_index,
            self.m_n_cx,
            self.m_n_cy,
            self.m_fourcc,
            166667,
            self.audio_callback,
            self.video_callback,
            True,
            self,
            self.m_n_clip)
        if t_b_ret == False:
            self.m_n_capture_index = -1
            self.m_menu_device_act[0].setChecked(True)
            action.setChecked(False)
            self.m_n_ui_select = 0
        else:
            self.m_n_ui_select = t_select_index
            self.m_ac_start_record.setEnabled(True)
    
    def slot_on_view(self,checked):
        self.m_b_status_bar = checked
        if self.m_b_status_bar == True:
            self.m_video_render.resize(self.width(),self.height()-self.m_n_status_bar_height)
        else:
            self.m_video_render.resize(self.width(),self.height())

    def slot_on_help(self): 
        QMessageBox.information(self,'About AVCapture','AVCapture,Vresion1.0\nCopyright(C) 2011-2020,Nanjing Magewell Electronics Co., Ltd.\nAll rights reserved.')

    def slot_on_timer(self):
        if self.m_b_status_bar == True:
            str = '%dx%d NV12 %.2ffps' %(self.m_capture.m_cx,self.m_capture.m_cy,self.m_capture.m_h_video_thread.m_d_fps)
            self.m_statusbar.showMessage(str)

    def paintEvent(self,event):
        pass

    def print_channel_info(self,t_channel_info):
         print('family id:%d\n'
               'product id:%d\n'
               'hardware ver:%s\n'
               'firmware id:%d\n'
               'firmware ver:%d\n'
               'driver ver:%d\n'
               'family name:%s\n'
               'product name:%s\n'
               'firmware ver:%s\n'
               'sn:%s\n'
               'board index:%d\n'
               'channel index:%d\n' %(
                t_channel_info.wFamilyID,
                t_channel_info.wProductID,
                t_channel_info.chHardwareVersion,
                t_channel_info.byFirmwareID,
                t_channel_info.dwFirmwareVersion,
                t_channel_info.dwDriverVersion,
                t_channel_info.szFamilyName,
                t_channel_info.szProductName,
                t_channel_info.szFirmwareName,
                t_channel_info.szBoardSerialNo,
                t_channel_info.byBoardIndex,
                t_channel_info.byChannelIndex
                ))
    
    def video_callback(self,pbframe,cbsize,u64timestamp):
        if cbsize > 0:
            t_str_buf = string_at(pbframe,cbsize)
            t_bytes = bytes(t_str_buf)
            self.m_video_render.put_frame(t_bytes)
            if self.m_b_record:
                self.m_venc_thread.put_video_frame(pbframe, cbsize, u64timestamp)
    

    def audio_callback(self,pbframe,cbsize,u64timestamp):
        if cbsize >0:
            t_str_buf = string_at(pbframe,cbsize)
            t_bytes = bytes(t_str_buf)
            self.m_audio_render.write_frame(t_bytes)
            if self.m_b_record:
                self.m_venc_thread.put_audio_frame(pbframe,cbsize,u64timestamp)
from PyQt5.QtMultimedia import QAudioDeviceInfo,QAudioOutput,QAudioFormat
from PyQt5.QtCore import QIODevice,QObject

class CAudioRender(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.m_audio_output = 0
        self.m_audio_fmt = 0
        self.m_io_device = 0

    def open_audio_render(self,channels,bits,samples):
        self.m_audio_fmt = QAudioFormat()
        self.m_audio_fmt.setChannelCount(2)
        self.m_audio_fmt.setSampleRate(48000)
        self.m_audio_fmt.setSampleSize(16)
        self.m_audio_fmt.setCodec("audio/pcm")
        self.m_audio_fmt.setByteOrder(QAudioFormat.LittleEndian)
        self.m_audio_fmt.setSampleType(QAudioFormat.UnSignedInt)
        self.m_audio_output = QAudioOutput(self.m_audio_fmt,self)
        self.m_io_device = self.m_audio_output.start()

    def close_audio_render(self):
        if self.m_io_device != 0:
            self.m_audio_output.stop()
            self.m_io_device = 0

    def write_frame(self,pbframe):
        self.m_io_device.write(pbframe)
import sys
from PyQt5 import QtWidgets
from avcapturewid import CAVCaptureWid

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = CAVCaptureWid()
    win.show()
    res = app.exec_()
    win.m_video_render.abolish_render()
    sys.exit(res)

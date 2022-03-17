""" This file was translated from the cpp example CaptureByInput.cpp"""
import time

from pymagewell.device import Device
from pymagewell.frame_grabber import FrameGrabber
from pymagewell.settings import VideoSettings

if __name__ == '__main__':

    device = Device()
    settings = VideoSettings()
    grabber = FrameGrabber(device, settings)

    frames = []
    for i in range(5):
        frames.append(grabber.wait_and_grab())
    grabber.shutdown()

    for frame in frames:
        print(f"Frame timestamp {frame.timestamp}")
        frame.as_image().show()

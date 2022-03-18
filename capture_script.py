import time

from cv2 import imshow, waitKey

from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.frame_grabber import FrameGrabber
from pymagewell.settings import VideoSettings, GrabMode

if __name__ == '__main__':

    settings = VideoSettings()
    settings.grab_mode = GrabMode.LOW_LATENCY

    device = ProCaptureDevice(settings.grab_mode)
    grabber = FrameGrabber(device, settings)

    print('PRESS Q TO QUIT!')

    while True:
        frame = grabber.wait_and_grab()
        t = time.perf_counter()
        imshow("video", frame.as_array())
        if waitKey(1) & 0xFF == ord('q'):
            break
        print(f"Frame took {time.perf_counter() - t} seconds to display on screen.")
    grabber.shutdown()

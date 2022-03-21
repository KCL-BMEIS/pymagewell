import time

from cv2 import imshow, waitKey

from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.pro_capture_controller import ProCaptureController
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, TransferMode

if __name__ == '__main__':

    video_settings = ProCaptureSettings()
    device = ProCaptureDevice(TransferMode.LOW_LATENCY)
    grabber = ProCaptureController(device, video_settings)

    print('PRESS Q TO QUIT!')

    while True:
        frame = grabber.transfer_when_ready()
        t = time.perf_counter()
        imshow("video", frame.as_array())
        if waitKey(1) & 0xFF == ord('q'):
            break
        print(f"Frame took {time.perf_counter() - t} seconds to display on screen.")
    grabber.shutdown()

import time

from cv2 import imshow, waitKey

from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.pro_capture_controller import ProCaptureController
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, TransferMode

if __name__ == '__main__':

    device_settings = ProCaptureSettings()
    device_settings.transfer_mode = TransferMode.LOW_LATENCY
    device = ProCaptureDevice(device_settings)
    frame_grabber = ProCaptureController(device)

    print('PRESS Q TO QUIT!')

    while True:
        frame = frame_grabber.transfer_when_ready()
        t = time.perf_counter()
        imshow("video", frame.as_array())
        if waitKey(1) & 0xFF == ord('q'):
            break
        # print(f"Frame took {time.perf_counter() - t} seconds to display on screen.")
        # print(frame.timestamp)
    frame_grabber.shutdown()

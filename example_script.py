import time
from datetime import timedelta
from typing import cast

from cv2 import imshow, waitKey
from numpy import array, diff

import versioneer
from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.pro_capture_controller import ProCaptureController
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, TransferMode
from pymagewell.pro_capture_device.mock_pro_capture_device import MockProCaptureDevice

if __name__ == '__main__':

    device_settings = ProCaptureSettings()
    device_settings.transfer_mode = TransferMode.LOW_LATENCY
    device = ProCaptureDevice(device_settings)
    controller = ProCaptureController(device)

    print(f'pymagewell version {versioneer.get_version()}')
    print('PRESS Q TO QUIT!')

    counter = 0
    timestamps = []
    while True:
        frame = controller.transfer_when_ready()
        timestamps.append(frame.timestamp)
        imshow("video", frame.as_array())
        if waitKey(1) & 0xFF == ord('q'):
            break
        if counter % 20 == 19:
            mean_period = array([p.total_seconds() for p in diff(array(timestamps))]).mean()
            print(f'Average frame rate over last 20 frames: {1 / mean_period} Hz')
            print(f'Last frame timestamp: {frame.timestamp}')
        counter += 1
    controller.shutdown()

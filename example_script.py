from cv2 import imshow, waitKey
from numpy import array, diff

import versioneer
from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.pro_capture_controller import ProCaptureController
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, TransferMode
from pymagewell.pro_capture_device.mock_pro_capture_device import MockProCaptureDevice

MOCK_MODE = True

if __name__ == '__main__':

    device_settings = ProCaptureSettings()
    device_settings.transfer_mode = TransferMode.TIMER
    if MOCK_MODE:
        device = MockProCaptureDevice(device_settings)
    else:
        device = ProCaptureDevice(device_settings)
    controller = ProCaptureController(device)

    print(f'pymagewell version {versioneer.get_version()}')
    print('PRESS Q TO QUIT!')

    counter = 0
    timestamps = []
    while True:
        frame = controller.transfer_when_ready()
        timestamps.append(frame.timestamps)
        imshow("video", frame.as_array())
        if waitKey(1) & 0xFF == ord('q'):
            break
        if counter % 20 == 19:
            transfer_complete_timestamps = array([t.transfer_complete for t in timestamps])
            mean_period = array([p.total_seconds() for p in diff(transfer_complete_timestamps)]).mean()
            print(f'Average frame rate over last 20 frames: {1 / mean_period} Hz')

            buffering_started_timestamps = array([t.buffering_started for t in timestamps])
            mean_latency = (transfer_complete_timestamps - buffering_started_timestamps).mean().total_seconds()
            print(f'Average frame acquisition latency over last 20 frames: {mean_latency * 1e3} ms')

        counter += 1
    controller.shutdown()

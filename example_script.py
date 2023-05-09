from cv2 import imshow, waitKey
from numpy import array, diff

from pymagewell import ProCaptureDevice, ProCaptureController, ProCaptureSettings, TransferMode, MockProCaptureDevice, \
    ImageSizeInPixels, ColourFormat
from pymagewell.conversion import convert_interleaved_yuv_to_rgb, convert_rgb10_to_array, convert_rgb16_to_array

MOCK_MODE = True

if __name__ == '__main__':

    # Configure the device
    device_settings = ProCaptureSettings(
        dimensions=ImageSizeInPixels(1920, 1080),
        color_format=ColourFormat.RGB10,
        transfer_mode=TransferMode.TIMER
    )

    # Create a device object
    if MOCK_MODE:
        device = MockProCaptureDevice(device_settings)
    else:
        device = ProCaptureDevice(device_settings)

    # Create a controller to start the device
    controller = ProCaptureController(device)

    print('PRESS Q TO QUIT!')
    counter = 0
    timestamps = []
    while True:
        # Use the controller to transfer frames from the device to the PC when they are ready.
        # This will block until a frame is ready or ‘timeout_ms’ is reached.
        frame = controller.transfer_when_ready(timeout_ms=1000)
        timestamps.append(frame.timestamps)

        # Here we are using OpenCV to display the acquired frames (flip channels because openCV expects BGR)

        frame_array = convert_rgb10_to_array(frame.string_buffer, frame.dimensions)
        imshow("video", frame_array)
        # imshow("video", frame.as_array())  # [:, :, ::-1])
        if waitKey(1) & 0xFF == ord('q'):
            break

        # Every 60 frames, print some timing information
        if counter % 60 == 59:
            transfer_complete_timestamps = array([t.transfer_complete for t in timestamps])
            mean_period = array([p.total_seconds() for p in diff(transfer_complete_timestamps)]).mean()
            print(f'Average frame rate over last 20 frames: {1 / mean_period} Hz')

            buffering_started_timestamps = array([t.buffering_started for t in timestamps])
            mean_latency = (transfer_complete_timestamps - buffering_started_timestamps).mean().total_seconds()
            print(f'Average frame acquisition latency over last 20 frames: {mean_latency * 1e3} ms')

        counter += 1

    # Stop transfer and grabbing
    controller.shutdown()

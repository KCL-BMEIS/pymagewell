from pymagewell.device import Device
from pymagewell.frame_grabber import FrameGrabber
from pymagewell.settings import VideoSettings, GrabMode

if __name__ == '__main__':

    device = Device()
    settings = VideoSettings()
    settings.grab_mode = GrabMode.LOW_LATENCY
    grabber = FrameGrabber(device, settings)

    frames = []
    for i in range(5):
        frames.append(grabber.wait_and_grab())
    grabber.shutdown()

    for frame in frames:
        print(f"Frame timestamp {frame.timestamp}")
        frame.as_image().show()

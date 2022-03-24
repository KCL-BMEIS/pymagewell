# pymagewell
Python library for interfacing with Magewell ProCapture frame grabbers

### Example of use
First, create a `ProCaptureSettings` dataclass:
```python
from pymagewell.pro_capture_device.device_settings import (
    ProCaptureSettings, ImageSizeInPixels, TransferMode, ColourFormat
)

device_settings = ProCaptureSettings(
    dimensions=ImageSizeInPixels(1920, 1080),
    color_format=ColourFormat.BGR24,  # Color format of captured video frames
    transfer_mode = TransferMode.LOW_LATENCY,
    num_lines_per_chunk = 64  # has effect only in low latency mode
)
```
Then create a `ProCaptureDevice` (or `MockProCaptureDevice` for testing on a system without a grabber) configured with
your chosen settings:
```python
from pymagewell.pro_capture_device import ProCaptureDevice

device = ProCaptureDevice(settings=device_settings)
```
Then create a `ProCaptureDeviceController` to transfer frames from the device to your PC:
```python
from pymagewell.pro_capture_controller import ProCaptureController

controller = ProCaptureController(device)
```
Then you can grab frames in a loop using the `transfer_when_ready()` method, which will wait until a frame has been 
acquired by the device, transfer it from the device to the PC, and return it as a `VideoFrame` object. 
```python
while True:
    frame = controller.transfer_when_ready()
```
`VideoFrame` provides access to the pixels as Pillow image with its `as_pillow_image()` method, or a Numpy array with
its `as_numpy_array` method. It also provides access to a Timestamp generated when the frame was ready for transfer from
the card to the PC.

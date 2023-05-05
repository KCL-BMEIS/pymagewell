# pymagewell
`pymagewell` is a Python library for interfacing with Magewell ProCapture frame grabbers.

It is based on (and includes) Magewell's Windows SDK and is therefore Windows only. However, it provides a mock class
that for testing and development that does not depend on the SDK's Windows .dll files, so `pymagwell` can also be 
installed on macOS and Linux.

* [GitHub page](https://github.com/KCL-BMEIS/pymagewell)
* [API reference documentation](https://kcl-bmeis.github.io/pymagewell/)
* [PyPI page](https://pypi.org/project/pymagewell/)

### Installation

From PyPI:
```bash
pip install pymagewell
```
From conda-forge (Windows and macOS only):
```bash
conda install -c conda-forge pymagewell
```

### Example of use

A full working example is provided in
[`example_script.py`](https://github.com/KCL-BMEIS/pymagewell/blob/main/example_script.py).

First, create a `ProCaptureSettings` dataclass:

```python
from src.pymagewell import (
    ProCaptureSettings, ImageSizeInPixels, TransferMode, ColourFormat
)

device_settings = ProCaptureSettings(
    dimensions=ImageSizeInPixels(1920, 1080),
    color_format=ColourFormat.BGR24,  # Color format of captured video frames
    transfer_mode=TransferMode.LOW_LATENCY,
    num_lines_per_chunk=64  # has effect only in low latency mode
)
```
Then create a `ProCaptureDevice` (or `MockProCaptureDevice` for testing on a system without a grabber) configured with
your chosen settings:

```python
from src.pymagewell import ProCaptureDevice

device = ProCaptureDevice(settings=device_settings)
```
Then create a `ProCaptureDeviceController` to transfer frames from the device to your PC:

```python
from src.pymagewell import ProCaptureController

controller = ProCaptureController(device)
```
Then you can grab frames in a loop using the `transfer_when_ready()` method, which will wait until a frame has been 
acquired by the device, transfer it from the device to the PC, and return it as a `VideoFrame` object. This is a 
blocking call.
```python
while True:
    frame = controller.transfer_when_ready()
```
`VideoFrame` provides access to the pixels as Pillow image with its `as_pillow_image()` method, or a Numpy array with
its `as_numpy_array` method. It also provides access to timestamps (datetime.datetime) describing the frame acquisition 
process:
```python
t1 = frame.timestamps.buffering_started  # time at which frame started being written to the hardware buffer
buffer
t2 = frame.timestamps.buffering_complete  # time at which frame was completely written to the hardware buffer
t3 = frame.timestamps.transfer_started  # time at which the software started transferring the frame to PC memory
t4 = frame.timestamps.transfer_complete  # time by which the whole frame had arrived in PC memory
```
In TIMER and NORMAL transfer modes, transfer starts after the full frame has been written to hardware buffer. In 
LOW_LATENCY transfer mode, transfer starts while the frame is still being written to hardware memory. This will be 
reflected in the timestamps.

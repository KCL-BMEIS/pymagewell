# Christian Baker, King's College London
# Copyright (c) 2022 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
"""
`pymagewell` is a Python library for interfacing with Magewell ProCapture frame grabbers.

It is based on (and includes) Magewell's Windows SDK and is therefore Windows only. However, it provides a mock class
that for testing and development that does not depend on the SDK's Windows .dll files, so `pymagwell` can also be
installed on macOS and Linux.

* [GitHub page](https://github.com/KCL-BMEIS/pymagewell)
* [API reference documentation](https://kcl-bmeis.github.io/pymagewell/)
* [PyPI page](https://pypi.org/project/pymagewell/)

### Installation

```bash
pip install pymagewell
```

### Example of use

A full working example is provided in
[`example_script.py`](https://github.com/KCL-BMEIS/pymagewell/blob/main/example_script.py).

"""
from . import _version
from .pro_capture_controller import ProCaptureController

from .pro_capture_device import ProCaptureDevice
from .pro_capture_device.device_settings import ProCaptureSettings, TransferMode, ImageSizeInPixels, ColourFormat
from .pro_capture_device.mock_pro_capture_device import MockProCaptureDevice

__version__ = _version.get_versions()["version"]  # type: ignore

__all__ = [
    "ProCaptureDevice",
    "MockProCaptureDevice",
    "ProCaptureController",
    "ProCaptureSettings",
    "TransferMode",
    "ImageSizeInPixels",
    "ColourFormat",
]

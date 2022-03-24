from datetime import datetime
from time import perf_counter
from unittest import TestCase

import pytest
from numpy import diff, array

from pymagewell.pro_capture_controller import ProCaptureController
from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.pro_capture_device.device_interface import ProCaptureDeviceInterface
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, TransferMode
from pymagewell.pro_capture_device.mock_pro_capture_device import MockProCaptureDevice


@pytest.mark.usefixtures("hardware_mode")
class TestCaptureController(TestCase):
    def setUp(self) -> None:
        device_settings = ProCaptureSettings()
        device_settings.transfer_mode = TransferMode.TIMER
        assert hasattr(self, "hardware_mode_is_set")
        if self.hardware_mode_is_set:  # type: ignore
            self._device: ProCaptureDeviceInterface = ProCaptureDevice(device_settings)
        else:
            self._device = MockProCaptureDevice(device_settings)

        self._controller = ProCaptureController(device=self._device)

    def tearDown(self) -> None:
        self._controller.shutdown()

    def test_frame_timestamp(self) -> None:
        frame = self._controller.transfer_when_ready(timeout_ms=1000)
        seconds_since_frame = (datetime.now() - frame.timestamp).total_seconds()
        self.assertTrue(0 <= seconds_since_frame < 0.25)

    def test_frame_size(self) -> None:
        frame = self._controller.transfer_when_ready(timeout_ms=1000)
        self.assertEqual(frame.dimensions.rows, self._device.frame_properties.dimensions.rows)
        self.assertEqual(frame.dimensions.cols, self._device.frame_properties.dimensions.cols)

    def test_frame_period(self) -> None:
        times_frames_received = []
        for _ in range(10):
            _ = self._controller.transfer_when_ready(timeout_ms=1000)
            times_frames_received.append(perf_counter())
        mean_frame_period = diff(array(times_frames_received)).mean()
        self.assertAlmostEqual(self._device.signal_status.frame_period_s, mean_frame_period, 1)
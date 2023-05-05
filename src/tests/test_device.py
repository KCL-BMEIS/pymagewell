from copy import copy
from ctypes import create_string_buffer
from time import perf_counter
from unittest import TestCase

import pytest

from pymagewell.events.event_base import wait_for_event
from pymagewell.pro_capture_device import ProCaptureDevice
from pymagewell.pro_capture_device.device_interface import ProCaptureDeviceInterface
from pymagewell.pro_capture_device.device_settings import ProCaptureSettings, TransferMode
from pymagewell.pro_capture_device.mock_pro_capture_device import MockProCaptureDevice


@pytest.mark.usefixtures("hardware_mode")
class TestEvents(TestCase):
    def setUp(self) -> None:
        device_settings = ProCaptureSettings()
        device_settings.transfer_mode = TransferMode.TIMER

        assert hasattr(self, "hardware_mode_is_set")
        if self.hardware_mode_is_set:  # type: ignore
            self._device: ProCaptureDeviceInterface = ProCaptureDevice(device_settings)
        else:
            self._device = MockProCaptureDevice(device_settings)

    def tearDown(self) -> None:
        self._device.shutdown()

    def test_transfer_mode(self) -> None:
        self.assertEqual(self._device.transfer_mode, TransferMode.TIMER)

    def test_timer_mode_event_registration(self) -> None:
        events = self._device.events
        self.assertTrue(events.signal_change.is_registered)
        self.assertTrue(events.timer_event.is_registered)

        self.assertFalse(events.frame_buffered.is_registered)
        self.assertFalse(events.frame_buffering.is_registered)

    def test_schedule_timer_event(self) -> None:
        expected_wait_time = self._device.signal_status.frame_period_s

        # First timer event not necessarily occurring after one frame period, so use second
        self._device.schedule_timer_event()
        wait_for_event(self._device.events.timer_event, timeout_ms=1000)

        # Seconds one happens after 1 frame period
        second_frame_start_time = perf_counter()
        self._device.schedule_timer_event()
        wait_for_event(self._device.events.timer_event, timeout_ms=1000)
        time_waited = perf_counter() - second_frame_start_time
        if self.hardware_mode_is_set:  # type: ignore
            self.assertAlmostEqual(time_waited, expected_wait_time, 3)
        else:
            # Mock mode timing is less accurate
            self.assertAlmostEqual(time_waited, expected_wait_time, 1)

    def test_frame_transfer(self) -> None:
        transfer_buffer = create_string_buffer(3840 * 2160 * 4)
        self._device.start_grabbing()
        self._device.schedule_timer_event()
        buffer_before = copy(transfer_buffer)
        wait_for_event(self._device.events.timer_event, timeout_ms=1000)
        self._device.start_a_frame_transfer(transfer_buffer)
        wait_for_event(self._device.events.transfer_complete, timeout_ms=1000)
        buffer_after = copy(transfer_buffer)
        self.assertFalse(buffer_before == buffer_after)

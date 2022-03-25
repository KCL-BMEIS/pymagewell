from threading import Thread
from time import sleep, perf_counter
from unittest import TestCase

from pymagewell.events.event_base import Event, wait_for_event, wait_for_events
from pymagewell.events.device_events import TransferCompleteEvent, TimerEvent, FrameBufferedEvent
from pymagewell.events.notification import Notification


class TestEvents(TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_wait_for_event(self) -> None:
        event = Event()
        event_thread = Thread(target=_set_event_after_100ms, args=[event])
        start_time = perf_counter()
        event_thread.start()
        wait_for_event(event, timeout_ms=1000)
        time_waited = perf_counter() - start_time
        self.assertTrue((time_waited > 0.1) and (time_waited < 0.15))

    def test_wait_for_events(self) -> None:
        events = [TransferCompleteEvent(), TimerEvent()]
        event_thread = Thread(target=_set_event_after_100ms, args=[events[0]])
        start_time = perf_counter()
        event_thread.start()
        event_that_occurred = wait_for_events(events, timeout_ms=1000)
        time_waited = perf_counter() - start_time
        self.assertTrue((time_waited > 0.1) and (time_waited < 0.15))
        self.assertTrue(isinstance(event_that_occurred, TransferCompleteEvent))

    def test_register_event(self) -> None:
        event = FrameBufferedEvent()
        self.assertFalse(event.is_registered)
        event.register(Notification(0, 0))
        self.assertTrue(event.is_registered)


def _set_event_after_100ms(event: Event) -> None:
    sleep(0.1)
    event.set()

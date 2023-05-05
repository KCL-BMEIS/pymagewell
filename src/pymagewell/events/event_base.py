from abc import ABC, abstractmethod
from typing import Optional, Any, List


try:
    import win32api
    import win32event
except ModuleNotFoundError as e:
    try:
        from pymagewell.events import mock_win32api as win32api, mock_win32event as win32event
    except ModuleNotFoundError:
        raise e

from pymagewell.events.notification import Notification
from pymagewell.exceptions import ProCaptureError, WaitForEventTimeout


class Event:
    def __init__(self) -> None:
        self._win32_event = win32event.CreateEvent(None, False, False, None)

    @property
    def win32_event(self) -> Any:
        return self._win32_event

    def set(self) -> None:
        win32event.SetEvent(self.win32_event)

    def destroy(self) -> None:
        win32api.CloseHandle(int(self.win32_event))
        self._win32_event = 0


class RegisterableEvent(Event, ABC):
    def __init__(self) -> None:
        super().__init__()
        self._state: EventState = Unregistered()
        self._notification: Optional[Notification] = None

    @property
    def notification(self) -> Optional[Notification]:
        return self._state.get_notification(self)

    def register(self, notification: Notification) -> None:
        self._state = self._state.register(notification)

    @property
    @abstractmethod
    def registration_token(self) -> Optional[int]:
        raise NotImplementedError()

    @property
    def is_registered(self) -> bool:
        return isinstance(self._state, Registered)


class EventState(ABC):
    @abstractmethod
    def register(self, notification: Notification) -> "EventState":
        raise NotImplementedError()

    @abstractmethod
    def get_notification(self, event: Event) -> Optional[Notification]:
        raise NotImplementedError()


class Registered(EventState):
    def __init__(self, notification: Notification):
        self._notification = notification

    def register(self, notification: Notification) -> "EventState":
        return self

    def get_notification(self, event: Event) -> Optional[Notification]:
        return self._notification


class Unregistered(EventState):
    def register(self, notification: Notification) -> "EventState":
        return Registered(notification)

    def get_notification(self, event: Event) -> Optional[Notification]:
        return None


def wait_for_events(events: List[Event], timeout_ms: int) -> Event:
    result = win32event.WaitForMultipleObjects(tuple([event.win32_event for event in events]), False, timeout_ms)
    if result == 258:
        raise WaitForEventTimeout("Error: wait timed out")
    elif result == win32event.WAIT_OBJECT_0 + 0:
        return events[0]
    elif result == win32event.WAIT_OBJECT_0 + 1:
        return events[1]
    else:
        raise ProCaptureError(f"Wait for event failed: error code {result}")


def wait_for_event(event: Event, timeout_ms: int) -> None:
    result = win32event.WaitForSingleObject(event.win32_event, timeout_ms)
    if result == 258:
        raise WaitForEventTimeout("Error: wait timed out")

from abc import ABC, abstractmethod
from typing import Optional, Any

import win32api
import win32event

from pymagewell.notifications import Notification


class Event:
    def __init__(self):
        self._win32_event = win32event.CreateEvent(None, False, False, None)

    @property
    def win32_event(self) -> Any:
        return self._win32_event

    def destroy(self) -> None:
        win32api.CloseHandle(int(self.win32_event))
        self._win32_event = 0


class RegisterableEvent(Event, ABC):
    def __init__(self):
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
    def register(self, notification: Notification) -> 'EventState':
        raise NotImplementedError()

    @abstractmethod
    def get_notification(self, event: Event) -> Optional[Notification]:
        raise NotImplementedError()


class Registered(EventState):
    def __init__(self, notification: Notification):
        self._notification = notification

    def register(self, notification: Notification) -> 'EventState':
        return self

    def get_notification(self, event: Event) -> Optional[Notification]:
        return self._notification


class Unregistered(EventState):
    def register(self, notification: Notification) -> 'EventState':
        return Registered(notification)

    def get_notification(self, event: Event) -> Optional[Notification]:
        return None

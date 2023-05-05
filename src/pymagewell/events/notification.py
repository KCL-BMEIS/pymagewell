from mwcapture.libmwcapture import mw_notify_status, MW_SUCCEEDED, mw_capture
from pymagewell.exceptions import ProCaptureError

MWCAP_NOTIFY_VIDEO_FRAME_BUFFERING = 0x0100
MWCAP_NOTIFY_VIDEO_FRAME_BUFFERED = 0x0400


class NotificationStatus:
    def __init__(self, mw_notify_status: mw_notify_status):
        self._mw_notify_status = mw_notify_status

    def check_notification_source(self, notification_token: int) -> bool:
        return (self._mw_notify_status.m_ll_notify_status & notification_token) == 0


class Notification:
    def __init__(self, notification_handle: int, channel: int):
        self._handle = notification_handle
        self._channel = channel

    def get_status(self, mw_capture: mw_capture) -> NotificationStatus:
        status: mw_notify_status = mw_notify_status()  # type: ignore
        res: int = mw_capture.mw_get_notify_status(self._channel, self._handle, status)  # type: ignore
        if res != MW_SUCCEEDED:
            raise ProCaptureError("Could not read status of notification")
        return NotificationStatus(status)

    @property
    def handle(self) -> int:
        return self._handle

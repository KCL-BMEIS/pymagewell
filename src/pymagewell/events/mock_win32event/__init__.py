import logging
from typing import Any

logger = logging.getLogger(__name__)

logger.warning("win32api and win32 event packages not available. pymagewell will only work with MockProCaptureDevice.")

WAIT_OBJECT_0 = 0


def CreateEvent(a: Any, b: Any, c: Any, d: Any) -> Any:
    pass


def SetEvent(a: Any) -> None:
    pass


def WaitForMultipleObjects(a: Any, b: Any, c: Any) -> Any:
    return WAIT_OBJECT_0 + 0


def WaitForSingleObject(a: Any, b: Any) -> Any:
    pass

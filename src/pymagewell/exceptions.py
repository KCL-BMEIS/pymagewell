class ProCaptureError(Exception):
    pass


class WaitForEventTimeout(ProCaptureError):
    pass


class FFMPEGNotAvailable(Exception):
    pass

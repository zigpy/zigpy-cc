from zigpy.exceptions import ZigbeeException


class CommandError(ZigbeeException):
    def __init__(self, status, *args, **kwargs):
        self._status = status
        super().__init__(*args, **kwargs)

    @property
    def status(self):
        return self._status

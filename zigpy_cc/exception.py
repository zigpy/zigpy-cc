import logging

from zigpy.exceptions import ZigbeeException

LOGGER = logging.getLogger(__name__)


class TODO(Exception):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        LOGGER.warning("Not implemented: " + msg, *args)


class CommandError(ZigbeeException):
    def __init__(self, status, *args, **kwargs):
        self._status = status
        super().__init__(*args, **kwargs)

    @property
    def status(self):
        return self._status

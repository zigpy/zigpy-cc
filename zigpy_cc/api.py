import asyncio
import logging

from . import uart
from .definition import Definition
from .types import Subsystem

LOGGER = logging.getLogger(__name__)

DataStart = 4
SOF = 0xFE

PositionDataLength = 1
PositionCmd0 = 2
PositionCmd1 = 3

MinMessageLength = 5
MaxDataSize = 250


COMMAND_TIMEOUT = 2
CC_BAUDRATE = 115200


class API:
    def __init__(self):
        self._uart = None
        self._seq = 1
        self._awaiting = {}
        self._app = None
        self._proto_ver = None

    @property
    def protocol_version(self):
        """Protocol Version."""
        return self._proto_ver

    def set_application(self, app):
        self._app = app

    async def connect(self, device, baudrate=CC_BAUDRATE):
        assert self._uart is None
        self._uart = await uart.connect(device, baudrate, self)

    def close(self):
        return self._uart.close()

    async def _command(self, subsystem, command, payload) -> uart.ZpiObject:
        cmd = self.createRequest(subsystem, command, payload)
        LOGGER.debug("Command %s", cmd)

        frame = cmd.to_unpi_frame()
        self._uart.send(frame)
        fut = asyncio.Future()
        seq = "{}_{}".format(subsystem, command)

        self._awaiting[seq] = fut
        try:
            return await asyncio.wait_for(fut, timeout=COMMAND_TIMEOUT)
        except asyncio.TimeoutError:
            LOGGER.warning("No response to '%s' command", cmd)
            self._awaiting.pop(seq)
            raise



    def data_received(self, frame):
        object = uart.ZpiObject.from_unpi_frame(frame)
        # print('data_received', object)

        # TODO ?
        solicited = True
        seq = "{}_{}".format(object.subsystem, object.command)

        if solicited and seq in self._awaiting:
            fut = self._awaiting.pop(seq)
            fut.set_result(object)

    async def version(self):
        version = await self._command(Subsystem.SYS, "version", {})
        # if (
        #     self.protocol_version >= MIN_PROTO_VERSION
        #     and (version[0] & 0x0000FF00) == 0x00000500
        # ):
        #     self._aps_data_ind_flags = 0x04
        return version.payload

    def _handle_version(self, data):
        LOGGER.debug("Version response: %x", data[0])





    def createRequest(self, subsystem, command, payload):
        cmd = next(c for c in Definition[subsystem] if c["name"] == command)

        return uart.ZpiObject(cmd["type"], subsystem, command, cmd["ID"], payload, cmd["request"])


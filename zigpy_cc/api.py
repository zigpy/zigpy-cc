import asyncio
import logging

from . import uart
from .definition import Definition
from .types import Subsystem, CommandType, Timeouts
from .zpi_object import ZpiObject

LOGGER = logging.getLogger(__name__)

COMMAND_TIMEOUT = 3
CC_BAUDRATE = 115200


class Waiter:
    def __init__(self, seq, future, timeout):
        self.seq = seq
        self.future = future
        self.timeout = timeout

    async def wait(self):
        return await asyncio.wait_for(self.future, self.timeout / 1000)

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

    async def _command(self, subsystem, command, payload) -> ZpiObject:
        return await self.request(subsystem, command, payload)

    async def request(self, subsystem, command, payload, expectedStatus = [0]):
        """
        TODO add queue
        """
        obj = self._create_obj(subsystem, command, payload)
        LOGGER.debug("<-- %s", obj)

        frame = obj.to_unpi_frame()

        if obj.type == CommandType.SREQ:
            timeout = Timeouts.SREQ
            waiter = self.wait_for(CommandType.SRSP, subsystem, command, {}, timeout)
            self._uart.send(frame)
            result = await waiter.wait()
            if result and 'status' in result.payload and result.payload['status'] not in expectedStatus:
                raise Exception(
                    "SREQ '{}' failed with status '{}' (expected '{}')".format(command, result.payload['status'], expectedStatus)
                )
            else:
                return result
        elif obj.type == CommandType.AREQ and obj.is_reset_command():
            waiter = self.wait_for(CommandType.AREQ, Subsystem.SYS, 'resetInd', {}, Timeouts.reset)
            # TODO clear queue
            self._uart.send(frame)
            return await waiter.wait()
        else:
            if obj.type == CommandType.AREQ:
                self._uart.send(frame)
                return None
            else:
                raise Exception("Unknown type '{}'".format(obj.type))

        # self._uart.send(frame)
        # fut = asyncio.Future()
        # seq = "{}_{}".format(subsystem, 'resetInd' if command == "resetReq" else command)
        #
        # self._awaiting[seq] = fut
        # try:
        #     return await asyncio.wait_for(fut, timeout=COMMAND_TIMEOUT)
        # except asyncio.TimeoutError:
        #     LOGGER.warning("No response to '%s' command", obj)
        #     self._awaiting.pop(seq)
        #     raise

    def wait_for(self, type, subsystem, command, payload = {}, timeout = Timeouts.default):
        fut = asyncio.Future()
        seq = "{}_{}_{}".format(type, subsystem, command)
        self._awaiting[seq] = fut

        return Waiter(seq, fut, timeout)

    def data_received(self, frame):
        obj = ZpiObject.from_unpi_frame(frame)
        LOGGER.debug('--> %s', obj)

        seq = "{}_{}_{}".format(obj.type, obj.subsystem, obj.command)

        if seq in self._awaiting:
            fut = self._awaiting.pop(seq)
            fut.set_result(obj)
        else:
            LOGGER.debug('NOT A RESPONSE %s', obj)

        try:
            getattr(self, "_handle_%s" % (obj.command,))(obj)
        except AttributeError as e:
            # LOGGER.warning(e)
            pass

    async def version(self):
        version = await self._command(Subsystem.SYS, "version", {})
        # todo check version
        self._proto_ver = version.payload
        return version.payload

    def _handle_version(self, data):
        LOGGER.debug("Version response: %s", data.payload)

    def _create_obj(self, subsystem, command, payload):
        cmd = next(c for c in Definition[subsystem] if c["name"] == command)

        return ZpiObject(
            cmd["type"], subsystem, command, cmd["ID"], payload, cmd["request"]
        )


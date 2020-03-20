import asyncio
import logging
from typing import List

from zigpy_cc.exception import CommandError
from . import uart
from .definition import Definition
from .types import Repr, Subsystem, CommandType, Timeouts
from .zpi_object import ZpiObject

LOGGER = logging.getLogger(__name__)

COMMAND_TIMEOUT = 3
CC_BAUDRATE = 115200


class Matcher(Repr):
    def __init__(self, type, subsystem, command, payload):
        self.type = type
        self.subsystem = subsystem
        self.command = command
        self.payload = payload


class Waiter(Repr):
    def __init__(
        self, type: int, subsystem: int, command: str, payload, timeout: int, sequence
    ):
        self.matcher = Matcher(type, subsystem, command, payload)
        self.future = asyncio.get_event_loop().create_future()
        self.timeout = timeout
        self.sequence = sequence

    async def wait(self):
        return await asyncio.wait_for(self.future, self.timeout / 1000)

    def set_result(self, result) -> None:
        if self.future.cancelled():
            LOGGER.warning("Waiter already cancelled: %s", self)
        elif self.future.done():
            LOGGER.warning("Waiter already done: %s", self)
        else:
            self.future.set_result(result)

    def match(self, obj: ZpiObject):
        matcher = self.matcher
        if (
            matcher.type != obj.type
            or matcher.subsystem != obj.subsystem
            or matcher.command != obj.command
        ):
            return False

        if matcher.payload:
            for f, v in matcher.payload.items():
                if v != obj.payload[f]:
                    LOGGER.debug(
                        "payload missmatch\n-%s\n+%s", matcher.payload, obj.payload
                    )
                    return False

        return True


class API:
    def __init__(self):
        self._uart = None
        self._seq = 1
        self._waiters: List[Waiter] = []
        self._app = None
        self._device = None
        self._baudrare = None
        self._proto_ver = None

    @property
    def protocol_version(self):
        """Protocol Version."""
        return self._proto_ver

    def set_application(self, app):
        self._app = app

    async def connect(self, device, baudrate=CC_BAUDRATE):
        assert self._uart is None
        self._device = device
        self._baudrare = baudrate
        self._uart = await uart.connect(device, baudrate, self)

    async def reconnect(self):
        self._uart = await uart.connect(self._device, self._baudrare, self)

    def close(self):
        return self._uart.close()

    def connection_lost(self):
        self._app.connection_lost()

    async def _command(self, subsystem, command, payload) -> ZpiObject:
        return await self.request(subsystem, command, payload)

    async def request(self, subsystem, command, payload, expectedStatus=None):
        obj = ZpiObject.from_command(subsystem, command, payload)
        return await self.request_raw(obj, expectedStatus)

    async def request_raw(self, obj: ZpiObject, expectedStatus=None):
        if expectedStatus is None:
            expectedStatus = [0]
        """
        TODO add queue
        """
        LOGGER.debug("--> %s", obj)
        frame = obj.to_unpi_frame()

        if obj.type == CommandType.SREQ:
            timeout = Timeouts.SREQ
            waiter = self.wait_for(
                CommandType.SRSP, obj.subsystem, obj.command, {}, timeout
            )
            self._uart.send(frame)
            result = await waiter.wait()
            if (
                result
                and "status" in result.payload
                and result.payload["status"] not in expectedStatus
            ):
                raise CommandError(
                    result.payload["status"],
                    "SREQ '{}' failed with status '{}' (expected '{}')".format(
                        obj.command, result.payload["status"], expectedStatus
                    ),
                )
            else:
                if obj.type == CommandType.SREQ and obj.command == "dataRequest":
                    payload = {
                        "endpoint": obj.payload["destendpoint"],
                        "transid": obj.payload["transid"],
                    }
                    waiter = self.wait_for(
                        CommandType.AREQ, Subsystem.AF, "dataConfirm", payload,
                    )
                    LOGGER.debug("waiting for dataConfirm")
                    result = await waiter.wait()
                    LOGGER.debug("res %s", result)

                return result
        elif obj.type == CommandType.AREQ and obj.is_reset_command():
            waiter = self.wait_for(
                CommandType.AREQ, Subsystem.SYS, "resetInd", {}, Timeouts.reset
            )
            # TODO clear queue
            self._uart.send(frame)
            return await waiter.wait()
        else:
            if obj.type == CommandType.AREQ:
                self._uart.send(frame)
                return None
            else:
                LOGGER.warning("Unknown type '%s'", obj.type)
                raise Exception("Unknown type '{}'".format(obj.type))

    def create_response_waiter(self, obj: ZpiObject, sequence=None):
        waiter = self.get_response_waiter(obj, sequence)
        if waiter:
            LOGGER.debug("waiting for %d %s", sequence, obj.command)

    def get_response_waiter(self, obj: ZpiObject, sequence=None):
        if obj.type == CommandType.SREQ and obj.command == "dataRequest":
            return None

        if obj.type == CommandType.SREQ and obj.command.endswith("Req"):
            rsp = obj.command.replace("Req", "Rsp")
            for cmd in Definition[obj.subsystem]:
                if rsp == cmd["name"]:
                    payload = {"srcaddr": obj.payload["dstaddr"]}
                    return self.wait_for(
                        CommandType.AREQ, Subsystem.ZDO, rsp, payload, sequence=sequence
                    )

        LOGGER.warning("no response cmd configured for %s", obj.command)
        return None

    def wait_for(
        self,
        type,
        subsystem,
        command,
        payload=None,
        timeout=Timeouts.default,
        sequence=None,
    ):
        waiter = Waiter(type, subsystem, command, payload, timeout, sequence)
        self._waiters.append(waiter)

        return waiter

    def data_received(self, frame):
        try:
            obj = ZpiObject.from_unpi_frame(frame)
        except Exception as e:
            LOGGER.error("Error while parsing frame: %s", frame)
            raise e

        to_remove = []
        for waiter in self._waiters:
            if waiter.match(obj):
                # LOGGER.debug("MATCH FOUND %s", waiter)
                to_remove.append(waiter)
                waiter.set_result(obj)
                if waiter.sequence:
                    obj.sequence = waiter.sequence
                    break

        LOGGER.debug("<-- %s", obj)

        for waiter in to_remove:
            self._waiters.remove(waiter)

        if self._app is not None:
            self._app.handle_znp(obj)

        try:
            getattr(self, "_handle_%s" % (obj.command,))(obj)
        except AttributeError:
            pass

    async def version(self):
        version = await self._command(Subsystem.SYS, "version", {})
        # todo check version
        self._proto_ver = version.payload
        return version.payload

    def _handle_version(self, data):
        LOGGER.debug("Version response: %s", data.payload)

    def _handle_getDeviceInfo(self, data):
        LOGGER.debug("Device info: %s", data.payload)

    def _handle_srcRtgInd(self, data):
        pass

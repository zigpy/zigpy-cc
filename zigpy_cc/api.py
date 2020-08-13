import asyncio
import logging
from typing import Any, Dict, Optional

import serial
import zigpy.exceptions

from zigpy_cc import uart
from zigpy_cc.config import CONF_DEVICE_PATH, SCHEMA_DEVICE
from zigpy_cc.definition import Definition
from zigpy_cc.exception import CommandError
from zigpy_cc.types import CommandType, Repr, Subsystem, Timeouts
from zigpy_cc.uart import Gateway
from zigpy_cc.zpi_object import ZpiObject

LOGGER = logging.getLogger(__name__)

COMMAND_TIMEOUT = 2


class Matcher(Repr):
    def __init__(self, command_type, subsystem, command, payload):
        self.command_type = command_type
        self.subsystem = subsystem
        self.command = command
        self.payload = payload


class Waiter(Repr):
    def __init__(
        self,
        waiter_id: int,
        command_type: int,
        subsystem: int,
        command: str,
        payload,
        timeout: int,
        sequence,
    ):
        self.id = waiter_id
        self.matcher = Matcher(command_type, subsystem, command, payload)
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
            matcher.command_type != obj.command_type
            or matcher.subsystem != obj.subsystem
            or matcher.command != obj.command
        ):
            return False

        if matcher.payload:
            for f, v in matcher.payload.items():
                if v != obj.payload[f]:
                    return False

        return True


class API:
    _uart: Optional[Gateway]

    def __init__(self, device_config: Dict[str, Any]):
        self._config = device_config
        self._lock = asyncio.Lock()
        self._waiter_id = 0
        self._waiters: Dict[int, Waiter] = {}
        self._app = None
        self._proto_ver = None
        self._uart = None

    @property
    def protocol_version(self):
        """Protocol Version."""
        return self._proto_ver

    @classmethod
    async def new(cls, application, config: Dict[str, Any]) -> "API":
        api = cls(config)
        await api.connect()
        api.set_application(application)
        return api

    def set_application(self, app):
        self._app = app

    async def connect(self):
        assert self._uart is None
        self._uart = await uart.connect(self._config, self)

    def close(self):
        if self._uart:
            self._uart.close()
            self._uart = None

    def connection_lost(self):
        self._app.connection_lost()

    async def request(
        self, subsystem, command, payload, waiter_id=None, expected_status=None
    ):
        obj = ZpiObject.from_command(subsystem, command, payload)
        return await self.request_raw(obj, waiter_id, expected_status)

    async def request_raw(self, obj: ZpiObject, waiter_id=None, expected_status=None):
        async with self._lock:
            return await self._request_raw(obj, waiter_id, expected_status)

    async def _request_raw(self, obj: ZpiObject, waiter_id=None, expected_status=None):
        if expected_status is None:
            expected_status = [0]

        LOGGER.debug("--> %s", obj)
        frame = obj.to_unpi_frame()

        if obj.command_type == CommandType.SREQ:
            timeout = (
                20000
                if obj.command == "bdbStartCommissioning"
                or obj.command == "startupFromApp"
                else Timeouts.SREQ
            )
            waiter = self.wait_for(
                CommandType.SRSP, obj.subsystem, obj.command, {}, timeout
            )
            self._uart.send(frame)
            result = await waiter.wait()
            if (
                result
                and "status" in result.payload
                and result.payload["status"] not in expected_status
            ):
                if waiter_id is not None:
                    self._waiters.pop(waiter_id).set_result(result)

                raise CommandError(
                    result.payload["status"],
                    "SREQ '{}' failed with status '{}' (expected '{}')".format(
                        obj.command, result.payload["status"], expected_status
                    ),
                )
            else:
                return result
        elif obj.command_type == CommandType.AREQ and obj.is_reset_command():
            waiter = self.wait_for(
                CommandType.AREQ, Subsystem.SYS, "resetInd", {}, Timeouts.reset
            )
            # TODO clear queue, requests waiting for lock
            self._uart.send(frame)
            return await waiter.wait()
        else:
            if obj.command_type == CommandType.AREQ:
                self._uart.send(frame)
                return None
            else:
                LOGGER.warning("Unknown type '%s'", obj.command_type)
                raise Exception("Unknown type '{}'".format(obj.command_type))

    def create_response_waiter(self, obj: ZpiObject, sequence=None):
        if obj.command_type == CommandType.SREQ and obj.command.startswith(
            "dataRequest"
        ):
            payload = {
                "transid": obj.payload["transid"],
            }
            return self.wait_for(CommandType.AREQ, Subsystem.AF, "dataConfirm", payload)

        if obj.command_type == CommandType.SREQ and obj.command.endswith("Req"):
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
        command_type: CommandType,
        subsystem: Subsystem,
        command: str,
        payload=None,
        timeout=Timeouts.default,
        sequence=None,
    ):
        waiter = Waiter(
            self._waiter_id,
            command_type,
            subsystem,
            command,
            payload,
            timeout,
            sequence,
        )
        self._waiters[waiter.id] = waiter
        self._waiter_id += 1

        def callback():
            if not waiter.future.done() or waiter.future.cancelled():
                LOGGER.warning(
                    "No response for: %s %s %s %s",
                    command_type.name,
                    subsystem.name,
                    command,
                    payload,
                )
                try:
                    self._waiters.pop(waiter.id)
                except KeyError:
                    LOGGER.warning("Waiter not found: %s", waiter)

        asyncio.get_event_loop().call_later(timeout / 1000 + 0.1, callback)

        return waiter

    def data_received(self, frame):
        try:
            obj = ZpiObject.from_unpi_frame(frame)
        except Exception as e:
            LOGGER.error("Error while parsing frame: %s", frame)
            raise e

        for waiter_id in list(self._waiters):
            waiter = self._waiters.get(waiter_id)
            if waiter.match(obj):
                self._waiters.pop(waiter_id)
                waiter.set_result(obj)
                if waiter.sequence:
                    obj.sequence = waiter.sequence
                    break

        LOGGER.debug("<-- %s", obj)

        if self._app is not None:
            self._app.handle_znp(obj)

        try:
            getattr(self, "_handle_%s" % (obj.command,))(obj)
        except AttributeError:
            pass

    async def version(self):
        version = await self.request(Subsystem.SYS, "version", {})
        # todo check version
        self._proto_ver = version.payload
        return version.payload

    def _handle_version(self, data):
        LOGGER.debug("Version response: %s", data.payload)

    def _handle_getDeviceInfo(self, data):
        LOGGER.info("Device info: %s", data.payload)

    def _handle_srcRtgInd(self, data):
        pass

    @classmethod
    async def probe(cls, device_config: Dict[str, Any]) -> bool:
        """Probe port for the device presence."""
        api = cls(SCHEMA_DEVICE(device_config))
        try:
            await asyncio.wait_for(api._probe(), timeout=COMMAND_TIMEOUT)
            return True
        except (
            asyncio.TimeoutError,
            serial.SerialException,
            zigpy.exceptions.ZigbeeException,
        ) as exc:
            LOGGER.debug(
                "Unsuccessful radio probe of '%s' port",
                device_config[CONF_DEVICE_PATH],
                exc_info=exc,
            )
        finally:
            api.close()

        return False

    async def _probe(self) -> None:
        """Open port and try sending a command"""
        await self.connect()
        await self.version()

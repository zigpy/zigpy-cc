import asyncio
import logging

import serial
import serial.tools.list_ports
import serial_asyncio

import zigpy_cc.types as t

LOGGER = logging.getLogger(__name__)

DataStart = 4
SOF = 0xFE

PositionDataLength = 1
PositionCmd0 = 2
PositionCmd1 = 3

MinMessageLength = 5
MaxDataSize = 250


class Parser:
    def __init__(self) -> None:
        self.buffer = b""

    def write(self, b: int):
        self.buffer += bytes([b])
        if SOF == self.buffer[0]:
            if len(self.buffer) > MinMessageLength:
                dataLength = self.buffer[PositionDataLength]

                fcsPosition = DataStart + dataLength
                frameLength = fcsPosition + 1

                if len(self.buffer) >= frameLength:
                    frameBuffer = self.buffer[0:frameLength]
                    self.buffer = self.buffer[frameLength:]

                    frame = UnpiFrame.from_buffer(dataLength, fcsPosition, frameBuffer)

                    return frame
        else:
            LOGGER.debug("drop char")
            self.buffer = b""

        return None


class UnpiFrame(t.Repr):
    def __init__(
        self,
        command_type: int,
        subsystem: int,
        command_id: int,
        data: bytes,
        length=None,
        fcs=None,
    ):
        self.type = t.CommandType(command_type)
        self.subsystem = t.Subsystem(subsystem)
        self.command_id = command_id
        self.data = data
        self.length = length
        self.fcs = fcs

    @classmethod
    def from_buffer(cls, length, fcs_position, buffer):
        subsystem = buffer[PositionCmd0] & 0x1F
        command_type = (buffer[PositionCmd0] & 0xE0) >> 5
        command_id = buffer[PositionCmd1]
        data = buffer[DataStart:fcs_position]
        fcs = buffer[fcs_position]

        checksum = cls.calculate_checksum(buffer[1:fcs_position])
        if checksum == fcs:
            return cls(command_type, subsystem, command_id, data, length, fcs)
        else:
            LOGGER.warning(
                "Invalid checksum: 0x%s, data: 0x%s", checksum, buffer,
            )
            return None

    @staticmethod
    def calculate_checksum(values):
        checksum = 0

        for value in values:
            checksum ^= value

        return checksum

    def to_buffer(self):
        length = len(self.data)
        cmd0 = ((self.type << 5) & 0xE0) | (self.subsystem & 0x1F)

        res = bytes([SOF, length, cmd0, self.command_id])
        res += self.data
        fcs = self.calculate_checksum(res[1:])

        return res + bytes([fcs])


class Gateway(asyncio.Protocol):
    _transport: serial_asyncio.SerialTransport

    def __init__(self, api, connected_future=None):
        self._parser = Parser()
        self._connected_future = connected_future
        self._api = api
        self._transport = None
        self._open = False

    def connection_made(self, transport: serial_asyncio.SerialTransport):
        """Callback when the uart is connected"""
        LOGGER.info("Connection made")
        self._open = True
        self._transport = transport
        if self._connected_future:
            self._connected_future.set_result(True)

    def close(self):
        self._open = False
        self._transport.close()

    def write(self, data):
        self._transport.write(data)

    def send(self, frame: UnpiFrame):
        """Send data, taking care of escaping and framing"""
        data = frame.to_buffer()
        LOGGER.debug("Send: %s", data)
        self._transport.write(data)

    def data_received(self, data):
        """Callback when there is data received from the uart"""

        found = False
        for b in data:
            frame = self._parser.write(b)
            if frame is not None:
                found = True
                LOGGER.debug("Frame received: %s", frame)
                self._api.data_received(frame)

        if not found:
            LOGGER.info("Bytes received: %s", data)

    def connection_lost(self, exc):
        if self._open:
            LOGGER.error("Serial port closed unexpectedly: %s", exc)
            self._api.connection_lost()


async def connect(port, baudrate, api, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    connected_future = loop.create_future()
    protocol = Gateway(api, connected_future)

    if port == "auto":
        devices = list(serial.tools.list_ports.grep("0451:"))
        if devices:
            port = devices[0].device
            LOGGER.info("%s found at %s", devices[0].product, port)
        else:
            LOGGER.error("Unable to find TI CC device using auto mode")

    _, protocol = await serial_asyncio.create_serial_connection(
        loop,
        lambda: protocol,
        url=port,
        baudrate=baudrate,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        xonxoff=False,
        rtscts=True,
    )

    await connected_future

    protocol.write(b"\xef")
    await asyncio.sleep(1)

    return protocol

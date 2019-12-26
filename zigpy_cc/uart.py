import asyncio
import logging

import serial
import serial_asyncio

from zigpy_cc.buffalo import Buffalo

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
        self.buffer = bytearray()

    def write(self, b):
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
            self.buffer = bytearray()

        return None




class UnpiFrame:
    def __init__(self, type, subsystem, command_id, data, length=None, fcs=None):
        self.type = type
        self.subsystem = subsystem
        self.command_id = command_id
        self.data = data
        self.length = length
        self.fcs = fcs

    @classmethod
    def from_buffer(cls, length, fcs_position, buffer):
        subsystem = buffer[PositionCmd0] & 0x1F
        type = (buffer[PositionCmd0] & 0xE0) >> 5
        command_id = buffer[PositionCmd1]
        data = buffer[DataStart:fcs_position]
        fcs = buffer[fcs_position]

        checksum = cls.calculate_checksum(buffer[1:fcs_position])

        if checksum == fcs:
            return cls(type, subsystem, command_id, data, length, fcs)
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
        res = b""

        cmd0 = ((self.type << 5) & 0xE0) | (self.subsystem & 0x1F)

        res += bytes([SOF, length, cmd0, self.command_id])
        res += self.data

        checksum = self.calculate_checksum(res[1:])
        res += bytes([checksum])

        return res

    def __str__(self) -> str:
        return "{} - {} - {} - {} - [{}] - {}".format(
            self.subsystem, self.command_id, self.type, self.length, self.data, self.fcs
        )


class Gateway(asyncio.Protocol):
    DataStart = 4

    PositionDataLength = 1
    PositionCmd0 = 2
    PositionCmd1 = 3

    MinMessageLength = 5
    MaxDataSize = 250

    def __init__(self, api, connected_future=None):
        self._parser = Parser()
        self._connected_future = connected_future
        self._api = api
        # self._transport = None

    def connection_made(self, transport: asyncio.Transport):
        """Callback when the uart is connected"""
        LOGGER.debug("Connection made")
        self._transport = transport
        if self._connected_future:
            self._connected_future.set_result(True)

    def close(self):
        self._transport.close()

    def write(self, data):
        self._transport.write(data)

    def send(self, frame: UnpiFrame):
        """Send data, taking care of escaping and framing"""
        LOGGER.debug("Send: %s", frame)
        data = frame.to_buffer()
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

        # self._buffer += data
        # while self._buffer:
        #     end = self._buffer.find(self.END)
        #     if end < 0:
        #         return None
        #
        #     frame = self._buffer[:end]
        #     self._buffer = self._buffer[(end + 1) :]
        #     frame = self._unescape(frame)
        #
        #     if len(frame) < 4:
        #         continue
        #
        #     checksum = frame[-2:]
        #     frame = frame[:-2]
        #     if self._checksum(frame) != checksum:
        #         LOGGER.warning(
        #             "Invalid checksum: 0x%s, data: 0x%s",
        #             binascii.hexlify(checksum).decode(),
        #             binascii.hexlify(frame).decode(),
        #         )
        #         continue
        #
        #     LOGGER.debug("Frame received: 0x%s", binascii.hexlify(frame).decode())
        #     self._api.data_received(frame)


async def connect(port, baudrate, api, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    connected_future = asyncio.Future()
    protocol = Gateway(api, connected_future)

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

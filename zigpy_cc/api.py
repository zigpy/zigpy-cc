from zigpy_cc.definition import Definition
from zigpy_cc.types import CommandType, ParameterType

DataStart = 4
SOF = 0xFE

PositionDataLength = 1
PositionCmd0 = 2
PositionCmd1 = 3

MinMessageLength = 5
MaxDataSize = 250


class Parser:
    buffer = bytearray()

    def write(self, b):
        self.buffer += b
        if SOF == self.buffer[0]:
            if len(self.buffer) > MinMessageLength:
                dataLength = self.buffer[PositionDataLength]

                fcsPosition = DataStart + dataLength
                frameLength = fcsPosition + 1

                if len(self.buffer) >= frameLength:
                    frameBuffer = self.buffer[0:frameLength]
                    self.buffer = self.buffer[frameLength:]

                    frame = UnpiFrame.from_buffer(dataLength, fcsPosition, frameBuffer)
                    # print('--> parsed', frame)

                    object = ZpiObject.from_unpi_frame(frame)

                    return object
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
            raise Exception("Invalid checksum")

    @staticmethod
    def calculate_checksum(values):
        checksum = 0

        for value in values:
            checksum ^= value

        return checksum

    def to_buffer(self):
        length = len(self.data)
        res = bytearray()

        cmd0 = ((self.type << 5) & 0xE0) | (self.subsystem & 0x1F)

        res.append(SOF)
        res.append(length)
        res.append(cmd0)
        res.append(self.command_id)
        res += self.data

        checksum = self.calculate_checksum(res[1:])
        res.append(checksum)

        # print(res)

        return res

    def __str__(self) -> str:
        return '{} - {} - {} - {} - [{}] - {}'.format(
            self.length, self.type, self.subsystem, self.command_id, self.data, self.fcs
        )


class ZpiObject:
    def __init__(self, type, subsystem, command, commandId, payload, parameters):
        self.type = type
        self.subsystem = subsystem
        self.command = command
        self.command_id = commandId
        self.payload = payload
        self.parameters = parameters

    def to_unpi_frame(self):
        data = bytearray()

        for p in self.parameters:
            # TODO
            print(p)

        return UnpiFrame(self.type, self.subsystem, self.command_id, data)

    @classmethod
    def from_unpi_frame(cls, frame):
        cmd = next(c for c in Definition[frame.subsystem] if c["ID"] == frame.command_id)
        parameters = cmd["response"] if frame.type == CommandType.SRSP else cmd["request"]
        payload = cls.read_parameters(frame.data, parameters)

        return cls(frame.type, frame.subsystem, cmd["name"], cmd["ID"], payload, parameters)

    @classmethod
    def read_parameters(cls, data: bytearray, parameters):
        res = {}
        # print(parameters)
        start = 0
        for p in parameters:
            if p["parameterType"] == ParameterType.UINT8:
                res[p["name"]] = int.from_bytes(data[start:start + 1], 'little')
                start += 1
            elif p["parameterType"] == ParameterType.UINT16:
                res[p["name"]] = int.from_bytes(data[start:start + 2], 'little')
                start += 2
            elif p["parameterType"] == ParameterType.UINT32:
                res[p["name"]] = int.from_bytes(data[start:start + 4], 'little')
                start += 4
            elif p["parameterType"] == ParameterType.IEEEADDR:
                res[p["name"]] = '0x' + data[start:start + 8].hex()
                start += 8
            else:
                res[p["name"]] = None

        return res

    def __str__(self) -> str:
        return '{} - [{}]'.format(
            self.command, self.payload
        )

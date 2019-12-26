from zigpy_cc.types import ParameterType


class BuffaloOptions:

    def __init__(self) -> None:
        self.startIndex = None
        self.length = None


class Buffalo:
    def __init__(self, buffer, position=0) -> None:
        self.position = position
        self.buffer = buffer

    def __len__(self) -> int:
        return len(self.buffer)

    def read_parameter(self, type, options):
        if type == ParameterType.UINT8:
            res = self.read_int()
        elif type == ParameterType.UINT16:
            res = self.read_int(2)
        elif type == ParameterType.UINT32:
            res = self.read_int(4)
        elif type == ParameterType.IEEEADDR:
            res = "0x" + self.read(8).hex()
        elif type == ParameterType.BUFFER:
            length = options.length
            res = self.read(length)
        elif type == ParameterType.LIST_UINT16:
            res = []
            for i in range(0, options.length):
                res.append(self.read_int(2))
        else:
            raise Exception('read not implemented', ParameterType(type))

        return res

    def read_int(self, length=1):
        return int.from_bytes(self.read(length), "little")

    def read(self, length=1):
        res = self.buffer[self.position: self.position + length]
        self.position += length
        return res

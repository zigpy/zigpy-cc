import zigpy.types
from zigpy_cc.exception import TODO
from zigpy_cc.types import ParameterType


class BuffaloOptions:
    def __init__(self) -> None:
        self.startIndex = None
        self.length = None
        self.is_address = False


class Buffalo:
    def __init__(self, buffer, position=0) -> None:
        self.position = position
        self.buffer = buffer
        self._len = len(buffer)

    def __len__(self) -> int:
        return len(self.buffer)

    def write_parameter(self, type, value, options):
        if type == ParameterType.UINT8:
            self.write(value)
        elif type == ParameterType.UINT16:
            self.write(value, 2)
        elif type == ParameterType.UINT32:
            self.write(value, 4)
        elif type == ParameterType.IEEEADDR:
            for i in value:
                self.write(i)
        elif type == ParameterType.BUFFER:
            self.buffer += value
        elif type == ParameterType.LIST_UINT8:
            for v in value:
                self.write(v)
        elif type == ParameterType.LIST_UINT16:
            for v in value:
                self.write(v, 2)
        else:
            raise TODO("write %s", ParameterType(type))

    def write(self, value, length=1):
        self.buffer += value.to_bytes(length, "little")

    def read_parameter(self, type, options):
        if type == ParameterType.UINT8:
            res = self.read_int()
        elif type == ParameterType.UINT16:
            res = self.read_int(2)
            if options.is_address:
                res = zigpy.types.NWK(res)
        elif type == ParameterType.UINT32:
            res = self.read_int(4)
        elif type == ParameterType.IEEEADDR:
            res = zigpy.types.EUI64(self.read(8))
        elif ParameterType.is_buffer(type):
            type_name = ParameterType(type).name
            length = int(type_name.replace("BUFFER", "") or options.length)
            res = self.read(length)
        elif type == ParameterType.INT8:
            res = self.read_int(signed=True)
        else:
            # list types
            res = []
            if type == ParameterType.LIST_UINT8:
                for i in range(0, options.length):
                    res.append(self.read_int())
            elif type == ParameterType.LIST_UINT16:
                for i in range(0, options.length):
                    res.append(self.read_int(2))
            else:
                raise TODO("read type %d", type)

        return res

    def read_int(self, length=1, signed=False):
        return int.from_bytes(self.read(length), "little", signed=signed)

    def read(self, length=1):
        if self.position + length > self._len:
            raise OverflowError
        res = self.buffer[self.position : self.position + length]
        self.position += length
        return res

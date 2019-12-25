import enum
import zigpy.types

def deserialize(data, schema):
    result = []
    for type_ in schema:
        value, data = type_.deserialize(data)
        result.append(value)
    return result, data


def serialize(data, schema):
    return b''.join(t(v).serialize() for t, v in zip(schema, data))


class Bytes(bytes):
    def serialize(self):
        return self

    @classmethod
    def deserialize(cls, data):
        return cls(data), b''


class LBytes(bytes):
    def serialize(self):
        return uint8_t(len(self)).serialize() + self

    @classmethod
    def deserialize(cls, data, byteorder='big'):
        _bytes = int.from_bytes(data[:1], byteorder)
        s = data[1:_bytes + 1]
        return s, data[_bytes + 1:]


class int_t(int):
    _signed = True
    _size = 0

    def serialize(self, byteorder='big'):
        return self.to_bytes(self._size, byteorder, signed=self._signed)

    @classmethod
    def deserialize(cls, data, byteorder='big'):
        # Work around https://bugs.python.org/issue23640
        r = cls(int.from_bytes(data[:cls._size],
                               byteorder, signed=cls._signed))
        data = data[cls._size:]
        return r, data


class int8s(int_t):
    _size = 1


class int16s(int_t):
    _size = 2


class int24s(int_t):
    _size = 3


class int32s(int_t):
    _size = 4


class int40s(int_t):
    _size = 5


class int48s(int_t):
    _size = 6


class int56s(int_t):
    _size = 7


class int64s(int_t):
    _size = 8


class uint_t(int_t):
    _signed = False


class uint8_t(uint_t):
    _size = 1


class uint16_t(uint_t):
    _size = 2


class uint24_t(uint_t):
    _size = 3


class uint32_t(uint_t):
    _size = 4


class uint40_t(uint_t):
    _size = 5


class uint48_t(uint_t):
    _size = 6


class uint56_t(uint_t):
    _size = 7


class uint64_t(uint_t):
    _size = 8


class EUI64(zigpy.types.EUI64):
    @classmethod
    def deserialize(cls, data):
        r, data = super().deserialize(data)
        return cls(r[::-1]), data

    def serialize(self):
        assert self._length == len(self)
        return super().serialize()[::-1]


class NWK(zigpy.types.HexRepr, uint16_t):
    pass


class ADDRESS_MODE(uint8_t, enum.Enum):
    # Address modes used in zigate protocol

    GROUP = 0x01
    NWK = 0x02
    IEEE = 0x03


class Struct:
    _fields = []

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], self.__class__):
            # copy constructor
            for field in self._fields:
                if hasattr(args[0], field[0]):
                    setattr(self, field[0], getattr(args[0], field[0]))
        elif len(args) == len(self._fields):
            for arg, field in zip(args, self._fields):
                setattr(self, field[0], field[1](arg))
        elif kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def serialize(self):
        r = b''
        for field in self._fields:
            if hasattr(self, field[0]):
                r += getattr(self, field[0]).serialize()
        return r

    @classmethod
    def deserialize(cls, data):
        r = cls()
        for field_name, field_type in cls._fields:
            v, data = field_type.deserialize(data)
            setattr(r, field_name, v)
        return r, data

    def __repr__(self):
        r = '<%s ' % (self.__class__.__name__, )
        r += ' '.join(
            ['%s=%s' % (f[0], getattr(self, f[0], None)) for f in self._fields]
        )
        r += '>'
        return r


class Address(Struct):
    _fields = [
        ('address_mode', ADDRESS_MODE),
        ('address', EUI64),
    ]

    def __eq__(self, other):
        return other.address_mode == self.address_mode and other.address == self.address

    @classmethod
    def deserialize(cls, data):
        r = cls()
        field_name, field_type = cls._fields[0]
        mode, data = field_type.deserialize(data)
        setattr(r, field_name, mode)
        v = None
        if mode in [ADDRESS_MODE.GROUP, ADDRESS_MODE.NWK]:
            v, data = NWK.deserialize(data)
        elif mode == ADDRESS_MODE.IEEE:
            v, data = EUI64.deserialize(data)
        setattr(r, cls._fields[1][0], v)
        return r, data


class CommandType(uint8_t, enum.Enum):
    POLL = 0
    SREQ = 1
    AREQ = 2
    SRSP = 3


class Subsystem(uint8_t, enum.Enum):
    RESERVED = 0
    SYS = 1
    MAC = 2
    NWK = 3
    AF = 4
    ZDO = 5
    SAPI = 6,
    UTIL = 7,
    DEBUG = 8,
    APP = 9,
    APP_CNF = 15,
    GREENPOWER = 21,


class ParameterType(uint8_t, enum.Enum):
    UINT8 = 0
    UINT16 = 1
    UINT32 = 2
    IEEEADDR = 3

    BUFFER  = 4,
    BUFFER8 = 5,
    BUFFER16 = 6,
    BUFFER18 = 7,
    BUFFER32 = 8,
    BUFFER42 = 9,
    BUFFER100 = 10,

    LIST_UINT8 = 11,
    LIST_UINT16 = 12,
    LIST_ROUTING_TABLE = 13,
    LIST_BIND_TABLE = 14,
    LIST_NEIGHBOR_LQI = 15,
    LIST_NETWORK = 16,
    LIST_ASSOC_DEV = 17,

    INT8 = 18,

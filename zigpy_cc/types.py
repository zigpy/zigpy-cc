import enum

from zigpy.profiles import zha

import zigpy.zdo.types as t

# TODO remove unused
from zigpy_cc.exception import TODO


def deserialize(data, schema):
    result = []
    for type_ in schema:
        value, data = type_.deserialize(data)
        result.append(value)
    return result, data


def serialize(data, schema):
    return b"".join(t(v).serialize() for t, v in zip(schema, data))


class Bytes(bytes):
    def serialize(self):
        return self

    @classmethod
    def deserialize(cls, data):
        return cls(data), b""


class LVBytes(bytes):
    def serialize(self):
        return uint16_t(len(self)).serialize() + self

    @classmethod
    def deserialize(cls, data, byteorder="little"):
        length, data = uint16_t.deserialize(data)
        return cls(data[:length]), data[length:]


class int_t(int):
    _signed = True
    _size = 0

    def serialize(self, byteorder="little"):
        return self.to_bytes(self._size, byteorder, signed=self._signed)

    @classmethod
    def deserialize(cls, data, byteorder="little"):
        # Work around https://bugs.python.org/issue23640
        r = cls(int.from_bytes(data[: cls._size], byteorder, signed=cls._signed))
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


class ADDRESS_MODE(uint8_t, enum.Enum):
    # Address modes used in deconz protocol

    GROUP = 0x01
    NWK = 0x02
    IEEE = 0x03
    NWK_AND_IEEE = 0x04


class Struct:
    _fields = []

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], self.__class__):
            # copy constructor
            for field in self._fields:
                if hasattr(args[0], field[0]):
                    setattr(self, field[0], getattr(args[0], field[0]))

    def serialize(self):
        r = b""
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
        r = "<%s " % (self.__class__.__name__,)
        r += " ".join(
            ["%s=%s" % (f[0], getattr(self, f[0], None)) for f in self._fields]
        )
        r += ">"
        return r


class List(list):
    _length = None
    _itemtype = None

    def serialize(self):
        assert self._length is None or len(self) == self._length
        return b"".join([self._itemtype(i).serialize() for i in self])

    @classmethod
    def deserialize(cls, data):
        assert cls._itemtype is not None
        r = cls()
        while data:
            item, data = cls._itemtype.deserialize(data)
            r.append(item)
        return r, data


class FixedList(List):
    _length = None
    _itemtype = None

    @classmethod
    def deserialize(cls, data):
        assert cls._itemtype is not None
        r = cls()
        for i in range(cls._length):
            item, data = cls._itemtype.deserialize(data)
            r.append(item)
        return r, data


class EUI64(FixedList):
    _length = 8
    _itemtype = uint8_t

    def __repr__(self):
        return ":".join("%02x" % i for i in self[::-1])

    def __hash__(self):
        return hash(repr(self))


class HexRepr:
    def __repr__(self):
        return ("0x{:0" + str(self._size * 2) + "x}").format(self)

    def __str__(self):
        return ("0x{:0" + str(self._size * 2) + "x}").format(self)


class GroupId(HexRepr, uint16_t):
    pass


class NWK(HexRepr, uint16_t):
    pass


class PanId(HexRepr, uint16_t):
    pass


class ExtendedPanId(EUI64):
    pass


class DeconzAddress(Struct):
    _fields = [
        # The address format (AddressMode)
        ("address_mode", ADDRESS_MODE),
        ("address", EUI64),
    ]

    @classmethod
    def deserialize(cls, data):
        r = cls()
        mode, data = ADDRESS_MODE.deserialize(data)
        r.address_mode = mode
        if mode in [ADDRESS_MODE.GROUP, ADDRESS_MODE.NWK, ADDRESS_MODE.NWK_AND_IEEE]:
            r.address, data = NWK.deserialize(data)
        elif mode == ADDRESS_MODE.IEEE:
            r.address, data = EUI64.deserialize(data)
        if mode == ADDRESS_MODE.NWK_AND_IEEE:
            r.ieee, data = EUI64.deserialize(data)
        return r, data

    def serialize(self):
        r = super().serialize()
        if self.address_mode == ADDRESS_MODE.NWK_AND_IEEE:
            r += self.ieee.serialize()
        return r


class AddressEndpoint(Struct):
    _fields = [
        # The address format (AddressMode)
        ("address_mode", ADDRESS_MODE),
        ("address", EUI64),
        ("endpoint", uint8_t),
    ]

    @classmethod
    def deserialize(cls, data):
        r = cls()
        mode, data = ADDRESS_MODE.deserialize(data)
        r.address_mode = mode
        a = e = None
        if mode == ADDRESS_MODE.GROUP:
            a, data = GroupId.deserialize(data)
        elif mode == ADDRESS_MODE.NWK:
            a, data = NWK.deserialize(data)
        elif mode == ADDRESS_MODE.IEEE:
            a, data = EUI64.deserialize(data)
        setattr(r, cls._fields[1][0], a)
        if mode in [ADDRESS_MODE.NWK, ADDRESS_MODE.IEEE]:
            e, data = uint8_t.deserialize(data)
        setattr(r, cls._fields[2][0], e)
        return r, data

    def serialize(self):
        r = uint8_t(self.address_mode).serialize()
        if self.address_mode == ADDRESS_MODE.NWK:
            r += NWK(self.address).serialize()
        elif self.address_mode == ADDRESS_MODE.GROUP:
            r += GroupId(self.address).serialize()
        elif self.address_mode == ADDRESS_MODE.IEEE:
            r += EUI64(self.address).serialize()
        if self.address_mode in (ADDRESS_MODE.NWK, ADDRESS_MODE.IEEE):
            r += uint8_t(self.endpoint).serialize()
        return r


class Key(FixedList):
    _itemtype = uint8_t
    _length = 16


class Repr:
    def __repr__(self) -> str:
        r = '<%s ' % (self.__class__.__name__,)
        r += ' '.join(
            ['%s=%s' % (f, getattr(self, f, None)) for f in vars(self)]
        )
        r += '>'
        return r


class Timeouts:
    SREQ = 6000
    reset = 30000
    default = 10000


class ZnpVersion(uint8_t, enum.Enum):
    zStack12 = 0
    zStack3x0 = 1
    zStack30x = 2


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
    SAPI = 6
    UTIL = 7
    DEBUG = 8
    APP = 9
    APP_CNF = 15
    GREENPOWER = 21

    @staticmethod
    def from_cluster(profile, cluster):
        if cluster.__class__ == t.ZDOCmd:
            return Subsystem.ZDO

        if profile == zha.PROFILE_ID:
            return Subsystem.AF

        raise TODO('from_cluster %s', cluster)


class ParameterType(uint8_t, enum.Enum):
    UINT8 = 0
    UINT16 = 1
    UINT32 = 2
    IEEEADDR = 3

    BUFFER = 4
    BUFFER8 = 5
    BUFFER16 = 6
    BUFFER18 = 7
    BUFFER32 = 8
    BUFFER42 = 9
    BUFFER100 = 10

    LIST_UINT8 = 11
    LIST_UINT16 = 12
    LIST_ROUTING_TABLE = 13
    LIST_BIND_TABLE = 14
    LIST_NEIGHBOR_LQI = 15
    LIST_NETWORK = 16
    LIST_ASSOC_DEV = 17

    INT8 = 18


class NetworkOptions:
    def __init__(self) -> None:
        self.networkKeyDistribute = False
        self.networkKey = [1, 3, 5, 7, 9, 11, 13, 15, 0, 2, 4, 6, 8, 10, 12, 13]
        self.panID = 0x1a62
        self.extendedPanID = [0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD]
        self.channelList = [11]

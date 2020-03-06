import enum

from zigpy.types import uint8_t


class Repr:
    def __repr__(self) -> str:
        r = "<%s " % (self.__class__.__name__,)
        r += " ".join(["%s=%s" % (f, getattr(self, f, None)) for f in vars(self)])
        r += ">"
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

    def is_buffer(type):
        return (
            type == ParameterType.BUFFER
            or type == ParameterType.BUFFER8
            or type == ParameterType.BUFFER16
            or type == ParameterType.BUFFER18
            or type == ParameterType.BUFFER32
            or type == ParameterType.BUFFER42
            or type == ParameterType.BUFFER100
        )


class NetworkOptions:
    def __init__(self) -> None:
        self.networkKeyDistribute = False
        self.networkKey = [1, 3, 5, 7, 9, 11, 13, 15, 0, 2, 4, 6, 8, 10, 12, 13]
        self.panID = 0x1A62
        self.extendedPanID = [0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD]
        self.channelList = [11]

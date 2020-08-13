import enum

import zigpy.config
import zigpy.types as t


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


class AddressMode(t.uint8_t, enum.Enum):
    ADDR_NOT_PRESENT = 0
    ADDR_GROUP = 1
    ADDR_16BIT = 2
    ADDR_64BIT = 3
    ADDR_BROADCAST = 15


class LedMode(t.uint8_t, enum.Enum):
    Off = 0
    On = 1
    Blink = 2
    Flash = 3
    Toggle = 4


class ZnpVersion(t.uint8_t, enum.Enum):
    zStack12 = 0
    zStack3x0 = 1
    zStack30x = 2


class CommandType(t.uint8_t, enum.Enum):
    POLL = 0
    SREQ = 1
    AREQ = 2
    SRSP = 3


class Subsystem(t.uint8_t, enum.Enum):
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


class ParameterType(t.uint8_t, enum.Enum):
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


class NetworkOptions(Repr):
    networkKey: t.KeyData
    panID: t.PanId
    extendedPanID: t.ExtendedPanId
    channelList: t.Channels

    def __init__(self, config: zigpy.config.SCHEMA_NETWORK) -> None:
        self.networkKeyDistribute = False
        self.networkKey = config[zigpy.config.CONF_NWK_KEY] or (
            zigpy.config.cv_key([1, 3, 5, 7, 9, 11, 13, 15, 0, 2, 4, 6, 8, 10, 12, 13])
        )
        self.panID = config[zigpy.config.CONF_NWK_PAN_ID] or t.PanId(0x1A62)
        self.extendedPanID = config[zigpy.config.CONF_NWK_EXTENDED_PAN_ID] or (
            t.ExtendedPanId([0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD])
        )
        self.channelList = (
            config[zigpy.config.CONF_NWK_CHANNELS] or t.Channels.from_channel_list([11])
        )

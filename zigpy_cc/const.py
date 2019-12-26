class ResetType:
    HARD = 0
    SOFT = 1


class System:
    resetType = ResetType


class DeviceLogicalType:
    COORDINATOR = 0
    ROUTER = 1
    ENDDEVICE = 2
    COMPLEX_DESC_AVAIL = 4
    USER_DESC_AVAIL = 8
    RESERVED1 = 16
    RESERVED2 = 32
    RESERVED3 = 64
    RESERVED4 = 128


class ZDO:
    deviceLogicalType = DeviceLogicalType


class Constants:
    SYS = System
    ZDO = ZDO

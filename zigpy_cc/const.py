import enum


class ResetType(enum.IntEnum):
    HARD = 0
    SOFT = 1


class System:
    resetType = ResetType


class DeviceLogicalType(enum.IntEnum):
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


class networkLatencyReq(enum.IntEnum):
    NO_LATENCY_REQS = 0
    FAST_BEACONS = 1
    SLOW_BEACONS = 2


class AF:
    networkLatencyReq = networkLatencyReq


class Constants:
    AF = AF
    SYS = System
    ZDO = ZDO

from zigpy.types import EUI64, Group, NWK

import zigpy_cc.types as t
from zigpy_cc.buffalo import Buffalo, BuffaloOptions

ieeeAddr1 = {
    "string": EUI64.convert("ae:44:01:12:00:4b:12:00"),
    "hex": bytes([0x00, 0x12, 0x4B, 0x00, 0x12, 0x01, 0x44, 0xAE]),
}

ieeeAddr2 = {
    "string": EUI64.convert("af:44:01:12:00:5b:12:00"),
    "hex": bytes([0x00, 0x12, 0x5B, 0x00, 0x12, 0x01, 0x44, 0xAF]),
}


def test_write_ieee():
    data_out = Buffalo(b"")
    data_out.write_parameter(t.ParameterType.IEEEADDR, ieeeAddr1["string"], {})
    assert ieeeAddr1["hex"] == data_out.buffer


def test_write_ieee2():
    data_out = Buffalo(b"")
    data_out.write_parameter(t.ParameterType.IEEEADDR, ieeeAddr2["string"], {})
    assert ieeeAddr2["hex"] == data_out.buffer


def test_write_ieee_group():
    data_out = Buffalo(b"")
    data_out.write_parameter(t.ParameterType.IEEEADDR, Group(2), {})
    assert b"\x02\x00\x00\x00\x00\x00\x00\x00" == data_out.buffer


def test_read_ieee():
    data_in = Buffalo(ieeeAddr1["hex"])
    actual = data_in.read_parameter(t.ParameterType.IEEEADDR, {})
    assert ieeeAddr1["string"] == actual


def test_read_ieee2():
    data_in = Buffalo(ieeeAddr2["hex"])
    actual = data_in.read_parameter(t.ParameterType.IEEEADDR, {})
    assert ieeeAddr2["string"] == actual


def test_list_nighbor_lqi():
    value = [
        {
            "extPanId": EUI64.convert("d8:dd:dd:dd:d0:dd:ed:dd"),
            "extAddr": EUI64.convert("00:15:8d:00:04:21:dc:b3"),
            "nwkAddr": NWK(0xE961),
            "deviceType": 1,
            "rxOnWhenIdle": 2,
            "relationship": 2,
            "permitJoin": 2,
            "depth": 255,
            "lqi": 69,
        }
    ]
    data_out = Buffalo(b"")
    data_out.write_parameter(t.ParameterType.LIST_NEIGHBOR_LQI, value, {})
    assert (
        b"\xdd\xed\xdd\xd0\xdd\xdd\xdd\xd8\xb3\xdc!\x04\x00\x8d\x15\x00a\xe9)\x02\xffE"
        == data_out.buffer
    )

    data_in = Buffalo(data_out.buffer)
    options = BuffaloOptions()
    options.length = len(value)
    act = data_in.read_parameter(t.ParameterType.LIST_NEIGHBOR_LQI, options)
    assert value == act

import zigpy_cc.types as t
from zigpy.types import EUI64

from zigpy_cc.buffalo import Buffalo

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


def test_read_ieee():
    data_in = Buffalo(ieeeAddr1["hex"])
    actual = data_in.read_parameter(t.ParameterType.IEEEADDR, {})
    assert ieeeAddr1["string"] == actual


def test_read_ieee2():
    data_in = Buffalo(ieeeAddr2["hex"])
    actual = data_in.read_parameter(t.ParameterType.IEEEADDR, {})
    assert ieeeAddr2["string"] == actual

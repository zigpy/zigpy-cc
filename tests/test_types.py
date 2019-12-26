from zigpy_cc import uart
from zigpy_cc.zpi_object import ZpiObject


def test_from_unpi_frame():
    frame = uart.UnpiFrame(3, 1, 2, b"\x02\x00\x02\x06\x03\x90\x154\x01")
    extra = {
        'maintrel': 3,
        'majorrel': 2,
        'minorrel': 6,
        'product': 0,
        'revision': 20190608,
        'transportrev': 2,
    }

    obj = ZpiObject.from_unpi_frame(frame)
    assert obj.command == 'version'
    assert obj.payload == extra

    assert str(obj.to_unpi_frame()) == str(frame)

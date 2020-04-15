from asynctest import mock

import pytest
import serial_asyncio

from zigpy_cc import uart
import zigpy_cc.config

DEVICE_CONFIG = zigpy_cc.config.SCHEMA_DEVICE(
    {zigpy_cc.config.CONF_DEVICE_PATH: "/dev/null"}
)


def eq(a, b):
    assert str(a) == str(b)


@pytest.fixture(scope="function")
def gw():
    gw = uart.Gateway(mock.MagicMock())
    gw._transport = mock.MagicMock()
    return gw


@pytest.mark.asyncio
async def test_connect(monkeypatch):
    api = mock.MagicMock()
    transport = mock.MagicMock()

    async def mock_conn(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, transport)
        return None, protocol

    monkeypatch.setattr(serial_asyncio, "create_serial_connection", mock_conn)

    await uart.connect(DEVICE_CONFIG, api)


def test_write(gw):
    data = b"\x00"
    gw.write(data)
    assert gw._transport.write.call_count == 1
    assert gw._transport.write.called_once_with(data)


def test_close(gw):
    gw.close()
    assert gw._transport.close.call_count == 1


def test_data_received_chunk_frame(gw):
    data = b"\xfe\x0ea\x02\x02\x00\x02\x06\x03\x90\x154\x01\x02\x00\x00\x00\x00\xda"
    gw.data_received(data[:-4])
    assert gw._api.data_received.call_count == 0
    gw.data_received(data[-4:])
    assert gw._api.data_received.call_count == 1
    eq(
        gw._api.data_received.call_args[0][0],
        uart.UnpiFrame(3, 1, 2, data[4:-1], 14, 218),
    )


def test_data_received_full_frame(gw):
    data = b"\xfe\x0ea\x02\x02\x00\x02\x06\x03\x90\x154\x01\x02\x01\x00\x00\x00\xdb"
    gw.data_received(data)
    assert gw._api.data_received.call_count == 1
    eq(
        gw._api.data_received.call_args[0][0],
        uart.UnpiFrame(3, 1, 2, data[4:-1], 14, 219),
    )


def test_data_received_incomplete_frame(gw):
    data = b"~\x00\x00"
    gw.data_received(data)
    assert gw._api.data_received.call_count == 0


def test_data_received_runt_frame(gw):
    data = b"\x02\x44\xC0"
    gw.data_received(data)
    assert gw._api.data_received.call_count == 0


def test_data_received_extra(gw):
    data = (
        b"\xfe\x0ea\x02\x02\x00\x02\x06\x03\x90\x154\x01\x02\x01\x00\x00\x00\xdb"
        b"\xfe\x00"
    )
    gw.data_received(data)
    assert gw._api.data_received.call_count == 1
    assert gw._parser.buffer == b"\xfe\x00"


def test_data_received_wrong_checksum(gw):
    data = b"\xfe\x0ea\x02\x02\x00\x02\x06\x03\x90\x154\x01\x02\x01\x00\x00\x00\xdc"
    gw.data_received(data)
    assert gw._api.data_received.call_count == 0


@pytest.mark.skip("TODO")
def test_unescape(gw):
    data = b"\x00\xDB\xDC\x00\xDB\xDD\x00\x00\x00"
    data_unescaped = b"\x00\xC0\x00\xDB\x00\x00\x00"
    r = gw._unescape(data)
    assert r == data_unescaped


@pytest.mark.skip("TODO")
def test_unescape_error(gw):
    data = b"\x00\xDB\xDC\x00\xDB\xDD\x00\x00\x00\xDB"
    r = gw._unescape(data)
    assert r is None


@pytest.mark.skip("TODO")
def test_escape(gw):
    data = b"\x00\xC0\x00\xDB\x00\x00\x00"
    data_escaped = b"\x00\xDB\xDC\x00\xDB\xDD\x00\x00\x00"
    r = gw._escape(data)
    assert r == data_escaped


def test_checksum():
    data = b"\x07\x01\x00\x08\x00\xaa\x00\x02"
    checksum = 166
    r = uart.UnpiFrame.calculate_checksum(data)
    assert r == checksum


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "control, xonxoff, rtscts",
    (("software", True, False), ("hardware", False, True), (None, False, False)),
)
@mock.patch.object(serial_asyncio, "create_serial_connection")
async def test_flow_control(conn_mock, control, xonxoff, rtscts):
    async def set_connected(loop, proto_factory, **kwargs):
        proto_factory()._connected_future.set_result(True)
        return mock.sentinel.a, mock.MagicMock()

    conn_mock.side_effect = set_connected
    await uart.connect(
        {**DEVICE_CONFIG, zigpy_cc.config.CONF_FLOW_CONTROL: control}, mock.MagicMock()
    )
    assert conn_mock.call_args[1]["xonxoff"] == xonxoff
    assert conn_mock.call_args[1]["rtscts"] == rtscts

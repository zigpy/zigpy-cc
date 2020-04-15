import asyncio

from asynctest import CoroutineMock, mock
import pytest
import serial

from zigpy_cc import types as t, uart
import zigpy_cc.api
import zigpy_cc.config
from zigpy_cc.definition import Definition
import zigpy_cc.exception
import zigpy_cc.uart
from zigpy_cc.uart import UnpiFrame
from zigpy_cc.zpi_object import ZpiObject

DEVICE_CONFIG = zigpy_cc.config.SCHEMA_DEVICE(
    {zigpy_cc.config.CONF_DEVICE_PATH: "/dev/null"}
)


@pytest.fixture
def api():
    api = zigpy_cc.api.API(DEVICE_CONFIG)
    api._uart = mock.MagicMock()
    return api


def test_set_application(api):
    api.set_application(mock.sentinel.app)
    assert api._app == mock.sentinel.app


@pytest.mark.asyncio
async def test_connect(monkeypatch):
    api = zigpy_cc.api.API(DEVICE_CONFIG)
    monkeypatch.setattr(
        uart, "connect", mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
    )
    await api.connect()


def test_close(api):
    api._uart.close = mock.MagicMock()
    uart = api._uart
    api.close()
    assert uart.close.call_count == 1


@pytest.mark.skip("TODO")
def test_commands():
    for cmd, cmd_opts in zigpy_cc.api.RX_COMMANDS.items():
        assert len(cmd_opts) == 2
        schema, solicited = cmd_opts
        assert isinstance(cmd, int) is True
        assert isinstance(schema, tuple) is True
        assert isinstance(solicited, bool)

    for cmd, schema in zigpy_cc.api.TX_COMMANDS.items():
        assert isinstance(cmd, int) is True
        assert isinstance(schema, tuple) is True


@pytest.mark.skip("TODO")
@pytest.mark.asyncio
async def test_command(api, monkeypatch):
    def mock_api_frame():
        return mock.sentinel.api_frame_data

    def mock_obj(subsystem, command, payload):
        obj = mock.sentinel.zpi_object
        obj.to_unpi_frame = mock.MagicMock(side_effect=mock_api_frame)
        return obj

    api._create_obj = mock.MagicMock(side_effect=mock_obj)
    api._uart.send = mock.MagicMock()

    async def mock_fut():
        return mock.sentinel.cmd_result

    monkeypatch.setattr(asyncio, "Future", mock_fut)

    for subsystem, commands in Definition.items():
        for cmd in commands:
            ret = await api._command(subsystem, cmd["name"], mock.sentinel.cmd_data)
            assert ret is mock.sentinel.cmd_result
            # assert api._api_frame.call_count == 1
            # assert api._api_frame.call_args[0][0] == cmd
            # assert api._api_frame.call_args[0][1] == mock.sentinel.cmd_data
            assert api._uart.send.call_count == 1
            # assert api._uart.send.call_args[0][0] == mock.sentinel.api_frame_data
            # api._api_frame.reset_mock()
            api._uart.send.reset_mock()


@pytest.mark.skip("TODO")
@pytest.mark.asyncio
async def test_command_timeout(api, monkeypatch):
    def mock_api_frame():
        return mock.sentinel.api_frame_data

    def mock_obj(subsystem, command, payload):
        obj = mock.sentinel.zpi_object
        obj.to_unpi_frame = mock.MagicMock(side_effect=mock_api_frame)
        return obj

    api._create_obj = mock.MagicMock(side_effect=mock_obj)
    api._uart.send = mock.MagicMock()

    monkeypatch.setattr(zigpy_cc.api, "COMMAND_TIMEOUT", 0.1)

    for subsystem, commands in Definition.items():
        for cmd in commands:
            with pytest.raises(asyncio.TimeoutError):
                await api._command(subsystem, cmd["name"], mock.sentinel.cmd_data)
            # assert api._api_frame.call_count == 1
            # assert api._api_frame.call_args[0][0] == cmd
            # assert api._api_frame.call_args[0][1] == mock.sentinel.cmd_data
            assert api._uart.send.call_count == 1
            # assert api._uart.send.call_args[0][0] == mock.sentinel.api_frame_data
            # api._api_frame.reset_mock()
            api._uart.send.reset_mock()


@pytest.mark.skip("TODO")
def test_api_frame(api):
    addr = t.DeconzAddressEndpoint()
    addr.address_mode = t.ADDRESS_MODE.NWK
    addr.address = t.uint8_t(0)
    addr.endpoint = t.uint8_t(0)
    for cmd, schema in zigpy_cc.api.TX_COMMANDS.items():
        if schema:
            args = [
                addr if isinstance(a(), t.DeconzAddressEndpoint) else a()
                for a in schema
            ]
            api._api_frame(cmd, *args)
        else:
            api._api_frame(cmd)


@pytest.mark.skip("TODO")
def test_data_received(api, monkeypatch):
    monkeypatch.setattr(
        t,
        "deserialize",
        mock.MagicMock(return_value=(mock.sentinel.deserialize_data, b"")),
    )
    my_handler = mock.MagicMock()

    data = UnpiFrame(3, 1, 2, b"\x02\x00\x02\x06\x03\x90\x154\x01\x02\x01\x00\x00\x00")
    setattr(api, "_handle_version", my_handler)
    api._awaiting[0] = mock.MagicMock()
    api.data_received(data)
    # assert t.deserialize.call_count == 1
    # assert t.deserialize.call_args[0][0] == payload
    assert my_handler.call_count == 1
    assert str(my_handler.call_args[0][0]) == str(
        ZpiObject(
            3,
            1,
            "version",
            2,
            {
                "transportrev": 2,
                "product": 0,
                "majorrel": 2,
                "minorrel": 6,
                "maintrel": 3,
                "revision": 20190608,
            },
            [],
        )
    )


"""
zigpy_cc.api DEBUG <-- SREQ ZDO nodeDescReq {'dstaddr': 53322, 'nwkaddrofinterest': 0}
zigpy_cc.api DEBUG --> SRSP ZDO nodeDescReq {'status': 0}
zigpy_cc.api DEBUG --> AREQ ZDO nodeDescRsp {'srcaddr': 53322, 'status': 128,
    'nwkaddr': 0, 'logicaltype_cmplxdescavai_userdescavai': 0, 'apsflags_freqband': 0,
    'maccapflags': 0, 'manufacturercode': 0, 'maxbuffersize': 0, 'maxintransfersize': 0,
    'servermask': 0, 'maxouttransfersize': 0, 'descriptorcap': 0}
"""


@pytest.mark.asyncio
async def test_node_desc(api: zigpy_cc.api.API):
    api._uart.send = mock.MagicMock()

    fut = api.request(5, "nodeDescReq", {"dstaddr": 53322, "nwkaddrofinterest": 0})
    fut = asyncio.ensure_future(fut)

    async def asd():
        api.data_received(UnpiFrame(3, 5, 2, b"\x00"))
        pass

    await asyncio.wait([fut, asd()], timeout=0.1)

    assert api._uart.send.call_count == 1
    assert fut.done()
    assert "SRSP ZDO nodeDescReq tsn: None {'status': 0}" == str(fut.result())


#
# @pytest.mark.parametrize(
#     "protocol_ver, firmware_version, flags",
#     [
#         (0x010A, 0x123405DD, 0x01),
#         (0x010B, 0x123405DD, 0x04),
#         (0x010A, 0x123407DD, 0x01),
#         (0x010B, 0x123407DD, 0x01),
#     ],
# )
# @pytest.mark.asyncio
# async def test_version(protocol_ver, firmware_version, flags, api):
#     api.read_parameter = mock.MagicMock()
#     api.read_parameter.side_effect = asyncio.coroutine(
#         mock.MagicMock(return_value=[protocol_ver])
#     )
#     api._command = mock.MagicMock()
#     api._command.side_effect = asyncio.coroutine(
#         mock.MagicMock(return_value=[firmware_version])
#     )
#     r = await api.version()
#     assert r == firmware_version
#     assert api._aps_data_ind_flags == flags
#
#
# def test_handle_version(api):
#     api._handle_version([mock.sentinel.version])


@pytest.mark.asyncio
@mock.patch.object(zigpy_cc.uart, "connect")
async def test_api_new(conn_mck):
    """Test new class method."""
    api = await zigpy_cc.api.API.new(mock.sentinel.application, DEVICE_CONFIG)
    assert isinstance(api, zigpy_cc.api.API)
    assert conn_mck.call_count == 1
    assert conn_mck.await_count == 1


@pytest.mark.asyncio
@mock.patch.object(zigpy_cc.api.API, "version", new_callable=CoroutineMock)
@mock.patch.object(uart, "connect")
async def test_probe_success(mock_connect, mock_version):
    """Test device probing."""

    res = await zigpy_cc.api.API.probe(DEVICE_CONFIG)
    assert res is True
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_connect.call_args[0][0] == DEVICE_CONFIG
    assert mock_version.call_count == 1
    assert mock_connect.return_value.close.call_count == 1


@pytest.mark.asyncio
@mock.patch.object(zigpy_cc.api.API, "version", side_effect=asyncio.TimeoutError)
@mock.patch.object(uart, "connect")
@pytest.mark.parametrize("exception", (asyncio.TimeoutError, serial.SerialException))
async def test_probe_fail(mock_connect, mock_version, exception):
    """Test device probing fails."""

    mock_version.side_effect = exception
    mock_connect.reset_mock()
    mock_version.reset_mock()
    res = await zigpy_cc.api.API.probe(DEVICE_CONFIG)
    assert res is False
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_connect.call_args[0][0] == DEVICE_CONFIG
    assert mock_version.call_count == 1
    assert mock_connect.return_value.close.call_count == 1

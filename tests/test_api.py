import asyncio
from unittest import mock

import pytest

import zigpy_cc.api
import zigpy_cc.exception
from zigpy_cc import types as t, uart
from zigpy_cc.definition import Definition
from zigpy_cc.uart import UnpiFrame
from zigpy_cc.zpi_object import ZpiObject


@pytest.fixture
def api():
    api = zigpy_cc.api.API()
    api._uart = mock.MagicMock()
    return api


def test_set_application(api):
    api.set_application(mock.sentinel.app)
    assert api._app == mock.sentinel.app


@pytest.mark.asyncio
async def test_connect(monkeypatch):
    api = zigpy_cc.api.API()
    dev = mock.MagicMock()
    monkeypatch.setattr(
        uart, "connect", mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
    )
    await api.connect(dev, 115200)


def test_close(api):
    api._uart.close = mock.MagicMock()
    api.close()
    assert api._uart.close.call_count == 1


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
    assert str(my_handler.call_args[0][0]) == str(ZpiObject(3, 1, "version", 2,
                                                            {'transportrev': 2, 'product': 0, 'majorrel': 2,
                                                             'minorrel': 6, 'maintrel': 3, 'revision': 20190608}, []))


'''
zigpy_cc.api DEBUG <-- SREQ ZDO nodeDescReq {'dstaddr': 53322, 'nwkaddrofinterest': 0}
zigpy_cc.api DEBUG --> SRSP ZDO nodeDescReq {'status': 0}
zigpy_cc.api DEBUG --> AREQ ZDO nodeDescRsp {'srcaddr': 53322, 'status': 128, 'nwkaddr': 0, 'logicaltype_cmplxdescavai_userdescavai': 0, 'apsflags_freqband': 0, 'maccapflags': 0, 'manufacturercode': 0, 'maxbuffersize': 0, 'maxintransfersize': 0, 'servermask': 0, 'maxouttransfersize': 0, 'descriptorcap': 0}
'''


@pytest.mark.skip
@pytest.mark.asyncio
async def test_node_desc(api: zigpy_cc.api.API, monkeypatch):
    async def mock_fut():
        res = mock.sentinel.cmd_result
        res.payload = {}

        return res

    # monkeypatch.setattr(asyncio, "Future", mock_fut)
    api._uart.send = mock.MagicMock()

    fut = api.request(5, 'nodeDescReq', {'dstaddr': 53322, 'nwkaddrofinterest': 0})

    api.data_received(UnpiFrame(3, 5, 2, b'\x00'))
    payload = {
        'srcaddr': 53322, 'status': 128, 'nwkaddr': 0, 'logicaltype_cmplxdescavai_userdescavai': 0,
        'apsflags_freqband': 0, 'maccapflags': 0, 'manufacturercode': 0, 'maxbuffersize': 0, 'maxintransfersize': 0,
        'servermask': 0, 'maxouttransfersize': 0, 'descriptorcap': 0
    }
    api.data_received(api._create_obj(5, 'nodeDescRsp', payload).to_unpi_frame())

    res = await asyncio.wait_for(fut, 0.1)

    assert res == ""

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

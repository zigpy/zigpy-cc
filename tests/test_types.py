# flake8: noqa: E501
from unittest import mock

from zigpy.zcl.clusters.general import PowerConfiguration

import zigpy_cc.types as t
from zigpy.zcl import Cluster
from zigpy.types import NWK, EUI64
from zigpy.zdo.types import ZDOCmd
from zigpy_cc import uart
from zigpy_cc.zpi_object import ZpiObject

DIMMER = '0x000b57fffe27783c'
COORDINATOR = '0x00124b0018ed250c'


def test_incoming_msg():
    """
    zigpy_cc.api DEBUG --> AREQ AF incomingMsg
    {'groupid': 0, 'clusterid': 0, 'srcaddr': 28294, 'srcendpoint': 1, 'dstendpoint': 1,
    'wasbroadcast': 0, 'linkquality': 115, 'securityuse': 0, 'timestamp': 15812278,
    'transseqnumber': 0, 'len': 25, 'data': b'\x18\x00\n\x05\x00B\x12lumi.sensor_switch'
    }

    ZLC msg not ZDO
    """
    epmock = mock.MagicMock()

    cls = Cluster.from_id(epmock, 0)
    hdr, data = cls.deserialize(b"\x18\x00\n\x05\x00B\x12lumi.sensor_switch")
    assert (
            str(data) == "[[<Attribute attrid=5 value="
                         "<TypeValue type=CharacterString, value=lumi.sensor_switch>>]]"
    )
    assert (
            str(
                hdr) == "<ZCLHeader frame_control=<FrameControl frame_type=GLOBAL_COMMAND "
                        "manufacturer_specific=False is_reply=False disable_default_response=True> "
                        "manufacturer=None tsn=0 command_id=Command.Report_Attributes>"
    )


def test_incoming_msg2():
    """
    zigpy_cc.api DEBUG --> AREQ AF incomingMsg
    {'groupid': 0, 'clusterid': 0, 'srcaddr': 4835, 'srcendpoint': 1, 'dstendpoint': 1,
    'wasbroadcast': 0, 'linkquality': 110, 'securityuse': 0, 'timestamp': 8255669,
    'transseqnumber': 0, 'len': 29,
    'data': b'\x1c4\x12\x02\n\x02\xffL\x06\x00\x10\x00!\xce\x0b!\xa8\x01$
              \x00\x00\x00\x00\x00!\xbdJ ]'}
    """
    epmock = mock.MagicMock()

    cls = Cluster.from_id(epmock, 0)
    hdr, data = cls.deserialize(
        b"\x1c\x34\x12\x02\x0a\x02\xffL\x06\x00\x10\x00!\xce\x0b!\xa8\x01$"
        b"\x00\x00\x00\x00\x00!\xbdJ ]"
    )
    assert (
            str(
                hdr) == "<ZCLHeader frame_control=<FrameControl frame_type=GLOBAL_COMMAND "
                        "manufacturer_specific=True is_reply=False disable_default_response=True> "
                        "manufacturer=4660 tsn=2 command_id=Command.Report_Attributes>"
    )


def test_from_unpi_frame():
    frame = uart.UnpiFrame(3, 1, 2, b"\x02\x00\x02\x06\x03\x90\x154\x01")
    extra = {
        "maintrel": 3,
        "majorrel": 2,
        "minorrel": 6,
        "product": 0,
        "revision": 20190608,
        "transportrev": 2,
    }

    obj = ZpiObject.from_unpi_frame(frame)
    assert obj.command == "version"
    assert obj.payload == extra

    assert str(obj.to_unpi_frame()) == str(frame)


def test_from_unpi_frame2():
    frame = uart.UnpiFrame(
        2,
        4,
        129,
        b"\x00\x00\x01\x00\xbbm\x01\x01\x00s\x00YC3\x00\x00\t\x18\x01\x01\x04\x00\x86"
        b"\x05\x00\x86\xbbm\x1d",
    )

    obj = ZpiObject.from_unpi_frame(frame)

    assert (
            "AREQ AF incomingMsg tsn: None {'groupid': 0, 'clusterid': 1, "
            "'srcaddr': 0x6dbb, 'srcendpoint': 1, 'dstendpoint': 1, 'wasbroadcast': 0,"
            " 'linkquality': 115, 'securityuse': 0, 'timestamp': 3359577, "
            "'transseqnumber': 0, 'len': 9, "
            "'data': b'\\x18\\x01\\x01\\x04\\x00\\x86\\x05\\x00\\x86'}" == str(obj)
    )


"""
zigbee-herdsman:adapter:zStack:znp:SREQ --> AF - dataRequest
{
    "dstaddr":44052,
    "destendpoint":1,
    "srcendpoint":1,
    "clusterid":0,
    "transid":1,
    "options":0,
    "radius":30,
    "len":9,
    "data":{
        "type":"Buffer",
        "data":[16,2,0,5,0,4,0,7,0]
    }
}

zigbee-herdsman:adapter:zStack:znp:SRSP <-- AF - dataRequest
{"status":0} +135ms

zigbee-herdsman:adapter:zStack:znp:AREQ <-- AF - dataConfirm
{"status":0,"endpoint":1,"transid":1} +62ms

zigbee-herdsman:adapter:zStack:znp:AREQ <-- AF - incomingMsg
{
    "groupid":0,
    "clusterid":0,
    "srcaddr":44052,
    "srcendpoint":1,
    "dstendpoint":1,
    "wasbroadcast":0,
    "linkquality":78,
    "securityuse":0,
    "timestamp":2206697,
    "transseqnumber":0,
    "len":55,
    "data":{
        "type":"Buffer",
        "data":[24,2,1,5,0,0,66,23,84,82,65,68,70,82,73,32,119,105,114,101,108,101,115,
                115,32,100,105,109,109,101,114,4,0,0,66,14,73,75,69,65,32,111,102,32,83,
                119,101,100,101,110,7,0,0,48,3]
    }
}

zigbee-herdsman:controller:log Received 'zcl' data '
{
    "frame":{
        "Header":{
            "frameControl":{"frameType":0,"manufacturerSpecific":false,"direction":1,
                "disableDefaultResponse":true},
            "transactionSequenceNumber":2,
            "manufacturerCode":null,
            "commandIdentifier":1
        },
        "Payload":[
            {"attrId":5,"status":0,"dataType":66,"attrData":"TRADFRI wireless dimmer"},
            {"attrId":4,"status":0,"dataType":66,"attrData":"IKEA of Sweden"},
            {"attrId":7,"status":0,"dataType":48,"attrData":3}
        ],
        "Cluster":{
            "ID":0,
            "attributes":{
                "zclVersion":{"ID":0,"type":32,"name":"zclVersion"},
                "appVersion":{"ID":1,"type":32,"name":"appVersion"},
                "stackVersion":{"ID":2,"type":32,"name":"stackVersion"},
                "hwVersion":{"ID":3,"type":32,"name":"hwVersion"},
                "manufacturerName":{"ID":4,"type":66,"name":"manufacturerName"},
                "modelId":{"ID":5,"type":66,"name":"modelId"},
                "dateCode":{"ID":6,"type":66,"name":"dateCode"},
                "powerSource":{"ID":7,"type":48,"name":"powerSource"},
                "appProfileVersion":{"ID":8,"type":48,"name":"appProfileVersion"},
                "swBuildId":{"ID":16384,"type":66,"name":"swBuildId"},
                "locationDesc":{"ID":16,"type":66,"name":"locationDesc"},
                "physicalEnv":{"ID":17,"type":48,"name":"physicalEnv"},
                "deviceEnabled":{"ID":18,"type":16,"name":"deviceEnabled"},
                "alarmMask":{"ID":19,"type":24,"name":"alarmMask"},
                "disableLocalConfig":{"ID":20,"type":24,"name":"disableLocalConfig"}
            },
            "name":"genBasic",
            "commands":{
                "resetFactDefault":{"ID":0,"parameters":[],"name":"resetFactDefault"}
            },
            "commandsResponse":{}
        }
    },
    "address":44052,
    "endpoint":1,
    "linkquality":78,
    "groupID":0
}
"""


def test_from_unpi_frame3():
    payload = {
        "groupid": 0,
        "clusterid": 0,
        "srcaddr": 44052,
        "srcendpoint": 1,
        "dstendpoint": 1,
        "wasbroadcast": 0,
        "linkquality": 78,
        "securityuse": 0,
        "timestamp": 2206697,
        "transseqnumber": 0,
        "len": 55,
        "data": bytes(
            [
                24,
                2,
                1,
                5,
                0,
                0,
                66,
                23,
                84,
                82,
                65,
                68,
                70,
                82,
                73,
                32,
                119,
                105,
                114,
                101,
                108,
                101,
                115,
                115,
                32,
                100,
                105,
                109,
                109,
                101,
                114,
                4,
                0,
                0,
                66,
                14,
                73,
                75,
                69,
                65,
                32,
                111,
                102,
                32,
                83,
                119,
                101,
                100,
                101,
                110,
                7,
                0,
                0,
                48,
                3,
            ]
        ),
    }
    obj = ZpiObject.from_command(t.Subsystem.AF, "incomingMsg", payload)

    assert (
            "AREQ AF incomingMsg tsn: None {'groupid': 0, 'clusterid': 0, "
            "'srcaddr': 44052, 'srcendpoint': 1, 'dstendpoint': 1, 'wasbroadcast': 0, "
            "'linkquality': 78, 'securityuse': 0, 'timestamp': 2206697, "
            "'transseqnumber': 0, 'len': 55, "
            "'data': b'\\x18\\x02\\x01\\x05\\x00\\x00B\\x17TRADFRI wireless dimmer"
            "\\x04\\x00\\x00B\\x0eIKEA of Sweden\\x07\\x00\\x000\\x03'}" == str(obj)
    )


def test_ieee_addr():
    frame = uart.UnpiFrame(
        3, 7, 0, b"\x00\x0c%\xed\x18\x00K\x12\x00\x00\x00\x07\t\x02J\xd0]\x97"
    )
    obj = ZpiObject.from_unpi_frame(frame)

    out = obj.to_unpi_frame()
    assert b"\x00\x0c%\xed\x18\x00K\x12\x00\x00\x00\x07\t\x02J\xd0]\x97" == out.data


"""
zigpy_cc.zigbee.application INFO New device joined: 53322, 00:15:8d:00:02:4b:e5:41
zigpy.application INFO Device 0xd04a (00:15:8d:00:02:4b:e5:41) joined the network
zigpy.zdo DEBUG [0xd04a:zdo] ZDO request ZDOCmd.Device_annce: [0xd04a, 41:e5:4b:02:00:8d:15:00, 132]
zigpy.device INFO [0xd04a] Requesting 'Node Descriptor'
Tries remaining: 2
zigpy.device DEBUG [0xd04a] Extending timeout for 0x03 request
zigpy_cc.zigbee.application DEBUG Sending Zigbee request with tsn 3 under 4 request id, data: b'034ad0'
zigpy_cc.api DEBUG <-- SREQ ZDO nodeDescReq {'dstaddr': 53322, 'nwkaddrofinterest': 0}
zigpy_cc.api DEBUG --> SRSP ZDO nodeDescReq {'status': 0}
zigpy_cc.api DEBUG --> AREQ ZDO nodeDescRsp {'srcaddr': 53322, 'status': 128, 'nwkaddr': 0, 'logicaltype_cmplxdescavai_userdescavai': 0, 'apsflags_freqband': 0, 'maccapflags': 0, 'manufacturercode': 0, 'maxbuffersize': 0, 'maxintransfersize': 0, 'servermask': 0, 'maxouttransfersize': 0, 'descriptorcap': 0}
"""


def test_from_cluster_id():
    profile = 0
    obj = ZpiObject.from_cluster(
        NWK(53322), profile, ZDOCmd.Node_Desc_req, 0, 0, 3, b"\x03\x4a\xd0", 32
    )

    assert (
            "SREQ ZDO nodeDescReq tsn: 3 {'dstaddr': 0xd04a, 'nwkaddrofinterest': 0xd04a}"
            == str(obj)
    )


"""
profile 260
cluster 0
src_ep 1
dst_ep 1
sequence 1
data b'\x00\x0b\x00\x04\x00\x05\x00'
"""


def test_from_cluster_id_ZCL():
    profile = 260
    obj = ZpiObject.from_cluster(
        NWK(53322), profile, 0, 1, 1, 1, b"\x00\x0b\x00\x04\x00\x05\x00", 123
    )

    assert (
            "SREQ AF dataRequest tsn: 1 {'dstaddr': 53322, 'destendpoint': 1, "
            "'srcendpoint': 1, 'clusterid': 0, 'transid': 123, 'options': 0, 'radius': 30, "
            "'len': 7, 'data': b'\\x00\\x0b\\x00\\x04\\x00\\x05\\x00'}" == str(obj)
    )


def test_deser():
    endp = mock.MagicMock()
    power_configuration = PowerConfiguration(endp)
    data = bytes([16, 5, 6, 0, 33, 0, 32, 16, 14, 48, 242, 0])
    hdr, value = power_configuration.deserialize(data)

    assert (
            "<ZCLHeader "
            "frame_control=<FrameControl frame_type=GLOBAL_COMMAND manufacturer_specific=False is_reply=False disable_default_response=True> "
            "manufacturer=None "
            "tsn=5 "
            "command_id=Command.Configure_Reporting>" == str(hdr)
    )
    assert 1 == len(value)
    assert (
            {'direction': False, 'attrid': 33, 'datatype': 32, 'min_interval': 3600,
             'max_interval': 62000, 'reportable_change': 0} == value[0][0].__dict__
    )


def test_bind_req():
    '''
    zigpy_cc.zigbee.application DEBUG request (
        0xbd8b, 0, <ZDOCmd.Bind_req: 0x0021>, 0, 0, 1,
        b"\x01<x'\xfe\xffW\x0b\x00\x01\x08\x00\x03\x0c%\xed\x18\x00K\x12\x00\x01", True, False)
    zigpy_cc.api DEBUG waiting for 1 bindReq
    zigpy_cc.api DEBUG --> SREQ ZDO bindReq tsn: 1 {
        'dstaddr': 0xbd8b, 'srcaddr': 00:0b:57:ff:fe:27:78:3c, 'srcendpoint': 1, 'clusterid': 8, 'dstaddrmode': 3, 'dstaddress': 00:12:4b:00:18:ed:25:0c, 'dstendpoint': 1}
    zigpy_cc.uart DEBUG Send:
        b"\xfe\x17%!\x8b\xbd<x'\xfe\xffW\x0b\x00\x01\x08\x00\x03\x0c%\xed\x18\x00K\x12\x00\x01\x95"

    '''

    data = b"\x02<x'\xfe\xffW\x0b\x00\x01\x08\x00\x03\x0c%\xed\x18\x00K\x12\x00\x01"

    obj = ZpiObject.from_cluster(
        NWK(0x6292), 0, 0x0021, 0, 0, 2, data, 123
    )

    assert (
            "SREQ ZDO bindReq tsn: 2 {"
            "'dstaddr': 0x6292, "
            "'srcaddr': 00:0b:57:ff:fe:27:78:3c, "
            "'srcendpoint': 1, "
            "'clusterid': 8, "
            "'dstaddrmode': 3, "
            "'dstaddress': 00:12:4b:00:18:ed:25:0c, "
            "'dstendpoint': 1}" == str(obj)
    )
    assert (
            bytes(
                [254, 23, 37, 33, 146, 98, 60, 120, 39, 254, 255, 87, 11, 0, 1, 8, 0, 3,
                 12, 37, 237, 24, 0, 75, 18, 0, 1, 83])
            == obj.to_unpi_frame().to_buffer()
    )


def test_bind_req_serialize():
    payload = {"dstaddr": NWK(25234),
               "srcaddr": EUI64(reversed(b'\x00\x0b\x57\xff\xfe\x27\x78\x3c')),
               "srcendpoint": 1,
               "clusterid": 8,
               "dstaddrmode": 3,
               "dstaddress": EUI64(reversed(b'\x00\x12\x4b\x00\x18\xed\x25\x0c')),
               "dstendpoint": 1}
    obj = ZpiObject.from_command(t.Subsystem.ZDO, 'bindReq', payload)
    assert (
            "SREQ ZDO bindReq tsn: None {"
            "'dstaddr': 0x6292, "
            "'srcaddr': 00:0b:57:ff:fe:27:78:3c, "
            "'srcendpoint': 1, "
            "'clusterid': 8, "
            "'dstaddrmode': 3, "
            "'dstaddress': 00:12:4b:00:18:ed:25:0c, "
            "'dstendpoint': 1}" == str(obj)
    )
    assert (
            bytes(
                [254, 23, 37, 33, 146, 98, 60, 120, 39, 254, 255, 87, 11, 0, 1, 8, 0, 3,
                 12, 37, 237, 24, 0, 75, 18, 0, 1, 83])
            == obj.to_unpi_frame().to_buffer()
    )

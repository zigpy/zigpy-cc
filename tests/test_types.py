from unittest import mock

from zigpy.zcl import Cluster

from zigpy.zdo.types import ZDOCmd

from zigpy_cc import uart
from zigpy_cc.types import NWK
from zigpy_cc.zpi_object import ZpiObject

def test_incomming_msg():
    '''
    zigpy_cc.api DEBUG --> AREQ AF incomingMsg
    {'groupid': 0, 'clusterid': 0, 'srcaddr': 28294, 'srcendpoint': 1, 'dstendpoint': 1,
    'wasbroadcast': 0, 'linkquality': 115, 'securityuse': 0, 'timestamp': 15812278,
    'transseqnumber': 0, 'len': 25, 'data': b'\x18\x00\n\x05\x00B\x12lumi.sensor_switch'}

    ZLC msg not ZDO
    '''
    epmock = mock.MagicMock()

    cls = Cluster.from_id(epmock, 0)
    hdr, data = cls.deserialize(b'\x18\x00\n\x05\x00B\x12lumi.sensor_switch')
    assert str(data) == '[[<Attribute attrid=5 value=<TypeValue type=CharacterString, value=lumi.sensor_switch>>]]'
    assert str(hdr) == '<ZCLHeader frame_control=<FrameControl frame_type=GLOBAL_COMMAND manufacturer_specific=False is_reply=False disable_default_response=True> manufacturer=None tsn=0 command_id=Command.Report_Attributes>'


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

def test_ieee_addr():
    # 3 - 7 - 0 - 18 - [bytearray(b'\x00\x0c%\xed\x18\x00K\x12\x00\x00\x00\x07\t\x02J\xd0]\x97')] - 172
    frame = uart.UnpiFrame(3, 7, 0, b'\x00\x0c%\xed\x18\x00K\x12\x00\x00\x00\x07\t\x02J\xd0]\x97')
    obj = ZpiObject.from_unpi_frame(frame)

    out = obj.to_unpi_frame()
    assert out.data == b'\x00\x00\x12K\x00\x18\xed%\x0c\x00\x00\x07\t\x02J\xd0]\x97'

    pass

'''
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
'''
def test_from_cluster_id():
    profile = 0
    obj = ZpiObject.from_cluster(NWK(53322), profile, ZDOCmd.Node_Desc_req, 0, 0, 0, b'\x03\x4a\xd0')

    assert str(obj) == "SREQ ZDO nodeDescReq {'dstaddr': 53322, 'nwkaddrofinterest': 53322}"


'''
profile 260
cluster 0
src_ep 1
dst_ep 1
sequence 1
data b'\x00\x0b\x00\x04\x00\x05\x00'
'''
def test_from_cluster_id_ZCL():
    profile = 260
    obj = ZpiObject.from_cluster(NWK(53322), profile, 0, 1, 1, 1, b'\x00\x0b\x00\x04\x00\x05\x00')

    assert "SREQ AF dataRequest {'dstaddr': 53322, 'destendpoint': 1, 'srcendpoint': 1, " \
           "'clusterid': 1, 'transid': 1, 'options': 0, 'radius': 0, 'len': 7, " \
           "'data': b'\\x00\\x0b\\x00\\x04\\x00\\x05\\x00'}" == str(obj)

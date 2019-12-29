from zigpy.zdo.types import ZDOCmd

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

    obj = ZpiObject.from_cluster(ZDOCmd.Node_Desc_req, b'\x03\x4a\xd0')

    assert str(obj) == "SREQ ZDO nodeDescReq {'dstaddr': 53322, 'nwkaddrofinterest': 0}"

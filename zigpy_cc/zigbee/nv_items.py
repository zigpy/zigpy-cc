from zigpy_cc.types import ZnpVersion
from zigpy_cc.zigbee.common import NvItemsIds
from zigpy_cc.zigbee.utils import getChannelMask


class Items:
    @staticmethod
    def znpHasConfiguredInit(version):
        return {
            "id": NvItemsIds.ZNP_HAS_CONFIGURED_ZSTACK1
            if version == ZnpVersion.zStack12
            else NvItemsIds.ZNP_HAS_CONFIGURED_ZSTACK3,
            "len": 0x01,
            "initlen": 0x01,
            "initvalue": b"\x00",
        }

    @staticmethod
    def znpHasConfigured(version):
        return {
            "id": NvItemsIds.ZNP_HAS_CONFIGURED_ZSTACK1
            if version == ZnpVersion.zStack12
            else NvItemsIds.ZNP_HAS_CONFIGURED_ZSTACK3,
            "offset": 0x00,
            "len": 0x01,
            "value": b"\x55",
        }

    @staticmethod
    def panID(panID):
        return {
            "id": NvItemsIds.PANID,
            "len": 0x02,
            "offset": 0x00,
            "value": bytes([panID & 0xFF, (panID >> 8) & 0xFF]),
        }

    @staticmethod
    def extendedPanID(extendedPanID):
        return {
            "id": NvItemsIds.EXTENDED_PAN_ID,
            "len": 0x08,
            "offset": 0x00,
            "value": bytes(extendedPanID),
        }

    @staticmethod
    def channelList(channelList):
        return {
            "id": NvItemsIds.CHANLIST,
            "len": 0x04,
            "offset": 0x00,
            "value": bytes(getChannelMask(channelList)),
        }

    @staticmethod
    def networkKeyDistribute(distribute):
        return {
            "id": NvItemsIds.PRECFGKEYS_ENABLE,
            "len": 0x01,
            "offset": 0x00,
            "value": b"\x01" if distribute else b"\x00",
        }

    @staticmethod
    def networkKey(key):
        return {
            # id/configid is used depending if SAPI or SYS command is executed
            "id": NvItemsIds.PRECFGKEY,
            "configid": NvItemsIds.PRECFGKEY,
            "len": 0x10,
            "offset": 0x00,
            "value": bytes(key),
        }

    @staticmethod
    def startupOption(value):
        return {
            "id": NvItemsIds.STARTUP_OPTION,
            "len": 0x01,
            "offset": 0x00,
            "value": bytes([value]),
        }

    @staticmethod
    def logicalType(value):
        return {
            "id": NvItemsIds.LOGICAL_TYPE,
            "len": 0x01,
            "offset": 0x00,
            "value": bytes([value]),
        }

    @staticmethod
    def zdoDirectCb():
        return {
            "id": NvItemsIds.ZDO_DIRECT_CB,
            "len": 0x01,
            "offset": 0x00,
            "value": b"\x01",
        }

    @staticmethod
    def tcLinkKey():
        return {
            "id": NvItemsIds.LEGACY_TCLK_TABLE_START,
            "offset": 0x00,
            "len": 0x20,
            # ZigBee Alliance Pre-configured TC Link Key - 'ZigBeeAlliance09'
            "value": bytes(
                [
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0x5A,
                    0x69,
                    0x67,
                    0x42,
                    0x65,
                    0x65,
                    0x41,
                    0x6C,
                    0x6C,
                    0x69,
                    0x61,
                    0x6E,
                    0x63,
                    0x65,
                    0x30,
                    0x39,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                ]
            ),
        }

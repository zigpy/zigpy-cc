from zigpy_cc.zigbee.common import Common


def getChannelMask(channels):
    value = 0

    for channel in channels:
        for key, logicalChannel in Common.logicalChannels.items():
            if logicalChannel == channel:
                value = value | Common.channelMask[key]

    return [
        value & 0xFF,
        (value >> 8) & 0xFF,
        (value >> 16) & 0xFF,
        (value >> 24) & 0xFF,
    ]

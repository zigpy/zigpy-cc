from zigpy_cc.zigbee.common import Common


def getCluster(key, manufacturerCode = None):

    if isinstance(key, int):
        raise Exception('Not implemented')
    else:
        name = key
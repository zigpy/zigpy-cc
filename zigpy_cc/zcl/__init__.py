

class ZclDataPayload:

    def __init__(self, obj) -> None:
        self.clusterid = obj.payload['clusterid']
        self.data = obj.payload['data']
        self.address = obj.payload['srcaddr']
        self.endpoint = obj.payload['srcendpoint']
        self.dstendpoint = obj.payload['dstendpoint']
        self.linkquality = obj.payload['linkquality']
        self.groupID = obj.payload['groupid']

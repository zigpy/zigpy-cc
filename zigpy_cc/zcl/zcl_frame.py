from zigpy.zcl import Cluster
from zigpy.zcl.foundation import ZCLHeader

MINIMAL_FRAME_LENGTH = 3


class ZclFrame:

    @classmethod
    def from_buffer(cls, cluster_id, buffer):
        if buffer.length < MINIMAL_FRAME_LENGTH:
            raise Exception("ZclFrame length is lower than minimal length")

        header = ZCLHeader.deserialize(buffer)
        cluster = Cluster.from_id(None, cluster_id)
        # cluster = Utils.getCluster(
        #     clusterID,
        #     header.frameControl.manufacturerSpecific ? header.manufacturerCode: null
        # );
        payload = cls.parse_payload(header, cluster, buffalo)

        return cls(header, payload, cluster);

    @classmethod
    def parse_header(cls, buffalo):

    @classmethod
    def parse_payload(cls, header, cluster, buffalo):
        pass

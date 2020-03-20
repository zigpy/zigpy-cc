import asyncio
import logging

import zigpy.application
import zigpy.device
import zigpy.types
import zigpy.util
from zigpy.profiles import zha
from zigpy.zdo.types import ZDOCmd
from zigpy_cc import types as t, __version__
from zigpy_cc.api import API
from zigpy_cc.exception import CommandError, TODO
from zigpy_cc.types import Subsystem, NetworkOptions, ZnpVersion
from zigpy_cc.zigbee.start_znp import start_znp
from zigpy_cc.zpi_object import ZpiObject

LOGGER = logging.getLogger(__name__)

CHANGE_NETWORK_WAIT = 1
SEND_CONFIRM_TIMEOUT = 60
PROTO_VER_WATCHDOG = 0x0108

REQUESTS = {
    "nwkAddrReq": (ZDOCmd.NWK_addr_req, 0),
    "ieeeAddrReq": (ZDOCmd.IEEE_addr_req, 0),
    "matchDescReq": (ZDOCmd.Match_Desc_req, 2),
    "endDeviceAnnceInd": (ZDOCmd.Device_annce, 2),
    "mgmtPermitJoinReq": (ZDOCmd.Mgmt_Permit_Joining_req, 3),
    "mgmtPermitJoinRsp": (ZDOCmd.Mgmt_Permit_Joining_rsp, 2),
    "nodeDescRsp": (ZDOCmd.Node_Desc_rsp, 2),
    "activeEpRsp": (ZDOCmd.Active_EP_rsp, 2),
    "simpleDescRsp": (ZDOCmd.Simple_Desc_rsp, 2),
    "bindRsp": (ZDOCmd.Bind_rsp, 2),
}

IGNORED = (
    # "activeEpRsp",
    "dataConfirm",
    "leaveInd",
    # "mgmtPermitJoinRsp",
    "srcRtgInd",
    "stateChangeInd",
    "tcDeviceInd",
)


class ControllerApplication(zigpy.application.ControllerApplication):
    _api: API

    def __init__(self, api: API, database_file=None):
        super().__init__(database_file=database_file)
        self._api = api
        api.set_application(self)

        self.discovering = False
        self.version = {}

    async def shutdown(self):
        """Shutdown application."""
        self._api.close()

    def connection_lost(self):
        asyncio.create_task(self.reconnect())

    async def reconnect(self):
        while True:
            self._api.close()
            await asyncio.sleep(5)
            try:
                await self._api.reconnect()
                break
            except Exception as e:
                LOGGER.info("Failed to reconnect: %s", e)
                pass
        await self.startup(True)

    async def startup(self, auto_form=False):
        """Perform a complete application startup"""
        LOGGER.debug("Starting zigpy-cc version: %s", __version__)
        self.version = await self._api.version()
        ver = ZnpVersion(self.version["product"]).name
        LOGGER.debug("Detected znp version '%s' (%s)", ver, self.version)

        if auto_form:
            await self.form_network()

        data = await self._api.request(Subsystem.UTIL, "getDeviceInfo", {})
        self._ieee = data.payload["ieeeaddr"]
        self._nwk = data.payload["shortaddr"]

        # add coordinator
        self.devices[self._ieee] = Coordinator(self, self._ieee, self._nwk)

    async def permit_with_key(self, node, code, time_s=60):
        raise TODO("permit_with_key")

    async def force_remove(self, dev: zigpy.device.Device):
        """Forcibly remove device from NCP."""
        LOGGER.warning("FORCE REMOVE %s", dev)

    async def form_network(self, channel=15, pan_id=None, extended_pan_id=None):
        LOGGER.info("Forming network")
        options = NetworkOptions()
        backupPath = ""
        status = await start_znp(
            self._api, self.version["product"], options, backupPath
        )
        LOGGER.debug("ZNP started, status: %s", status)

    async def mrequest(
        self,
        group_id,
        profile,
        cluster,
        src_ep,
        sequence,
        data,
        *,
        hops=0,
        non_member_radius=3
    ):
        """Submit and send data out as a multicast transmission.

        :param group_id: destination multicast address
        :param profile: Zigbee Profile ID to use for outgoing message
        :param cluster: cluster id where the message is being sent
        :param src_ep: source endpoint id
        :param sequence: transaction sequence number of the message
        :param data: Zigbee message payload
        :param hops: the message will be delivered to all nodes within this number of
                     hops of the sender. A value of zero is converted to MAX_HOPS
        :param non_member_radius: the number of hops that the message will be forwarded
                                  by devices that are not members of the group. A value
                                  of 7 or greater is treated as infinite
        :returns: return a tuple of a status and an error_message. Original requestor
                  has more context to provide a more meaningful error message
        """
        req_id = self.get_sequence()
        LOGGER.debug(
            "multicast %s",
            (
                group_id,
                profile,
                cluster,
                src_ep,
                sequence,
                data,
                hops,
                non_member_radius,
            ),
        )
        try:
            obj = ZpiObject.from_cluster(
                group_id, profile, cluster, src_ep, src_ep, sequence, data, req_id
            )

            await self._api.request_raw(obj)

        except CommandError as ex:
            return ex.status, "Couldn't enqueue send data multicast: {}".format(ex)

        return 0, "message send success"

    @zigpy.util.retryable_request
    async def request(
        self,
        device,
        profile,
        cluster,
        src_ep,
        dst_ep,
        sequence,
        data,
        expect_reply=True,
        use_ieee=False,
    ):
        req_id = self.get_sequence()
        LOGGER.debug(
            "request %s",
            (
                device.nwk,
                profile,
                cluster,
                src_ep,
                dst_ep,
                sequence,
                data,
                expect_reply,
                use_ieee,
            ),
        )

        try:
            obj = ZpiObject.from_cluster(
                device.nwk, profile, cluster, src_ep, dst_ep, sequence, data, req_id
            )
            if expect_reply:
                self._api.create_response_waiter(obj, sequence)

            await self._api.request_raw(obj)

        except CommandError as ex:
            return ex.status, "Couldn't enqueue send data request: {}".format(ex)

        return 0, "message send success"

    async def broadcast(
        self,
        profile,
        cluster,
        src_ep,
        dst_ep,
        grpid,
        radius,
        sequence,
        data,
        broadcast_address=zigpy.types.BroadcastAddress.RX_ON_WHEN_IDLE,
    ):
        req_id = self.get_sequence()
        LOGGER.debug(
            "broadcast %s",
            (
                profile,
                cluster,
                src_ep,
                dst_ep,
                grpid,
                radius,
                sequence,
                data,
                broadcast_address,
            ),
        )
        try:
            obj = ZpiObject.from_cluster(
                broadcast_address,
                profile,
                cluster,
                src_ep,
                dst_ep,
                sequence,
                data,
                req_id,
                radius=radius,
            )

            await self._api.request_raw(obj)

        except CommandError as ex:
            return (
                ex.status,
                "Couldn't enqueue send data request for broadcast: {}".format(ex),
            )

        return 0, "broadcast send success"

    async def permit_ncp(self, time_s=60):
        assert 0 <= time_s <= 254
        payload = {
            "addrmode": 0x0F,
            "dstaddr": 0xFFFC,
            "duration": time_s,
            "tcsignificance": 0,
        }
        await self._api.request(Subsystem.ZDO, "mgmtPermitJoinReq", payload)

    def handle_znp(self, obj: ZpiObject):
        if obj.type != t.CommandType.AREQ:
            return

        # if obj.subsystem == t.Subsystem.ZDO and obj.command == 'tcDeviceInd':
        #     nwk = obj.payload['nwkaddr']
        #     rest = obj.payload['extaddr'][2:].encode("ascii")
        #     ieee, _ = zigpy.types.EUI64.deserialize(rest)
        #     LOGGER.info("New device joined: 0x%04x, %s", nwk, ieee)
        #     self.handle_join(nwk, ieee, obj.payload['parentaddr'])

        frame = obj.to_unpi_frame()

        nwk = obj.payload["srcaddr"] if "srcaddr" in obj.payload else None
        ieee = obj.payload["ieeeaddr"] if "ieeeaddr" in obj.payload else None
        profile_id = zha.PROFILE_ID
        src_ep = 0
        dst_ep = 0
        lqi = 0
        rssi = 0

        if obj.subsystem == t.Subsystem.ZDO and obj.command == "endDeviceAnnceInd":
            nwk = obj.payload["nwkaddr"]
            LOGGER.info("New device joined: 0x%04x, %s", nwk, ieee)
            self.handle_join(nwk, ieee, 0)
            # TODO TEST
            obj.sequence = 0

        # TODO bindRsp

        if obj.command in IGNORED:
            LOGGER.debug("message ignored: %s", obj.command)
            return

        if obj.subsystem == t.Subsystem.ZDO and obj.command == "permitJoinInd":
            # if obj.payload["duration"] == 0:
            #     loop = asyncio.get_event_loop()
            #     loop.create_task(self.permit_ncp())
            return

        if obj.subsystem == t.Subsystem.ZDO and obj.command in REQUESTS:
            if obj.sequence is None:
                LOGGER.warning("missing tsn from %s, maybe not a reply", obj.command)
                return
            LOGGER.info("REPLY for %d %s", obj.sequence, obj.command)
            cluster_id, prefix_length = REQUESTS[obj.command]
            tsn = bytes([obj.sequence])
            data = tsn + frame.data[prefix_length:]

        elif obj.subsystem == t.Subsystem.AF and (
            obj.command == "incomingMsg" or obj.command == "incomingMsgExt"
        ):
            # ZCL commands
            cluster_id = obj.payload["clusterid"]
            src_ep = obj.payload["srcendpoint"]
            dst_ep = obj.payload["dstendpoint"]
            data = obj.payload["data"]
            lqi = obj.payload["linkquality"]

        else:
            LOGGER.warning(
                "Unhandled message: %s %s", t.Subsystem(obj.subsystem), obj.command
            )
            return

        try:
            if ieee:
                device = self.get_device(ieee=ieee)
            else:
                device = self.get_device(nwk=nwk)
        except KeyError:
            LOGGER.warning(
                "Received frame from unknown device: %s", ieee if ieee else nwk
            )
            return

        device.radio_details(lqi, rssi)
        # if obj.subsystem == t.Subsystem.ZDO:
        #     pass
        LOGGER.info("handle_message %s", obj.command)
        self.handle_message(device, profile_id, cluster_id, src_ep, dst_ep, data)


class Coordinator(zigpy.device.Device):
    @property
    def manufacturer(self):
        return "Texas Instruments"

    @property
    def model(self):
        return "ZNP Coordinator"

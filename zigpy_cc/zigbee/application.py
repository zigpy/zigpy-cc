import asyncio
import logging
from asyncio.locks import Semaphore
from typing import Any, Dict, Optional

import zigpy.application
import zigpy.config
import zigpy.device
import zigpy.types
import zigpy.util
from zigpy.profiles import zha
from zigpy.types import BroadcastAddress
from zigpy.zdo.types import ZDOCmd

from zigpy_cc import __version__, types as t
from zigpy_cc.api import API
from zigpy_cc.config import CONF_DEVICE, CONFIG_SCHEMA, SCHEMA_DEVICE
from zigpy_cc.exception import TODO, CommandError
from zigpy_cc.types import NetworkOptions, Subsystem, ZnpVersion, LedMode, AddressMode
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
    "mgmtLqiRsp": (ZDOCmd.Mgmt_Lqi_rsp, 2),
    "mgmtPermitJoinReq": (ZDOCmd.Mgmt_Permit_Joining_req, 3),
    "mgmtPermitJoinRsp": (ZDOCmd.Mgmt_Permit_Joining_rsp, 2),
    "nodeDescRsp": (ZDOCmd.Node_Desc_rsp, 2),
    "activeEpRsp": (ZDOCmd.Active_EP_rsp, 2),
    "simpleDescRsp": (ZDOCmd.Simple_Desc_rsp, 2),
    "bindRsp": (ZDOCmd.Bind_rsp, 2),
}

IGNORED = (
    "bdbComissioningNotifcation",
    "dataConfirm",
    "leaveInd",
    "resetInd",
    "srcRtgInd",
    "stateChangeInd",
    "tcDeviceInd",
)


class ControllerApplication(zigpy.application.ControllerApplication):
    _semaphore: Semaphore
    _api: Optional[API]
    SCHEMA = CONFIG_SCHEMA
    SCHEMA_DEVICE = SCHEMA_DEVICE

    probe = API.probe

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config=zigpy.config.ZIGPY_SCHEMA(config))
        self._api = None

        self.discovering = False
        self.version = {}

    async def shutdown(self):
        """Shutdown application."""
        self._api.close()

    def connection_lost(self):
        asyncio.create_task(self.reconnect())

    async def reconnect(self):
        while True:
            if self._api is not None:
                self._api.close()
            await asyncio.sleep(5)
            try:
                await self.startup(True)
                break
            except Exception as e:
                LOGGER.info("Failed to reconnect: %s", e)
                pass

    async def startup(self, auto_form=False):
        """Perform a complete application startup"""

        LOGGER.info("Starting zigpy-cc version: %s", __version__)
        self._api = await API.new(self, self._config[CONF_DEVICE])

        try:
            await self._api.request(Subsystem.SYS, "ping", {"capabilities": 1})
        except CommandError as e:
            raise Exception("Failed to connect to the adapter(%s)", e)

        self.version = await self._api.version()

        concurrent = 16 if self.version["product"] == ZnpVersion.zStack3x0 else 2
        LOGGER.debug("Adapter concurrent: %d", concurrent)

        self._semaphore = asyncio.Semaphore(concurrent)

        ver = ZnpVersion(self.version["product"]).name
        LOGGER.info("Detected znp version '%s' (%s)", ver, self.version)

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
        LOGGER.debug("Config: %s", self.config)
        options = NetworkOptions(self.config[zigpy.config.CONF_NWK])
        LOGGER.debug("NetworkOptions: %s", options)
        backupPath = ""
        status = await start_znp(
            self._api, self.version["product"], options, 0x0B84, backupPath
        )
        LOGGER.info("ZNP started, status: %s", status)

        self.set_led(LedMode.Off)

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
                group_id,
                profile,
                cluster,
                src_ep or 1,
                0xFF,
                sequence,
                data,
                addr_mode=AddressMode.ADDR_GROUP,
            )
            waiter_id = None
            waiter = self._api.create_response_waiter(obj, sequence)
            if waiter:
                waiter_id = waiter.id

            async with self._semaphore:
                await self._api.request_raw(obj, waiter_id)
                """
                As a group command is not confirmed and thus immediately returns
                (contrary to network address requests) we will give the
                command some time to 'settle' in the network.
                """
                await asyncio.sleep(0.2)

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
                device.nwk, profile, cluster, src_ep, dst_ep, sequence, data
            )
            waiter_id = None
            if expect_reply:
                waiter = self._api.create_response_waiter(obj, sequence)
                if waiter:
                    waiter_id = waiter.id

            async with self._semaphore:
                await self._api.request_raw(obj, waiter_id)

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
                radius=radius,
                addr_mode=AddressMode.ADDR_16BIT,
            )

            async with self._semaphore:
                await self._api.request_raw(obj)
                """
                As a broadcast command is not confirmed and thus immediately returns
                (contrary to network address requests) we will give the
                command some time to 'settle' in the network.
                """
                await asyncio.sleep(0.2)

        except CommandError as ex:
            return (
                ex.status,
                "Couldn't enqueue send data request for broadcast: {}".format(ex),
            )

        return 0, "broadcast send success"

    async def permit_ncp(self, time_s=60):
        assert 0 <= time_s <= 254
        payload = {
            "addrmode": AddressMode.ADDR_BROADCAST,
            "dstaddr": BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
            "duration": time_s,
            "tcsignificance": 0,
        }
        async with self._semaphore:
            await self._api.request(Subsystem.ZDO, "mgmtPermitJoinReq", payload)

    def handle_znp(self, obj: ZpiObject):
        if obj.command_type != t.CommandType.AREQ:
            return

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
            obj.sequence = 0

        if obj.command in IGNORED:
            return

        if obj.subsystem == t.Subsystem.ZDO and obj.command == "mgmtPermitJoinRsp":
            self.set_led(LedMode.On)

        if obj.subsystem == t.Subsystem.ZDO and obj.command == "permitJoinInd":
            self.set_led(LedMode.Off if obj.payload["duration"] == 0 else LedMode.On)
            return

        if obj.subsystem == t.Subsystem.ZDO and obj.command in REQUESTS:
            if obj.sequence is None:
                return
            LOGGER.debug("REPLY for %d %s", obj.sequence, obj.command)
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
                "Unhandled message: %s %s %s",
                t.CommandType(obj.command_type),
                t.Subsystem(obj.subsystem),
                obj.command,
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

        LOGGER.info("handle_message %s", obj.command)
        self.handle_message(device, profile_id, cluster_id, src_ep, dst_ep, data)

    def set_led(self, mode: LedMode):
        if self.version["product"] != ZnpVersion.zStack3x0:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self._api.request(
                        Subsystem.UTIL, "ledControl", {"ledid": 3, "mode": mode}
                    )
                )
            except Exception as ex:
                LOGGER.warning("Can't set LED: %s", ex)


class Coordinator(zigpy.device.Device):
    """
    todo add endpoints?
    @see zStackAdapter.ts - getCoordinator
    """

    @property
    def manufacturer(self):
        return "Texas Instruments"

    @property
    def model(self):
        return "ZNP Coordinator"

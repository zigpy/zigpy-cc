import asyncio
import binascii
import logging
import os

from zigpy.profiles import zha

from zigpy.zdo.types import ZDOCmd

import zigpy.application
import zigpy.device
import zigpy.endpoint
import zigpy.exceptions
import zigpy.types
import zigpy.util
import zigpy_cc.exception
from zigpy_cc import types as t
# from zigpy_cc.api import NetworkParameter, NetworkState, Status
from zigpy_cc.api import API
from zigpy_cc.const import Constants
from zigpy_cc.uart import UnpiFrame
from zigpy_cc.zigbee.nv_items import Items
from zigpy_cc.types import Subsystem, NetworkOptions, ZnpVersion, CommandType
from zigpy_cc.zigbee.start_znp import initialise, start_znp
from zigpy_cc.zpi_object import ZpiObject

LOGGER = logging.getLogger(__name__)

CHANGE_NETWORK_WAIT = 1
SEND_CONFIRM_TIMEOUT = 60
PROTO_VER_WATCHDOG = 0x0108


class ControllerApplication(zigpy.application.ControllerApplication):
    def __init__(self, api: API, database_file=None):
        super().__init__(database_file=database_file)
        self._api = api
        api.set_application(self)

        self._pending = zigpy.util.Requests()

        self.discovering = False
        self.version = {}

    async def _reset_watchdog(self):
        while True:
            await self._api.write_parameter(NetworkParameter.watchdog_ttl, 3600)
            await asyncio.sleep(1200)

    async def shutdown(self):
        """Shutdown application."""
        self._api.close()

    async def startup(self, auto_form=False):
        """Perform a complete application startup"""
        self.version = await self._api.version()
        ver = ZnpVersion(self.version['product']).name
        LOGGER.debug("Detected znp version '%s' (%s)", ver, self.version)

        if auto_form:
            await self.form_network()

        data = await self._api.request(Subsystem.UTIL, 'getDeviceInfo', {})
        self._ieee = data.payload['ieeeaddr']
        self._nwk = data.payload['shortaddr']

        # add coordinator
        self.handle_join(self.nwk, self.ieee, 0)

    async def force_remove(self, dev):
        """Forcibly remove device from NCP."""
        pass

    async def form_network(self, channel=15, pan_id=None, extended_pan_id=None):
        LOGGER.info("Forming network")
        options = NetworkOptions()
        backupPath = ""
        status = await start_znp(self._api, self.version['product'], options, backupPath)
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
            "Sending Zigbee multicast with tsn %s under %s request id, data: %s",
            sequence,
            req_id,
            binascii.hexlify(data),
        )
        dst_addr_ep = t.DeconzAddressEndpoint()
        dst_addr_ep.address_mode = t.ADDRESS_MODE.GROUP
        dst_addr_ep.address = group_id

        with self._pending.new(req_id) as req:
            try:
                await self._api.aps_data_request(
                    req_id, dst_addr_ep, profile, cluster, min(1, src_ep), data
                )
            except zigpy_cc.exception.CommandError as ex:
                return ex.status, "Couldn't enqueue send data request: {}".format(ex)

            r = await asyncio.wait_for(req.result, SEND_CONFIRM_TIMEOUT)
            if r:
                LOGGER.warning("Error while sending %s req id frame: 0x%02x", req_id, r)
                return r, "message send failure"

        return Status.SUCCESS, "message send success"

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
            "Sending Zigbee request with tsn %s under %s request id, data: %s",
            sequence,
            req_id,
            binascii.hexlify(data),
        )

        with self._pending.new(req_id) as req:
            obj = ZpiObject.from_cluster(cluster, data)

            try:
                await self._api.request_raw(obj)
            except zigpy_cc.exception.CommandError as ex:
                return ex.status, "Couldn't enqueue send data request: {}".format(ex)

            return 0, "message send success"

        #     try:
        #         await self._api.aps_data_request(
        #             req_id, dst_addr_ep, profile, cluster, min(1, src_ep), data
        #         )
        #     except zigpy_cc.exception.CommandError as ex:
        #         return ex.status, "Couldn't enqueue send data request: {}".format(ex)
        #
        #     r = await asyncio.wait_for(req.result, SEND_CONFIRM_TIMEOUT)
        #
        #     if r:
        #         LOGGER.warning("Error while sending %s req id frame: 0x%02x", req_id, r)
        #         return r, "message send failure"
        #
        #     return r, "message send success"

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
            "Sending Zigbee broadcast with tsn %s under %s request id, data: %s",
            sequence,
            req_id,
            binascii.hexlify(data),
        )
        dst_addr_ep = t.DeconzAddressEndpoint()
        dst_addr_ep.address_mode = t.uint8_t(t.ADDRESS_MODE.GROUP.value)
        dst_addr_ep.address = t.uint16_t(broadcast_address)

        with self._pending.new(req_id) as req:
            try:
                await self._api.aps_data_request(
                    req_id, dst_addr_ep, profile, cluster, min(1, src_ep), data
                )
            except zigpy_cc.exception.CommandError as ex:
                return (
                    ex.status,
                    "Couldn't enqueue send data request for broadcast: {}".format(ex),
                )

            r = await asyncio.wait_for(req.result, SEND_CONFIRM_TIMEOUT)

            if r:
                LOGGER.warning(
                    "Error while sending %s req id broadcast: 0x%02x", req_id, r
                )
                return r, "broadcast send failure"
            return r, "broadcast send success"

    async def permit_ncp(self, time_s=60):
        assert 0 <= time_s <= 254
        await self._api.write_parameter(NetworkParameter.permit_join, time_s)

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

        profile_id = zha.PROFILE_ID
        src_ep = 0
        dst_ep = 0
        lqi = 0
        rssi = 0


        if obj.subsystem == t.Subsystem.ZDO and obj.command == 'endDeviceAnnceInd':
            nwk = obj.payload['nwkaddr']
            cluster_id = ZDOCmd.Device_annce
            tsn = b'\x00'
            data = tsn + frame.data[2:]
            ieee = obj.payload['ieeeaddr']
            LOGGER.info("New device joined: %s, %s", nwk, ieee)
            self.handle_join(nwk, ieee, 0)

        elif obj.subsystem == t.Subsystem.AF and (obj.command == 'incomingMsg' or obj.command == 'incomingMsgExt'):
            nwk = obj.payload['srcaddr']
            cluster_id = obj.payload['clusterid']
            src_ep = obj.payload['srcendpoint']
            dst_ep = obj.payload['dstendpoint']
            data = obj.payload['data']
            lqi = obj.payload['linkquality']
        else:
            LOGGER.warning("Unhandled message: %s %s", obj.subsystem, obj.command)
            return

        try:
            device = self.get_device(nwk=nwk)
        except KeyError:
            LOGGER.debug("Received frame from unknown device: %s", nwk)
            return

        device.radio_details(lqi, rssi)
        self.handle_message(device, profile_id, cluster_id, src_ep, dst_ep, data)

        #
        # try:
        #     if src_addr.address_mode == t.ADDRESS_MODE.NWK_AND_IEEE:
        #         device = self.get_device(ieee=src_addr.ieee)
        #     elif src_addr.address_mode == t.ADDRESS_MODE.NWK.value:
        #         device = self.get_device(nwk=src_addr.address)
        #     elif src_addr.address_mode == t.ADDRESS_MODE.IEEE.value:
        #         device = self.get_device(ieee=src_addr.address)
        #     else:
        #         raise Exception(
        #             "Unsupported address mode in handle_rx: %s"
        #             % (src_addr.address_mode)
        #         )
        # except KeyError:
        #     LOGGER.debug("Received frame from unknown device: 0x%04x", src_addr.address)
        #     return
        #
        # device.radio_details(lqi, rssi)
        # self.handle_message(device, profile_id, cluster_id, src_ep, dst_ep, data)

    def handle_tx_confirm(self, req_id, status):
        try:
            self._pending[req_id].result.set_result(status)
            return
        except KeyError as exc:
            LOGGER.warning(
                "Unexpected transmit confirm for request id %s, Status: 0x%02x, %s",
                req_id,
                status,
                exc,
            )
        except asyncio.InvalidStateError as exc:
            LOGGER.debug(
                "Invalid state on future - probably duplicate response: %s", exc
            )


class CCDevice(zigpy.device.Device):
    """Zigpy Device representing Coordinator."""

    async def add_to_group(self, grp_id: int, name: str = None) -> None:
        group = self.application.groups.add_group(grp_id, name)

        for epid in self.endpoints:
            if not epid:
                continue  # skip ZDO
            group.add_member(self.endpoints[epid])
        return [0]

    async def remove_from_group(self, grp_id: int) -> None:
        for epid in self.endpoints:
            if not epid:
                continue  # skip ZDO
            self.application.groups[grp_id].remove_member(self.endpoints[epid])
        return [0]

    @property
    def manufacturer(self):
        return "dresden elektronik"

    @property
    def model(self):
        return "ConBee"

    @classmethod
    async def new(cls, application, ieee, nwk):
        """Create or replace zigpy device."""
        dev = cls(application, ieee, nwk)

        if ieee in application.devices:
            from_dev = application.get_device(ieee=ieee)
            dev.status = from_dev.status
            dev.node_desc = from_dev.node_desc
            for ep_id, from_ep in from_dev.endpoints.items():
                if not ep_id:
                    continue  # Skip ZDO
                ep = dev.add_endpoint(ep_id)
                ep.profile_id = from_ep.profile_id
                ep.device_type = from_ep.device_type
                ep.status = from_ep.status
                ep.in_clusters = from_ep.in_clusters
                ep.out_clusters = from_ep.out_clusters
        else:
            application.devices[ieee] = dev
            await dev._initialize()

        return dev

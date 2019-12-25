import asyncio
import logging

import zigpy.application
import zigpy.device
import zigpy.types
import zigpy.util
from zigpy_zigate import types as t
from zigpy_zigate.api import NoResponseError

LOGGER = logging.getLogger(__name__)


class ControllerApplication(zigpy.application.ControllerApplication):
    def __init__(self, api, database_file=None):
        super().__init__(database_file=database_file)
        self._api = api
        self._api.add_callback(self.zigate_callback_handler)
        api.set_application(self)

        self._pending = {}

        self._nwk = 0
        self._ieee = 0
        self.version = ''

    async def startup(self, auto_form=False):
        """Perform a complete application startup"""
        await self._api.set_raw_mode()
        version, lqi = await self._api.version()
        version = '{:x}'.format(version[1])
        version = '{}.{}'.format(version[0], version[1:])
        self.version = version

        if auto_form:
            await self.form_network()

        network_state, lqi = await self._api.get_network_state()
        self._nwk = network_state[0]
        self._ieee = zigpy.types.EUI64(network_state[1])

        dev = ZiGateDevice(self, self._ieee, self._nwk)
        self.devices[dev.ieee] = dev

    async def shutdown(self):
        """Shutdown application."""
        self._api.close()

    async def form_network(self, channel=15, pan_id=None, extended_pan_id=None):
        await self._api.set_channel(channel)
        if pan_id:
            LOGGER.warning('Setting pan_id is not supported by ZiGate')
#             self._api.set_panid(pan_id)
        if extended_pan_id:
            await self._api.set_extended_panid(extended_pan_id)

        network_formed, lqi = await self._api.start_network()
        if network_formed[0] in (0, 1, 4):
            LOGGER.info('Network started %s %s',
                        network_formed[1],
                        network_formed[2])
            self._nwk = network_formed[1]
            self._ieee = network_formed[2]
        else:
            LOGGER.warning('Starting network got status %s, wait...', network_formed[0])
            tries = 3
            while tries > 0:
                await asyncio.sleep(1)
                tries -= 1
                network_state, lqi = await self._api.get_network_state()
                if network_state and \
                   network_state[3] != 0 and \
                   network_state[0] != 'ffff':
                    break
            if tries <= 0:
                LOGGER.error('Failed to start network error %s', network_formed[0])
                await self._api.reset()

    async def force_remove(self, dev):
        await self._api.remove_device(self._ieee, dev.ieee)

    def zigate_callback_handler(self, msg, response, lqi):
        LOGGER.debug('zigate_callback_handler {}'.format(response))

        if msg == 0x8048:  # leave
            nwk = 0
            ieee = zigpy.types.EUI64(response[0])
            self.handle_leave(nwk, ieee)
        elif msg == 0x004D:  # join
            nwk = response[0]
            ieee = zigpy.types.EUI64(response[1])
            parent_nwk = 0
            self.handle_join(nwk, ieee, parent_nwk)
        elif msg == 0x8002:
            try:
                if response[5].address_mode == t.ADDRESS_MODE.NWK:
                    device = self.get_device(nwk=response[5].address)
                elif response[5].address_mode == t.ADDRESS_MODE.IEEE:
                    device = self.get_device(ieee=zigpy.types.EUI64(response[5].address))
                else:
                    LOGGER.error("No such device %s", response[5].address)
                    return
            except KeyError:
                LOGGER.debug("No such device %s", response[5].address)
                return
            rssi = 0
            device.radio_details(lqi, rssi)
            self.handle_message(device, response[1],
                                response[2],
                                response[3], response[4], response[-1])
        elif msg == 0x8702:  # APS Data confirm Fail
            self._handle_frame_failure(response[4], response[0])

    def _handle_frame_failure(self, message_tag, status):
        try:
            send_fut = self._pending.pop(message_tag)
            send_fut.set_result(status)
        except KeyError:
            LOGGER.warning("Unexpected message send failure")
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug("Invalid state on future - probably duplicate response: %s", exc)

    @zigpy.util.retryable_request
    async def request(self, device, profile, cluster, src_ep, dst_ep, sequence, data,
                      expect_reply=True, use_ieee=False):
        src_ep = 1 if dst_ep else 0  # ZiGate only support endpoint 1
        LOGGER.debug('request %s',
                     (device.nwk, profile, cluster, src_ep, dst_ep, sequence, data, expect_reply, use_ieee))
        req_id = self.get_sequence()
        send_fut = asyncio.Future()
        self._pending[req_id] = send_fut
        try:
            v, lqi = await self._api.raw_aps_data_request(device.nwk, src_ep, dst_ep, profile, cluster, data)
        except NoResponseError:
            return 1, "ZiGate doesn't answer to command"

        if v[0] != 0:
            self._pending.pop(req_id)
            return v[0], "Message send failure {}".format(v[0])

        # Commented out for now
        # Currently (Firmware 3.1a) only send APS Data confirm in case of failure
        # https://github.com/fairecasoimeme/ZiGate/issues/239
#         try:
#             v = await asyncio.wait_for(send_fut, 120)
#         except asyncio.TimeoutError:
#             return 1, "timeout waiting for message %s send ACK" % (sequence, )
#         finally:
#             self._pending.pop(req_id)
#         return v, "Message sent"
        return 0, "Message sent"

    async def permit_ncp(self, time_s=60):
        assert 0 <= time_s <= 254
        status, lqi = await self._api.permit_join(time_s)
        if status[0] != 0:
            await self._api.reset()

    async def broadcast(self, profile, cluster, src_ep, dst_ep, grpid, radius,
                        sequence, data, broadcast_address):
        LOGGER.debug("Broadcast not implemented.")


class ZiGateDevice(zigpy.device.Device):
    @property
    def manufacturer(self):
        return "ZiGate"

    @property
    def model(self):
        return 'ZiGate'

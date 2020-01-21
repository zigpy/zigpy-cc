import logging
import os

from zigpy.zcl.clusters.security import IasZone

from zigpy_cc.api import API
from zigpy_cc.const import Constants
from zigpy_cc.types import NetworkOptions, Subsystem, ZnpVersion, CommandType
from zigpy_cc.exception import CommandError
from zigpy_cc.zigbee.backup import Restore
from zigpy_cc.zigbee.common import Common
from zigpy_cc.zigbee.utils import getChannelMask
from .nv_items import Items

LOGGER = logging.getLogger(__name__)


class Endpoint:
    def __init__(self, **kwargs) -> None:
        self.endpoint = None
        self.appdeviceid = 0x0005
        self.appdevver = 0
        self.appnuminclusters = 0
        self.appinclusterlist = []
        self.appnumoutclusters = 0
        self.appoutclusterlist = []
        self.latencyreq = Constants.AF.networkLatencyReq.NO_LATENCY_REQS
        for key, value in kwargs.items():
            setattr(self, key, value)


Endpoints = [
    Endpoint(endpoint=1, appprofid=0x0104),
    Endpoint(endpoint=2, appprofid=0x0101),
    Endpoint(endpoint=3, appprofid=0x0106),
    Endpoint(endpoint=4, appprofid=0x0107),
    Endpoint(endpoint=5, appprofid=0x0108),
    Endpoint(endpoint=6, appprofid=0x0109),
    Endpoint(endpoint=8, appprofid=0x0104),
    Endpoint(
        endpoint=11,
        appprofid=0x0104,
        appdeviceid=0x0400,
        appnumoutclusters=1,
        appoutclusterlist=[IasZone.cluster_id],
    ),
    # TERNCY: https://github.com/Koenkk/zigbee-herdsman/issues/82
    Endpoint(endpoint=0x6E, appprofid=0x0104),
    Endpoint(endpoint=12, appprofid=0xC05E),
]


async def validate_item(
    znp: API, item, message, subsystem=Subsystem.SYS, command="osalNvRead"
):
    result = await znp.request(subsystem, command, item)
    if result.payload["value"] != item["value"]:
        msg = "Item '{}' is invalid, got '{}', expected '{}'".format(
            message, result.payload["value"], item["value"]
        )
        LOGGER.debug(msg)
        raise AssertionError(msg)
    else:
        LOGGER.debug("Item '%s' is valid", message)


async def needsToBeInitialised(znp: API, version, options):
    try:
        await validate_item(znp, Items.znpHasConfigured(version), "hasConfigured")
        await validate_item(znp, Items.channelList(options.channelList), "channelList")
        await validate_item(
            znp,
            Items.networkKeyDistribute(options.networkKeyDistribute),
            "networkKeyDistribute",
        )

        if version == ZnpVersion.zStack3x0:
            await validate_item(znp, Items.networkKey(options.networkKey), "networkKey")
        else:
            await validate_item(
                znp,
                Items.networkKey(options.networkKey),
                "networkKey",
                Subsystem.SAPI,
                "readConfiguration",
            )

        await validate_item(znp, Items.panID(options.panID), "panID")
        await validate_item(
            znp, Items.extendedPanID(options.extendedPanID), "extendedPanID"
        )

        return False
    except Exception as e:
        LOGGER.debug("Error while validating items: %s", e)
        return True


async def boot(znp: API):
    result = await znp.request(Subsystem.UTIL, "getDeviceInfo", {})

    if result.payload["devicestate"] != Common.devStates["ZB_COORD"]:
        LOGGER.debug("Start ZNP as coordinator...")
        started = znp.wait_for(
            CommandType.AREQ, Subsystem.ZDO, "stateChangeInd", {"state": 9}, 60000
        )
        await znp.request(Subsystem.ZDO, "startupFromApp", {"startdelay": 100}, [0, 1])
        await started.wait()
        LOGGER.debug("ZNP started as coordinator")
    else:
        LOGGER.debug("ZNP is already started as coordinator")


async def registerEndpoints(znp: API):
    LOGGER.debug("Register endpoints...")

    activeEpResponse = znp.wait_for(CommandType.AREQ, Subsystem.ZDO, "activeEpRsp")
    try:
        await znp.request(
            Subsystem.ZDO, "activeEpReq", {"dstaddr": 0, "nwkaddrofinterest": 0}
        )
    except Exception as e:
        LOGGER.debug(e)
    activeEp = await activeEpResponse.wait()

    for endpoint in Endpoints:
        if endpoint.endpoint in activeEp.payload["activeeplist"]:
            LOGGER.debug("Endpoint '%s' already registered", endpoint.endpoint)
        else:
            LOGGER.debug("Registering endpoint '%s'", endpoint.endpoint)
            await znp.request(Subsystem.AF, "register", vars(endpoint))


async def initialise(znp: API, version, options: NetworkOptions):
    await znp.request(Subsystem.SYS, "resetReq", {"type": Constants.SYS.resetType.SOFT})
    await znp.request(Subsystem.SYS, "osalNvWrite", Items.startupOption(0x02))
    await znp.request(Subsystem.SYS, "resetReq", {"type": Constants.SYS.resetType.SOFT})
    await znp.request(
        Subsystem.SYS,
        "osalNvWrite",
        Items.logicalType(Constants.ZDO.deviceLogicalType.COORDINATOR),
    )
    await znp.request(
        Subsystem.SYS,
        "osalNvWrite",
        Items.networkKeyDistribute(options.networkKeyDistribute),
    )
    await znp.request(Subsystem.SYS, "osalNvWrite", Items.zdoDirectCb())
    await znp.request(
        Subsystem.SYS, "osalNvWrite", Items.channelList(options.channelList)
    )
    await znp.request(Subsystem.SYS, "osalNvWrite", Items.panID(options.panID))
    await znp.request(
        Subsystem.SYS, "osalNvWrite", Items.extendedPanID(options.extendedPanID)
    )

    if version == ZnpVersion.zStack30x or version == ZnpVersion.zStack3x0:
        await znp.request(
            Subsystem.SYS, "osalNvWrite", Items.networkKey(options.networkKey)
        )

        # Default link key is already OK for Z-Stack 3 ('ZigBeeAlliance09')
        channelMask = int.from_bytes(
            bytes(getChannelMask(options.channelList)), "little"
        )
        await znp.request(
            Subsystem.APP_CNF,
            "bdbSetChannel",
            {"isPrimary": 0x1, "channel": channelMask},
        )
        await znp.request(
            Subsystem.APP_CNF, "bdbSetChannel", {"isPrimary": 0x0, "channel": 0x0}
        )

        started = znp.wait_for(
            CommandType.AREQ, Subsystem.ZDO, "stateChangeInd", {"state": 9}, 60000
        )
        await znp.request(Subsystem.APP_CNF, "bdbStartCommissioning", {"mode": 0x04})
        try:
            await started.wait()
        except Exception:
            raise Exception(
                "Coordinator failed to start, probably the panID is already in use, "
                "try a different panID or channel"
            )

        await znp.request(Subsystem.APP_CNF, "bdbStartCommissioning", {"mode": 0x02})
    else:
        await znp.request(
            Subsystem.SAPI, "writeConfiguration", Items.networkKey(options.networkKey)
        )
        await znp.request(Subsystem.SYS, "osalNvWrite", Items.tcLinkKey())

    # expect status code 9 (= item created and initialized)
    await znp.request(
        Subsystem.SYS, "osalNvItemInit", Items.znpHasConfiguredInit(version), [0, 9]
    )
    await znp.request(Subsystem.SYS, "osalNvWrite", Items.znpHasConfigured(version))


async def start_znp(znp: API, version, options: NetworkOptions, backupPath=""):
    result = "resumed"

    try:
        await validate_item(znp, Items.znpHasConfigured(version), "hasConfigured")
        hasConfigured = True
    except (AssertionError, CommandError):
        hasConfigured = False

    if backupPath and os.path.exists(backupPath) and not hasConfigured:
        LOGGER.debug("Restoring coordinator from backup")
        await Restore(znp, backupPath, options)
        result = "restored"
    elif await needsToBeInitialised(znp, version, options):
        LOGGER.debug("Initialize coordinator")
        await initialise(znp, version, options)

        if version == ZnpVersion.zStack12:
            # zStack12 allows to restore a network without restoring a backup
            # (as long as the network key, panID and channel don't change).
            # If the device has not been configured yet we assume that this is the case.
            # If we always return 'reset'
            # the controller clears the database on a reflash of the stick.
            result = "reset" if hasConfigured else "restored"
        else:
            result = "reset"

    await boot(znp)
    await registerEndpoints(znp)

    if result == "restored":
        # Write channel list again, otherwise it doesnt seem to stick.
        await znp.request(
            Subsystem.SYS, "osalNvWrite", Items.channelList(options.channelList)
        )

    return result

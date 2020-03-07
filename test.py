import asyncio
import logging
import os

import coloredlogs as coloredlogs
from serial import SerialException

from zigpy.device import Device

from zigpy_cc.api import API
from zigpy_cc.zigbee import application

fmt = "%(name)s %(levelname)s %(message)s"
coloredlogs.install(level="DEBUG", fmt=fmt)

LOGGER = logging.getLogger(__name__)

# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('zigpy_cc.uart').setLevel(logging.INFO)
# logging.getLogger('zigpy_cc.api').setLevel(logging.INFO)

loop = asyncio.get_event_loop()


class TestApp:
    def device_joined(self, app, device: Device):
        async def init_dev():
            LOGGER.info("endpoints %s", device.endpoints)

            for key, endp in device.endpoints.items():
                LOGGER.info("endpoint %s", key)
                if hasattr(endp, 'in_clusters'):
                    LOGGER.info("in_clusters %s", endp.in_clusters)
                    LOGGER.info("out_clusters %s", endp.out_clusters)

                    await asyncio.sleep(2)
                    await endp.out_clusters[8].bind()


            # res = await device.zdo.bind(endp.out_clusters[8])
            # LOGGER.warning(res)
            #res = await device.zdo.bind(endp.out_clusters[6])
            #LOGGER.warning(res)
            #res = await device.zdo.bind(endp.in_clusters[1])
            #LOGGER.warning(res)

            # power_cluster: PowerConfiguration = endp.in_clusters[1]
            # res = await power_cluster.configure_reporting(
            #     'battery_percentage_remaining', 3600, 62000, 0
            # )
            # LOGGER.warning(res)

        loop.create_task(init_dev())


async def main():
    # noinspection PyUnresolvedReferences
    import zhaquirks  # noqa: F401

    api = API()
    while True:
        try:
            await api.connect("auto")
            break
        except SerialException as e:
            print(e)
            await asyncio.sleep(2)

    db = "store.db"
    try:
        app = application.ControllerApplication(api, database_file=db)
    except KeyError:
        LOGGER.error("DB error, removing DB...")
        await asyncio.sleep(1)
        os.remove(db)
        app = application.ControllerApplication(api, database_file=db)

    testapp = TestApp()

    app.add_context_listener(testapp)

    LOGGER.info("STARTUP")
    await app.startup(auto_form=False)
    await app.form_network()

    await app.permit_ncp()


loop.run_until_complete(main())
loop.run_forever()
loop.close()

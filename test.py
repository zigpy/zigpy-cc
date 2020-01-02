import asyncio
import logging
import os

import coloredlogs as coloredlogs
from serial import SerialException

from zigpy_cc.api import API
from zigpy_cc.zigbee import application

fmt = '%(name)s %(levelname)s %(message)s'
coloredlogs.install(level='DEBUG', fmt=fmt)

LOGGER = logging.getLogger(__name__)

# logging.basicConfig(level=logging.DEBUG)
#logging.getLogger('zigpy_cc.uart').setLevel(logging.INFO)
#logging.getLogger('zigpy_cc.api').setLevel(logging.INFO)


async def main():
    # noinspection PyUnresolvedReferences
    import zhaquirks

    api = API()
    while True:
        try:
            await api.connect("/dev/ttyACM0")
            break
        except SerialException as e:
            print(e)
            await asyncio.sleep(2)

    db = 'store.db'
    try:
        app = application.ControllerApplication(api, database_file=db)
    except KeyError:
        LOGGER.error('DB error, removing DB...')
        await asyncio.sleep(1)
        os.remove(db)
        app = application.ControllerApplication(api, database_file=db)

    await app.startup(auto_form=False)
    await app.form_network()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
loop.close()

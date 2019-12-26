import asyncio
import logging

from zigpy_cc.api import API
from zigpy_cc.zigbee import application

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('zigpy_cc.uart').setLevel(logging.INFO)
# logging.getLogger('zigpy_cc.api').setLevel(logging.INFO)

path = "/dev/ttyACM0"


async def main():
    api = API()
    await api.connect(path)
    app = application.ControllerApplication(api, database_file=None)
    await app.startup(auto_form=False)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

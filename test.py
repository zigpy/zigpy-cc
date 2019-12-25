import asyncio
import logging

from zigpy_cc import api
from zigpy_cc.api import API
from zigpy_cc.uart import Parser

logging.basicConfig(level=logging.DEBUG)

path = "/dev/ttyACM0"

baudrate = 115200
rtscts = True


SOF = bytearray()
SOF.append(api.SOF)

response = []

# noise
response.append(b'\x00')
response.append(b'\x00')

response.append(b'\xfe')
response.append(b'\x0c')
response.append(b'E')
response.append(b'\xca')
response.append(b'J')
response.append(b'\xd0')
response.append(b'A')
response.append(b'\xe5')
response.append(b'K')
response.append(b'\x02')
response.append(b'\x00')
response.append(b'\x8d')
response.append(b'\x15')
response.append(b'\x00')
response.append(b'\xc3')
response.append(b'\x19')
response.append(b'\xb6')

response.append(b'\xfe')
response.append(b'\r')
response.append(b'E')
response.append(b'\xc1')
response.append(b'J')
response.append(b'\xd0')
response.append(b'J')
response.append(b'\xd0')
response.append(b'A')
response.append(b'\xe5')
response.append(b'K')
response.append(b'\x02')
response.append(b'\x00')
response.append(b'\x8d')
response.append(b'\x15')
response.append(b'\x00')
response.append(b'\x84')
response.append(b'x')

response.append(b'\xfe')
response.append(b'\x0e')
response.append(b'a')
response.append(b'\x02')
response.append(b'\x02')
response.append(b'\x00')
response.append(b'\x02')
response.append(b'\x06')
response.append(b'\x03')
response.append(b'\x90')
response.append(b'\x15')
response.append(b'4')
response.append(b'\x01')
response.append(b'\x02')
response.append(b'\x00')
response.append(b'\x00')
response.append(b'\x00')
response.append(b'\x00')
response.append(b'\xda')




def test():
    parser = Parser()
    for b in b'\xfe\x0ea\x02\x02\x00\x02\x06\x03\x90\x154\x01\x02\x00\x00\x00\x00\xda':
        obj = parser.write(b)
        if obj is not None:
            print('-->', obj)

    print()
    print()
    # req = createRequest(Subsystem.SYS, "version", {})
    # print("<--", req)
    # frame = req.to_unpi_frame()
    # print('frame', frame)
    # print('buffer', frame.to_buffer())

async def main():
    api = API()
    await api.connect(path)
    print("connected")
    ver = await api.version()
    print("ver", ver)

# test()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

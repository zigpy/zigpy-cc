import time

import serial

from zigpy_cc import api
from zigpy_cc.types import Subsystem

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

def request(ser, subsystem, command, payload):
    req = createRequest(subsystem, command, payload)
    print("<--", req)

    frame = req.to_unpi_frame()
    ser.write(frame.to_buffer())
    read_frame(ser)

def read_frame(ser):
    parser = api.Parser()
    while True:
        b = ser.read()
        obj = parser.write(b)
        if obj is not None:
            print("-->", obj)
            return


def createRequest(subsystem, command, payload):
    cmd = next(c for c in api.Definition[subsystem] if c["name"] == command)

    return api.ZpiObject(cmd["type"], subsystem, command, cmd["ID"], payload, cmd["request"])



def test():
    parser = api.Parser()
    for b in response:
        obj = parser.write(b)
        if obj is not None:
            print('-->', obj)

    print()
    print()
    req = createRequest(Subsystem.SYS, "version", {})
    print("<--", req)
    frame = req.to_unpi_frame()
    print('frame', frame)
    print('buffer', frame.to_buffer())

# test()
with serial.Serial(path, baudrate, rtscts=rtscts) as ser:
    print("connected", ser.name)
    ser.write(b'\xef')
    time.sleep(1)
    request(ser, Subsystem.SYS, "version", {})

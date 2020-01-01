from zigpy.profiles import zha

from zigpy_cc import uart
from zigpy_cc.buffalo import Buffalo, BuffaloOptions
from zigpy_cc.definition import Definition
from zigpy_cc.types import CommandType, ParameterType, Subsystem

BufferAndListTypes = [
    ParameterType.BUFFER, ParameterType.BUFFER8, ParameterType.BUFFER16,
    ParameterType.BUFFER18, ParameterType.BUFFER32, ParameterType.BUFFER42,
    ParameterType.BUFFER100, ParameterType.LIST_UINT16, ParameterType.LIST_ROUTING_TABLE,
    ParameterType.LIST_BIND_TABLE, ParameterType.LIST_NEIGHBOR_LQI, ParameterType.LIST_NETWORK,
    ParameterType.LIST_ASSOC_DEV, ParameterType.LIST_UINT8,
]


class ZpiObject:
    def __init__(self, type, subsystem, command: str, commandId, payload, parameters):
        self.type = type
        self.subsystem = subsystem
        self.command = command
        self.command_id = commandId
        self.payload = payload
        self.parameters = parameters
        self.sequence = None

    def is_reset_command(self):
        return (self.command == "resetReq" and self.subsystem == Subsystem.SYS) or \
               (self.command == "systemReset" and self.subsystem == Subsystem.SAPI)

    def to_unpi_frame(self):
        data = Buffalo(b'')

        for p in self.parameters:
            value = self.payload[p['name']]
            data.write_parameter(p['parameterType'], value, {})

        return uart.UnpiFrame(self.type, self.subsystem, self.command_id, data.buffer)

    @classmethod
    def from_command(cls, type, subsystem, command, payload):
        cmd = next(
            c for c in Definition[subsystem] if c["name"] == command
        )
        parameters = (
            cmd["response"] if type == CommandType.SRSP else cmd["request"]
        )

        return cls(
            type, subsystem, cmd["name"], cmd["ID"], payload, parameters
        )

    @classmethod
    def from_unpi_frame(cls, frame):
        cmd = next(
            c for c in Definition[frame.subsystem] if c["ID"] == frame.command_id
        )
        parameters = (
            cmd["response"] if frame.type == CommandType.SRSP else cmd["request"]
        )
        payload = cls.read_parameters(frame.data, parameters)

        return cls(
            frame.type, frame.subsystem, cmd["name"], cmd["ID"], payload, parameters
        )

    @classmethod
    def from_cluster(cls, nwk, profile, cluster, src_ep, dst_ep, sequence, data):
        subsystem = Subsystem.from_cluster(profile, cluster)
        if profile == zha.PROFILE_ID:
            cluster = 1

        cmd = next(
            c for c in Definition[subsystem] if c["ID"] == cluster
        )
        name = cmd['name']
        parameters = (
            cmd["response"] if cmd["type"] == CommandType.SRSP else cmd["request"]
        )

        if name == 'dataRequest':
            payload = {
                'dstaddr': int(nwk),
                'destendpoint': dst_ep,
                'srcendpoint': src_ep,
                'clusterid': cluster,
                'transid': sequence,
                'options': 0,
                'radius': 0,
                'len': len(data),
                'data': data,
            }
        else:
            payload = cls.read_parameters(nwk.to_bytes(2, 'little') + data[1:], parameters)

        return cls(
            cmd["type"], subsystem, name, cmd["ID"], payload, parameters
        )

    @classmethod
    def read_parameters(cls, data: bytes, parameters):
        # print(parameters)
        buffalo = Buffalo(data)
        res = {}
        length = None
        startIndex = None
        for p in parameters:
            options = BuffaloOptions()
            if p["parameterType"] in BufferAndListTypes:
                # When reading a buffer, assume that the previous parsed parameter contains
                # the length of the buffer
                if isinstance(length, int):
                    options.length = length

                if p["parameterType"] == ParameterType.LIST_ASSOC_DEV:
                    # For LIST_ASSOC_DEV, we also need to grab the startindex which is right before the length
                    if isinstance(startIndex, int):
                        options.startIndex = startIndex

            res[p['name']] = buffalo.read_parameter(p["parameterType"], options)
            startIndex = length
            length = res[p['name']]

        return res

    def __str__(self) -> str:
        command_type = CommandType(self.type).name
        subsystem = Subsystem(self.subsystem).name
        return "{} {} {} {}".format(command_type, subsystem, self.command, self.payload)

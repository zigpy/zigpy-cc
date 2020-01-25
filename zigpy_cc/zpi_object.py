from zigpy.profiles import zha

from zigpy_cc import uart
from zigpy_cc.buffalo import Buffalo, BuffaloOptions
from zigpy_cc.definition import Definition
from zigpy_cc.types import CommandType, ParameterType, Subsystem

BufferAndListTypes = [
    ParameterType.BUFFER,
    ParameterType.BUFFER8,
    ParameterType.BUFFER16,
    ParameterType.BUFFER18,
    ParameterType.BUFFER32,
    ParameterType.BUFFER42,
    ParameterType.BUFFER100,
    ParameterType.LIST_UINT16,
    ParameterType.LIST_ROUTING_TABLE,
    ParameterType.LIST_BIND_TABLE,
    ParameterType.LIST_NEIGHBOR_LQI,
    ParameterType.LIST_NETWORK,
    ParameterType.LIST_ASSOC_DEV,
    ParameterType.LIST_UINT8,
]


class ZpiObject:
    def __init__(
        self,
        type,
        subsystem,
        command: str,
        commandId,
        payload,
        parameters,
        sequence=None,
    ):
        self.type = type
        self.subsystem = subsystem
        self.command = command
        self.command_id = commandId
        self.payload = payload
        self.parameters = parameters
        self.sequence = sequence

    def is_reset_command(self):
        return (self.command == "resetReq" and self.subsystem == Subsystem.SYS) or (
            self.command == "systemReset" and self.subsystem == Subsystem.SAPI
        )

    def to_unpi_frame(self):
        data = Buffalo(b"")

        for p in self.parameters:
            value = self.payload[p["name"]]
            data.write_parameter(p["parameterType"], value, {})

        return uart.UnpiFrame(self.type, self.subsystem, self.command_id, data.buffer)

    @classmethod
    def from_command(cls, subsystem, command, payload):
        cmd = next(c for c in Definition[subsystem] if c["name"] == command)
        parameters = (
            cmd["response"] if cmd["type"] == CommandType.SRSP else cmd["request"]
        )

        return cls(cmd["type"], subsystem, cmd["name"], cmd["ID"], payload, parameters)

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
    def from_cluster(
        cls, nwk, profile, cluster, src_ep, dst_ep, sequence, data, req_id, *, radius=30
    ):
        if profile == zha.PROFILE_ID:
            subsystem = Subsystem.AF
            cmd = next(c for c in Definition[subsystem] if c["ID"] == 1)
        else:
            subsystem = Subsystem.ZDO
            cmd = next(c for c in Definition[subsystem] if c["ID"] == cluster)
        name = cmd["name"]
        parameters = (
            cmd["response"] if cmd["type"] == CommandType.SRSP else cmd["request"]
        )

        if name == "dataRequest":
            payload = {
                "dstaddr": int(nwk),
                "destendpoint": dst_ep,
                "srcendpoint": src_ep,
                "clusterid": cluster,
                "transid": req_id,
                "options": 0,
                "radius": radius,
                "len": len(data),
                "data": data,
            }
        elif name == "mgmtPermitJoinReq":
            payload = cls.read_parameters(
                bytes([0x0F]) + nwk.to_bytes(2, "little") + data[1:], parameters
            )
        else:
            # TODO
            # assert sequence == data[0]
            payload = cls.read_parameters(
                nwk.to_bytes(2, "little") + data[1:], parameters
            )

        return cls(
            cmd["type"], subsystem, name, cmd["ID"], payload, parameters, sequence
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
            name = p["name"]
            if (
                name.endswith("addr")
                or name.endswith("address")
                or name.endswith("addrofinterest")
            ):
                options.is_address = True
            type = p["parameterType"]
            if type in BufferAndListTypes:
                if isinstance(length, int):
                    options.length = length

                if type == ParameterType.LIST_ASSOC_DEV:
                    if isinstance(startIndex, int):
                        options.startIndex = startIndex

            res[name] = buffalo.read_parameter(type, options)
            # For LIST_ASSOC_DEV, we need to grab the startindex which is
            # right before the length
            startIndex = length
            # When reading a buffer, assume that the previous parsed parameter
            # contains the length of the buffer
            length = res[name]

        return res

    def __repr__(self) -> str:
        command_type = CommandType(self.type).name
        subsystem = Subsystem(self.subsystem).name
        return "{} {} {} tsn: {} {}".format(
            command_type, subsystem, self.command, self.sequence, self.payload
        )

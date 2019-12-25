from zigpy_cc.types import Subsystem, CommandType, ParameterType

# todo transform typescript to python or JSON
# github: zigbee-herdsman/src/adapter/z-stack/znp/definition.ts

Definition = {
    Subsystem.SYS: [
        {
            "name": 'version',
            "ID": 2,
            "type": CommandType.SREQ,
            "request": [
            ],
            "response": [
                {"name": 'transportrev', "parameterType": ParameterType.UINT8},
                {"name": 'product', "parameterType": ParameterType.UINT8},
                {"name": 'majorrel', "parameterType": ParameterType.UINT8},
                {"name": 'minorrel', "parameterType": ParameterType.UINT8},
                {"name": 'maintrel', "parameterType": ParameterType.UINT8},
                {"name": 'revision', "parameterType": ParameterType.UINT32},
            ],
        }
    ],
    Subsystem.ZDO: [
        {
            "name": 'endDeviceAnnceInd',
            "ID": 193,
            "type": CommandType.AREQ,
            "request": [
                {"name": 'srcaddr', "parameterType": ParameterType.UINT16},
                {"name": 'nwkaddr', "parameterType": ParameterType.UINT16},
                {"name": 'ieeeaddr', "parameterType": ParameterType.IEEEADDR},
                {"name": 'capabilities', "parameterType": ParameterType.UINT8},
            ],
        },
        {
            "name": 'tcDeviceInd',
            "ID": 202,
            "type": CommandType.AREQ,
            "request": [
                {"name": 'nwkaddr', "parameterType": ParameterType.UINT16},
                {"name": 'extaddr', "parameterType": ParameterType.IEEEADDR},
                {"name": 'parentaddr', "parameterType": ParameterType.UINT16},
            ],
        }
    ]
}
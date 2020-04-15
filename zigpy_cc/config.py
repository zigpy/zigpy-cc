import voluptuous as vol
from zigpy.config import (  # noqa: F401 pylint: disable=unused-import
    CONF_DATABASE,
    CONF_DEVICE,
    CONF_DEVICE_PATH,
    CONFIG_SCHEMA,
    cv_boolean,
)

CONF_DEVICE_BAUDRATE = "baudrate"
CONF_DEVICE_BAUDRATE_DEFAULT = 115200
CONF_FLOW_CONTROL = "flow_control"
CONF_FLOW_CONTROL_DEFAULT = None

SCHEMA_DEVICE = vol.Schema(
    {
        vol.Required(CONF_DEVICE_PATH): vol.Any(vol.PathExists(), "auto"),
        vol.Optional(CONF_DEVICE_BAUDRATE, default=CONF_DEVICE_BAUDRATE_DEFAULT): int,
        vol.Optional(CONF_FLOW_CONTROL, default=CONF_FLOW_CONTROL_DEFAULT): vol.In(
            ("hardware", "software", None)
        ),
    }
)

CONFIG_SCHEMA = CONFIG_SCHEMA.extend({vol.Required(CONF_DEVICE): SCHEMA_DEVICE})

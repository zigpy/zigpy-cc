## Migration to v0.5 (HA v0.115)
Before version 0.5 we used fixed network options, now we are using network options from the config.

If you want to upgrade from 0.4 to 0.5 you have two options:
1. Repair you devices
2. Add network options to config

```yaml
zha:
  zigpy_config:
    network:
      channel: 11
      channels: [11]
      pan_id: 0x1A62
      extended_pan_id: "DD:DD:DD:DD:DD:DD:DD:DD"
```

# zigpy-cc

[![Build Status](https://travis-ci.org/sanyatuning/zigpy-cc.svg?branch=master)](https://travis-ci.org/sanyatuning/zigpy-cc)
[![Coverage](https://coveralls.io/repos/github/sanyatuning/zigpy-cc/badge.svg?branch=master)](https://coveralls.io/github/sanyatuning/zigpy-cc?branch=master)

[zigpy-cc](https://github.com/sanyatuning/zigpy-cc) is a Python 3 implementation for the [Zigpy](https://github.com/zigpy/) project to implement support for CC2531/CC2530 and possible other Texas Instruments [Zigbee](https://www.zigbee.org) radio modules flashed with custom Z-Stack coordinator firmware.

The goal of this project is to add native support for inexpensive CC2531 based USB sticks in Home Assistant ZHA integration via [Zigpy](https://github.com/zigpy/) to directly control compatible Zigbee HA (Home Automation) devices such as Philips HUE, GE, Osram Lightify, Xiaomi/Aqara, IKEA Tradfri, Samsung SmartThings, and many more.

- https://www.home-assistant.io/integrations/zha/

zigpy-cc allows Zigpy to interact with Texas Instruments CC253x Zigbee Network Processor(ZNP) via TI Z-Stack Monitor and Test(MT) APIs using an UART interface.

The zigpy-cc library is a port of the [zigbee-herdsman](https://github.com/Koenkk/zigbee-herdsman/tree/v0.12.24) project (version 0.12.24) by the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project by Koen Kanters (a.k.a. Koenkk GitHub) which in turn was originally forked from the [zigbee-shepherd](https://github.com/zigbeer/zigbee-shepherd) project by zigbeer. Therefore, if any improvements like support for new Zigbee devices that gets added in the Zigbee2MQTT project it could be possible to port those improvements and benifit much of that to the zigpy-cc library. 

## WARNING!!! - Work in progress
This project is under development as WIP (work in progress), it is not working yet.

TODO list:
- [x] uart communication
- [x] init coordinator
- [x] handling join requests
- [x] get node descriptor
- [x] get endpoint list
- [x] get endpoint info
- [ ] bind
- [ ] fix entities in Home Assistant
- [ ] fix lint problems
- [ ] add more tests
- [ ] ...more coming?

# Hardware requirement
The necessary hardware and equipment for flashing firmware and the device preparation process is best described by the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project whos community develops the custom Z-Stack coordinator firmware that zigpy-cc requires. They have intructions for several alternative metods on how to initially flash their Z-Stack coordinator firmware on a new CC253x based adapter that does not have a bootloader. They also have a FAQ and knowledgebase that can be useful for working with the supported hardware adapters/equipment and Zigbee devices.

- https://www.zigbee2mqtt.io/information/supported_adapters.html
- https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html
- https://www.zigbee2mqtt.io/getting_started/flashing_the_cc2531.html
- https://www.zigbee2mqtt.io/information/alternative_flashing_methods.html
- https://github.com/Koenkk/Z-Stack-firmware/tree/master/coordinator

# Releases via PyPI
Tagged versions will also be released via PyPI

- TODO

# External documentation and reference

- TODO

# How to contribute

If you are looking to make a code or documentation contribution to this project we suggest that you follow the steps in these guides:
- https://github.com/firstcontributions/first-contributions/blob/master/README.md
- https://github.com/firstcontributions/first-contributions/blob/master/github-desktop-tutorial.md

# Related projects

### Zigpy
[Zvigpy](https://github.com/zigpy/zigpy)** is **[Zigbee protocol stack](https://en.wikipedia.org/wiki/Zigbee)** integration project to implement the **[Zigbee Home Automation](https://www.zigbee.org/)** standard as a Python 3 library. Zigbee Home Automation integration with zigpy allows you to connect one of many off-the-shelf Zigbee adapters using one of the available Zigbee radio library modules compatible with zigpy to control Zigbee based devices. There is currently support for controlling Zigbee device types such as binary sensors (e.g., motion and door sensors), sensors (e.g., temperature sensors), lightbulbs, switches, and fans. A working implementation of zigbe exist in **[Home Assistant](https://www.home-assistant.io)** (Python based open source home automation software) as part of its **[ZHA component](https://www.home-assistant.io/components/zha/)**

### ZHA Device Handlers
ZHA deviation handling in Home Assistant relies on on the third-party [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) project. Zigbee devices that deviate from or do not fully conform to the standard specifications set by the [Zigbee Alliance](https://www.zigbee.org) may require the development of custom [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) (ZHA custom quirks handler implementation) to for all their functions to work properly with the ZHA component in Home Assistant. These ZHA Device Handlers for Home Assistant can thus be used to parse custom messages to and from non-compliant Zigbee devices. The custom quirks implementations for zigpy implemented as ZHA Device Handlers for Home Assistant are a similar concept to that of [Hub-connected Device Handlers for the SmartThings Classics platform](https://docs.smartthings.com/en/latest/device-type-developers-guide/) as well as that of [Zigbee-Shepherd Converters as used by Zigbee2mqtt](https://www.zigbee2mqtt.io/how_tos/how_to_support_new_devices.html), meaning they are each virtual representations of a physical device that expose additional functionality that is not provided out-of-the-box by the existing integration between these platforms.

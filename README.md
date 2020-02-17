# zigpy-cc

[![Build Status](https://travis-ci.org/sanyatuning/zigpy-cc.svg?branch=master)](https://travis-ci.org/sanyatuning/zigpy-cc)
[![Coverage](https://coveralls.io/repos/github/sanyatuning/zigpy-cc/badge.svg?branch=master)](https://coveralls.io/github/sanyatuning/zigpy-cc?branch=master)

[zigpy-cc](https://github.com/sanyatuning/zigpy-cc) is a Python 3 library implemention to add support for Texas Instruments CC series of [Zigbee](https://www.zigbee.org) radio module chips hardware to the [Zigpy](https://github.com/zigpy/) project. Including but possibly not limited to Texas Instruments CC253x, CC26x2R, and CC13x2 chips flashed with a custom Z-Stack coordinator firmware.

The goal of this project is to add native support for inexpensive Texas Instruments CC chip based USB sticks in Home Assistant's built-in ZHA (Zigbee Home Automation) integration component (via the [Zigpy](https://github.com/zigpy/) library), allowing Home Assistant with such hardware to nativly support direct control of compatible Zigbee devices such as Philips HUE, GE, Osram Lightify, Xiaomi/Aqara, IKEA Tradfri, Samsung SmartThings, and many more.

- https://www.home-assistant.io/integrations/zha/

zigpy-cc allows Zigpy to interact with Texas Instruments ZNP (Zigbee Network Processor) coordinator firmware via TI Z-Stack Monitor and Test(MT) APIs using an UART/serial interface.

The zigpy-cc library itself is a port of the [zigbee-herdsman](https://github.com/Koenkk/zigbee-herdsman/tree/v0.12.24) project (version 0.12.24) by the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project by Koen Kanters (a.k.a. Koenkk GitHub) which in turn was originally forked from the [zigbee-shepherd](https://github.com/zigbeer/zigbee-shepherd) project by zigbeer. Therefore, if any improvements like support for new Zigbee devices that gets added in the Zigbee2MQTT project it could be possible to port those improvements and benifit much of that to the zigpy-cc library. 

## WARNING!!! - Work in progress
Disclaimer: This software is provided "AS IS", without warranty of any kind. The zigpy-cc project is under development as WIP (work in progress), it is not fully working yet. 

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
The zigpy-cc library is currently being tested by developers with Texas Instruments CC2531 and CC2652R based adapters as as reference hardware but it should in theory be possible to get it working with work most USB-adapters and GPIO-modules based on Texas Instruments CC Zigbee radio module chips hardware. Note that you also have to flash the chip a custom Z-Stack coordinator firmware before you can use the hardware, read the firmware requirement section below.

## Hardware being tested by zigpy-cc developers
  - [CC2531 USB stick hardware flashed with custom Z-Stack coordinator firmware from the Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC2652R dev board hardware flashed with custom Z-Stack coordinator firmware from the Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  
 ## Hardware not yet tested by zigpy-cc developers
  - [CC2530 + CC2591 USB stick hardware flashed with custom Z-Stack coordinator firmware from the Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC2530 + CC2592 dev board hardware flashed with custom Z-Stack coordinator firmware from the Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC1352P-2 dev board hardware flashed with custom Z-Stack coordinator firmware from the Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC2538 + CC2592 dev board hardware flashed with custom Z-Stack coordinator firmware from the Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)  

## Firmware requirement
Firmware requirement is that they support Texas Instruments Z-Stack Monitor and Test(MT) APIs using an UART interface (serial communcation protocol), which they should do if they are flashed with custom Z-Stack "coordinator" firmware for Zigbee 1.2 or Zigbee 3.0 from the Zigbee2mqtt project.

- https://github.com/Koenkk/Z-Stack-firmware/tree/master/coordinator

The necessary hardware and equipment for flashing firmware and the device preparation process is best described by the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project whos community develops the custom Z-Stack coordinator firmware that this zigpy-cc libary requires.

The [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project has intructions for several alternative metods on how to initially flash their special Z-Stack coordinator firmware on a new CC253x, CC26x2R, CC13x2, CC2538 or other Texas Instruments CCxxxx based USB adapters and development boards that does not have a bootloader. They also have a FAQ and knowledgebase that can be useful for working with these supported hardware adapters/equipment as well as with Zigbee devices.

- https://www.zigbee2mqtt.io/information/supported_adapters.html
- https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html
- https://www.zigbee2mqtt.io/getting_started/flashing_the_cc2531.html
- https://www.zigbee2mqtt.io/information/alternative_flashing_methods.html

## Port configuration

- To configure __usb__ port path for your TI CC serial device, just specify the TTY (serial com) port, example : `/dev/ttyACM0`
    - Alternatively you could try to set just port to `auto` to enable automatic usb port discovery (not garanteed to work).
- Texas Instruments default recommend Baud rate of CC253x serial device is 115200 (this could be different for other TI CC chips).

# Releases via PyPI

Tagged versions will also be released via PyPI

- https://pypi.org/project/zigpy-cc/
    - https://pypi.org/project/zigpy-cc/#history
    - https://pypi.org/project/zigpy-cc/#files

# External documentation and reference

- http://www.ti.com/tool/LAUNCHXL-CC26X2R1
- http://www.ti.com/tool/LAUNCHXL-CC1352P

# How to contribute

If you are looking to make a code or documentation contribution to this project we suggest that you follow the steps in these guides:
- https://github.com/firstcontributions/first-contributions/blob/master/README.md
- https://github.com/firstcontributions/first-contributions/blob/master/github-desktop-tutorial.md

# Related projects

### Zigpy
[Zvigpy](https://github.com/zigpy/zigpy)** is **[Zigbee protocol stack](https://en.wikipedia.org/wiki/Zigbee)** integration project to implement the **[Zigbee Home Automation](https://www.zigbee.org/)** standard as a Python 3 library. Zigbee Home Automation integration with zigpy allows you to connect one of many off-the-shelf Zigbee adapters using one of the available Zigbee radio library modules compatible with zigpy to control Zigbee based devices. There is currently support for controlling Zigbee device types such as binary sensors (e.g., motion and door sensors), sensors (e.g., temperature sensors), lightbulbs, switches, and fans. A working implementation of zigbe exist in **[Home Assistant](https://www.home-assistant.io)** (Python based open source home automation software) as part of its **[ZHA component](https://www.home-assistant.io/components/zha/)**

### ZHA Device Handlers
ZHA deviation handling in Home Assistant relies on on the third-party [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) project. Zigbee devices that deviate from or do not fully conform to the standard specifications set by the [Zigbee Alliance](https://www.zigbee.org) may require the development of custom [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) (ZHA custom quirks handler implementation) to for all their functions to work properly with the ZHA component in Home Assistant. These ZHA Device Handlers for Home Assistant can thus be used to parse custom messages to and from non-compliant Zigbee devices. The custom quirks implementations for zigpy implemented as ZHA Device Handlers for Home Assistant are a similar concept to that of [Zigbee-Herdsman Converters / Zigbee-Shepherd Converters as used by Zigbee2mqtt](https://www.zigbee2mqtt.io/how_tos/how_to_support_new_devices.html) as well as that of [Hub-connected Device Handlers for the SmartThings Classics platform](https://docs.smartthings.com/en/latest/device-type-developers-guide/), meaning they are each virtual representations of a physical device that expose additional functionality that is not provided out-of-the-box by the existing integration between these platforms.

### ZHA Map
Home Assistant can build ZHA network topology map using the [zha-map](https://github.com/zha-ng/zha-map) project.

### zha-network-visualization-card
[zha-network-visualization-card](https://github.com/dmulcahey/zha-network-visualization-card) is a custom Lovelace element for visualizing the ZHA Zigbee network in Home Assistant.

### ZHA Network Card
[zha-network-card](https://github.com/dmulcahey/zha-network-card) is a custom Lovelace card that displays ZHA network and device information in Home Assistant

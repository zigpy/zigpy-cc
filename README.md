# zigpy-cc

[![Build Status](https://travis-ci.org/zigpy/zigpy-cc.svg?branch=master)](https://travis-ci.org/zigpy/zigpy-cc)
[![Coverage](https://coveralls.io/repos/github/zigpy/zigpy-cc/badge.svg?branch=master)](https://coveralls.io/github/zigpy/zigpy-cc?branch=master)

[zigpy-cc](https://github.com/zigpy/zigpy-cc) is a Python 3 library implemention to add support for Texas Instruments CC series of [Zigbee](https://www.zigbee.org) radio module chips hardware to the [zigpy](https://github.com/zigpy/) project. Including but possibly not limited to Texas Instruments CC253x, CC26x2R, and CC13x2 chips flashed with a custom Z-Stack coordinator firmware.

The goal of this project is to add native support for inexpensive Texas Instruments CC chip based USB sticks in Home Assistant's built-in ZHA (Zigbee Home Automation) integration component (via the [zigpy](https://github.com/zigpy/) library), allowing Home Assistant with such hardware to nativly support direct control of compatible Zigbee devices such as Philips HUE, GE, Osram Lightify, Xiaomi/Aqara, IKEA Tradfri, Samsung SmartThings, and many more.

- https://www.home-assistant.io/integrations/zha/

zigpy-cc allows Zigpy to interact with Texas Instruments ZNP (Zigbee Network Processor) coordinator firmware via TI Z-Stack Monitor and Test(MT) APIs using an UART/serial interface.

The zigpy-cc library itself contain port code from the [zigbee-herdsman](https://github.com/Koenkk/zigbee-herdsman/tree/v0.12.24) project (version 0.12.24) for the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project by Koen Kanters (a.k.a. Koenkk GitHub). The zigbee-herdsman library itself in turn was originally a fork and rewrite of the [zigbee-shepherd](https://github.com/zigbeer/zigbee-shepherd) library by the [Zigbeer](https://github.com/zigbeer) project. Therefore, if code improvements or bug-fixes gets commited to the [zigbee-herdsman](https://github.com/Koenkk/zigbee-herdsman) library then it could, in theory, also be possible to port some or many of those code improvements to this zigpy-cc library for its benifit.

## WARNING!!! - Work in progress
Disclaimer: This software is provided "AS IS", without warranty of any kind. The zigpy-cc project is under development as WIP (work in progress), it is not fully working yet. 

# Hardware requirement
The zigpy-cc library is currently being tested by developers with Texas Instruments CC2531 and CC2652R based adapters/boards as as reference hardware but it should in theory be possible to get it working with work most USB-adapters and GPIO-modules based on Texas Instruments CC Zigbee radio module chips hardware. Note that unless you bought pre-flashed with correct custom firmware you will also have to flash the chip a compatible Z-Stack coordinator firmware before you can use the hardware, please read the firmware requirement section below.

## Reference hardware being tested by zigpy-cc developers
  - [CC2531 USB stick hardware flashed with custom Z-Stack 1.2 coordinator firmware from Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC2652R dev board hardware flashed with custom Z-Stack 3.x coordinator firmware from Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  
 ## Hardware not activly tested by zigpy-cc developers
  - [CC2530 + CC2591 USB stick hardware flashed with custom Z-Stack 1.2 coordinator firmware from Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC2530 + CC2592 dev board hardware flashed with custom Z-Stack 1.2 coordinator firmware from Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC1352P-2 dev board hardware flashed with custom Z-Stack 3.0 coordinator firmware from Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  - [CC2538 + CC2592 dev board hardware flashed with custom Z-Stack 3.0 coordinator firmware from Zigbee2mqtt project](https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html)
  
## Firmware requirement
Firmware requirement is that they support Texas Instruments "Z-Stack Monitor and Test" APIs using an UART interface (serial communcation protocol), which they should do if they are flashed with custom Z-Stack "coordinator" firmware for Zigbee 1.2 or Zigbee 3.0 from the Zigbee2mqtt project.

- https://github.com/Koenkk/Z-Stack-firmware/tree/master/coordinator

The necessary hardware and equipment for flashing firmware and the device preparation process is best described by the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project whos community maintain and distribute a custom pre-compiled Z-Stack coordinator firmware (.hex files) for their [Zigbee-Heardsman](https://github.com/Koenkk/zigbee-herdsman/) libary which also makes it compatible with the zigpy-cc library.

CC253x based adapters/boards in general does not come with a bootloader from the factory so needs to first be hardware flashed with a pre-compiled Z-Stack coordinator firmware (.hex file) via a Texas Instruments CC Debugger or a DIY GPIO debug adapter using the official "SmartRF Flash-Programmer" (v1.1x) software from Texas Instruments, or comparative alternative metods and software.

CC13x2 and CC26x2 based adapters/boards in general already come with a bootloader from the factory so can be software flashed with a pre-compiled Z-Stack coordinator firmware (.hex file) directly over USB using the official "SmartRF Flash-Programmer-2" (v1.8+) or "UniFlash" (6.x) from Texas Instruments, or comparative alternative metods and software.

The [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project has step-by-step intructions for both flashing with Texas Instruments official software as well as several alternative metods on how to initially flash their custom Z-Stack coordinator firmware on a new CC253x, CC13x2, CC26x2 and other Texas Instruments CCxxxx based USB adapters and development boards that comes or do not come with a bootloader. 

- https://www.zigbee2mqtt.io/information/supported_adapters.html
- https://www.zigbee2mqtt.io/getting_started/what_do_i_need.html
- https://www.zigbee2mqtt.io/getting_started/flashing_the_cc2531.html
- https://www.zigbee2mqtt.io/information/alternative_flashing_methods.html

Note that the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project also have a FAQ and knowledgebase that can be useful for working with these Texas Instruments ZNP coordinator hardware adapters/equipment for their Z-Stack as well as lists Zigbee devices which should be supported.

## Port configuration

- To configure __usb__ port path for your TI CC serial device, just specify the TTY (serial com) port, example : `/dev/ttyACM0`
    - Alternatively you could try to set just port to `auto` to enable automatic usb port discovery (not garanteed to work).

Developers should note that Texas Instruments recommends different baud rates for UART interface of different TI CC chips.
- CC2530 and CC2531 default recommended UART baud rate is 115200 baud.
- CC2538 also supports flexible UART baud rate generation but only up to a maximum of 460800 baud.
- CC13x2 and CC26x2 support flexible UART baud rate generation up to a maximum of 1.5 Mbps.

# Toubleshooting 

For toubleshooting with Home Assistant, the general recommendation is to first only enable DEBUG logging for homeassistant.core and homeassistant.components.zha in Home Assistant, then look in the home-assistant.log file and try to get the Home Assistant community to exhausted their combined troubleshooting knowledge of the ZHA component before posting issue directly to a radio library like zigpy-cc.

That is, begin with checking debug logs for Home Assistant core and the ZHA component first, (troubleshooting/debugging from the top down instead of from the bottom up), trying to getting help via Home Assistant community forum before moving on to posting debug logs to zigpy and zigpy-cc. This is to general suggestion to help filter away common problems and not flood the zigpy-cc developer(s) with to many logs.

Please also try the very latest versions of zigpy and zigpy-cc, (see the section below about "Testing new releases"), and only if you still have the same issues with the latest versions then enable debug logging for zigpy and zigpy_cc in Home Assistant in addition to core and zha. Once enabled debug logging for all those libraries in Home Assistant you should try to reproduce the problem and then raise an issue in zigpy-cc repo with a copy of those logs.

To enable debugging in Home Assistant to get debug logs, either update logger configuration section in configuration.yaml or call logger.set_default_level service with {"level": "debug"} data. 

Check logger component configuration where you want something in your Home Assistant configuration.yaml like this: 
  ```
  logger:
  default: info
  logs:
  asyncio: debug
  homeassistant.core: debug
  homeassistant.components.zha: debug
  zigpy: debug
  zigpy_cc: debug
 ```

# Testing new releases

Testing a new release of the zigpy-cc library before it is released in Home Assistant.

If you are using Supervised Home Assistant (formerly known as the Hassio/Hass.io distro):
- Add https://github.com/home-assistant/hassio-addons-development as "add-on" repository
- Install "Custom deps deployment" addon
- Update config like: 
  ```
  pypi:
    - zigpy-cc==0.2.3
  apk: []
  ```
  where 0.2.3 is the new version
- Start the addon

This version will persist even so you update HA core.
You can remove custom deps with this config:
  ```
  pypi: []
  apk: []
  ```
  
If you are instead using some custom python installation of Home Assistant then do this:
- Activate your python virtual env
- Update package with ``pip``
  ```
  pip install zigpy-cc==0.2.3
  ```

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
**[zigpy](https://github.com/zigpy/zigpy)** is a [Zigbee protocol stack](https://en.wikipedia.org/wiki/Zigbee) integration project to implement the **[Zigbee Home Automation](https://www.zigbee.org/)** standard as a Python 3 library. Zigbee Home Automation integration with zigpy allows you to connect one of many off-the-shelf Zigbee adapters using one of the available Zigbee radio library modules compatible with zigpy to control Zigbee based devices. There is currently support for controlling Zigbee device types such as binary sensors (e.g., motion and door sensors), sensors (e.g., temperature sensors), lightbulbs, switches, and fans. A working implementation of zigbe exist in **[Home Assistant](https://www.home-assistant.io)** (Python based open source home automation software) as part of its **[ZHA component](https://www.home-assistant.io/components/zha/)**

### ZHA Device Handlers
ZHA deviation handling in Home Assistant relies on on the third-party [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) project. Zigbee devices that deviate from or do not fully conform to the standard specifications set by the [Zigbee Alliance](https://www.zigbee.org) may require the development of custom [ZHA Device Handlers](https://github.com/dmulcahey/zha-device-handlers) (ZHA custom quirks handler implementation) to for all their functions to work properly with the ZHA component in Home Assistant. These ZHA Device Handlers for Home Assistant can thus be used to parse custom messages to and from non-compliant Zigbee devices. The custom quirks implementations for zigpy implemented as ZHA Device Handlers for Home Assistant are a similar concept to that of [Zigbee-Herdsman Converters / Zigbee-Shepherd Converters as used by Zigbee2mqtt](https://www.zigbee2mqtt.io/how_tos/how_to_support_new_devices.html) as well as that of [Hub-connected Device Handlers for the SmartThings Classics platform](https://docs.smartthings.com/en/latest/device-type-developers-guide/), meaning they are each virtual representations of a physical device that expose additional functionality that is not provided out-of-the-box by the existing integration between these platforms.

### ZHA Map
Home Assistant can build ZHA network topology map using the [zha-map](https://github.com/zha-ng/zha-map) project.

### zha-network-visualization-card
[zha-network-visualization-card](https://github.com/dmulcahey/zha-network-visualization-card) is a custom Lovelace element for visualizing the ZHA Zigbee network in Home Assistant.

### ZHA Network Card
[zha-network-card](https://github.com/dmulcahey/zha-network-card) is a custom Lovelace card that displays ZHA network and device information in Home Assistant

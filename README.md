# zigpy-cc

[![Build Status](https://travis-ci.org/sanyatuning/zigpy-cc.svg?branch=master)](https://travis-ci.org/sanyatuning/zigpy-cc)
[![Coverage](https://coveralls.io/repos/github/sanyatuning/zigpy-cc/badge.svg?branch=master)](https://coveralls.io/github/sanyatuning/zigpy-cc?branch=master)

[zigpy-cc](https://github.com/sanyatuning/zigpy-cc) is a Python 3 implementation for the [Zigpy](https://github.com/zigpy/) project to implement support for Texas Instruments CC2531 [Zigbee](https://www.zigbee.org) radio modules. 

The goal of this project is to add native support for inexpensive CC2531 based USB sticks in Home Assistant via [Zigpy](https://github.com/zigpy/) to directly control Zigbee home automation devices such as Philips HUE, GE, Osram Lightify, Xiaomi/Aqara, IKEA Tradfri, Samsung SmartThings, and many more.

This library is a port of the [zigbee-herdsman](https://github.com/Koenkk/zigbee-herdsman/tree/v0.12.24) project (version 0.12.24) by Koen Kanters (a.k.a. Koenkk GitHub) which is turn was originally forked from the [zigbee-shepherd](https://github.com/zigbeer/zigbee-shepherd) project by zigbeer.

# Hardware requirement
For now best is to follow the instructions from the [Zigbee2mqtt](https://www.zigbee2mqtt.io/) project on what hardware is needed and how to flash a CC2531 USB stick with their custom Z-Stack firmware 
- https://www.zigbee2mqtt.io/
- https://github.com/Koenkk/Z-Stack-firmware

# Releases via PyPI
Tagged versions are also released via PyPI

- TODO

# External documentation and reference

- TODO

# How to contribute

If you are looking to make a contribution to this project we suggest that you follow the steps in these guides:
- https://github.com/firstcontributions/first-contributions/blob/master/README.md
- https://github.com/firstcontributions/first-contributions/blob/master/github-desktop-tutorial.md

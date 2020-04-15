"""Setup module for zigpy-cc"""

from setuptools import find_packages, setup

import zigpy_cc

setup(
    name="zigpy-cc",
    version=zigpy_cc.__version__,
    description="A library which communicates with "
    "Texas Instruments CC2531 radios for zigpy",
    url="http://github.com/sanyatuning/zigpy-cc",
    author="Balázs Sándor",
    author_email="sanyatuning@gmail.com",
    license="GPL-3.0",
    packages=find_packages(exclude=["*.tests"]),
    install_requires=["pyserial-asyncio", "zigpy>=0.20.a1"],
    tests_require=["asynctest", "pytest", "pytest-asyncio"],
)

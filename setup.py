"""Setup module for zigpy-cc"""

import os

from setuptools import find_packages, setup

import zigpy_cc

this_directory = os.path.join(os.path.abspath(os.path.dirname(__file__)))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="zigpy-cc",
    version=zigpy_cc.__version__,
    description="A library which communicates with "
    "Texas Instruments CC2531 radios for zigpy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/sanyatuning/zigpy-cc",
    author="Balázs Sándor",
    author_email="sanyatuning@gmail.com",
    license="GPL-3.0",
    packages=find_packages(exclude=["*.tests"]),
    install_requires=["pyserial-asyncio", "zigpy>=0.20.a1"],
    tests_require=["asynctest", "pytest", "pytest-asyncio"],
)

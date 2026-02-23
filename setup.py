#!/usr/bin/env python3
"""IoTwizz - IoT Pentesting Framework"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="iotwizz",
    version="1.0.0",
    author="Khushal Mistry",
    author_email="",
    description="IoTwizz - The Hardware Hacker's Playbook",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/khushalmistry/iotwizz",
    packages=find_packages(),
    package_data={
        "": ["data/*.json"],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "Intended Audience :: Information Technology",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "prompt-toolkit>=3.0.0",
        "pyserial>=3.5",
        "paho-mqtt>=1.6.0",
        "scapy>=2.5.0",
        "paramiko>=3.0.0",
        "requests>=2.28.0",
        "google-generativeai>=0.6.0",
        "openai>=1.0.0",
        "anthropic>=0.18.0"
    ],
    entry_points={
        "console_scripts": [
            "iotwizz=iotwizz.main:main",
        ],
    },
)

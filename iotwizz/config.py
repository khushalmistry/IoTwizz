"""
IoTwizz Configuration
"""

import os


class Config:
    """Global configuration for IoTwizz framework."""

    # Framework info
    APP_NAME = "IoTwizz"
    VERSION = "1.0.0"
    AUTHOR = "Khushal Mistry"

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    CREDS_FILE = os.path.join(DATA_DIR, "default_credentials.json")

    # Serial defaults
    DEFAULT_BAUD_RATES = [
        300, 1200, 2400, 4800, 9600, 14400, 19200, 28800,
        38400, 57600, 115200, 230400, 460800, 921600
    ]
    DEFAULT_SERIAL_TIMEOUT = 2

    # Network defaults
    DEFAULT_SSH_PORT = 22
    DEFAULT_TELNET_PORT = 23
    DEFAULT_HTTP_PORT = 80
    DEFAULT_FTP_PORT = 21
    DEFAULT_MQTT_PORT = 1883

    # U-Boot defaults
    UBOOT_INTERRUPT_KEYS = ["\n", " ", "\x1b", "1", "f", "s"]
    UBOOT_COMMON_BAUD = 115200

    # Console
    PROMPT = "\033[38;5;196miotwizz\033[0m"
    MODULE_PROMPT = "\033[38;5;196miotwizz\033[0m(\033[38;5;51m{module}\033[0m)"

    # Logging
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    LOG_LEVEL = "INFO"

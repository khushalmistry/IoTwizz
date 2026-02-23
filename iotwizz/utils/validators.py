"""
IoTwizz - Input Validation Helpers
"""

import os
import re


def validate_ip(ip: str) -> bool:
    """Validate an IPv4 address."""
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, ip):
        return False
    octets = ip.split(".")
    return all(0 <= int(o) <= 255 for o in octets)


def validate_port(port) -> bool:
    """Validate a port number."""
    try:
        port = int(port)
        return 1 <= port <= 65535
    except (ValueError, TypeError):
        return False


def validate_file_path(path: str) -> bool:
    """Validate that a file exists and is readable."""
    return os.path.isfile(path) and os.access(path, os.R_OK)


def validate_serial_port(port: str) -> bool:
    """Validate a serial port path exists."""
    return os.path.exists(port)


def validate_baud_rate(baud_rate) -> bool:
    """Validate a baud rate value."""
    try:
        baud = int(baud_rate)
        return baud > 0
    except (ValueError, TypeError):
        return False


def validate_required_options(options: dict) -> list:
    """Check that all required options have values.

    Args:
        options: Module options dict

    Returns:
        List of missing option names
    """
    missing = []
    for name, opt in options.items():
        if opt.get("required", False) and not opt.get("value"):
            missing.append(name)
    return missing

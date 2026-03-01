"""
IoTwizz Configuration
Global configuration management with workspace support.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Global configuration for IoTwizz framework with workspace support."""

    # Framework info
    APP_NAME = "IoTwizz"
    VERSION = "1.0.0"
    AUTHOR = "Khushal Mistry"

    # Determine base directory
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        BASE_DIR = sys._MEIPASS
        MODULES_DIR = os.path.join(BASE_DIR, "iotwizz", "modules")
    else:
        # Development/installation
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        MODULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")

    # Data directory
    DATA_DIR = os.path.join(BASE_DIR, "data")
    CREDS_FILE = os.path.join(DATA_DIR, "default_credentials.json")

    # User configuration directory
    USER_CONFIG_DIR = os.path.expanduser("~/.iotwizz")
    USER_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "config.json")
    WORKSPACE_FILE = os.path.join(USER_CONFIG_DIR, "workspace.json")

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
    DEFAULT_HTTPS_PORT = 443
    DEFAULT_FTP_PORT = 21
    DEFAULT_MQTT_PORT = 1883
    DEFAULT_MQTTS_PORT = 8883
    DEFAULT_COAP_PORT = 5683
    DEFAULT_COAPS_PORT = 5684

    # U-Boot defaults
    UBOOT_INTERRUPT_KEYS = ["s", "\n", " ", "\x1b", "1", "f"]
    UBOOT_COMMON_BAUD = 115200

    # Logging
    LOG_DIR = os.path.join(USER_CONFIG_DIR, "logs")
    LOG_LEVEL = "INFO"

    @classmethod
    def ensure_user_dirs(cls):
        """Ensure user configuration directories exist."""
        os.makedirs(cls.USER_CONFIG_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)

    @classmethod
    def load_user_config(cls) -> Dict[str, Any]:
        """Load user configuration file."""
        cls.ensure_user_dirs()
        
        if os.path.exists(cls.USER_CONFIG_FILE):
            try:
                with open(cls.USER_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return default config
        return {
            "default_target": "",
            "default_port": "",
            "default_baud_rate": "115200",
            "default_serial_port": "",
            "ai_provider": "gemini",
            "ai_model": "",
            "ai_api_key": "",
            "theme": "dark",
            "output_directory": os.path.expanduser("~/iotwizz-output"),
        }

    @classmethod
    def save_user_config(cls, config: Dict[str, Any]):
        """Save user configuration file."""
        cls.ensure_user_dirs()
        
        with open(cls.USER_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load_workspace(cls) -> Dict[str, Any]:
        """Load current workspace state."""
        cls.ensure_user_dirs()
        
        if os.path.exists(cls.WORKSPACE_FILE):
            try:
                with open(cls.WORKSPACE_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            "current_module": None,
            "module_options": {},
            "history": [],
            "findings": [],
            "notes": "",
            "target": "",
        }

    @classmethod
    def save_workspace(cls, workspace: Dict[str, Any]):
        """Save current workspace state."""
        cls.ensure_user_dirs()
        
        with open(cls.WORKSPACE_FILE, 'w') as f:
            json.dump(workspace, f, indent=2)

    @classmethod
    def get_output_dir(cls, subdir: Optional[str] = None) -> str:
        """Get the output directory path."""
        config = cls.load_user_config()
        output_dir = config.get("output_directory", os.path.expanduser("~/iotwizz-output"))
        
        if subdir:
            output_dir = os.path.join(output_dir, subdir)
        
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    @classmethod
    def get_log_file(cls) -> str:
        """Get the log file path."""
        cls.ensure_user_dirs()
        return os.path.join(cls.LOG_DIR, f"iotwizz_{time.strftime('%Y%m%d')}.log")


# Import time for get_log_file
import time

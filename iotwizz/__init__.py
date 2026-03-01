"""
IoTwizz - The Hardware Hacker's Playbook
A modular IoT security testing framework.

Version: 1.1.0
Author: Khushal Mistry
Repository: https://github.com/iotwizz/iotwizz
License: CC BY-NC 4.0
"""

__version__ = "1.1.0"
__author__ = "Khushal Mistry"
__email__ = ""
__license__ = "CC BY-NC 4.0"

__banner__ = """
\033[38;5;196m██\033[38;5;202m██\033[38;5;208m██\033[38;5;214m██\033[38;5;220m██\033[38;5;226m██\033[38;5;190m██\033[38;5;154m██\033[38;5;118m██\033[38;5;82m██\033[38;5;46m██\033[38;5;47m██\033[38;5;48m██\033[38;5;49m██\033[38;5;50m██\033[38;5;51m██\033[0m
\033[38;5;51m
  ___    _______          _         
 |_ _|__|_   _\ \  _  / (_)________
  | |/ _ \| |  \ \/ \/ / | |_  /_  /
  | | (_) | |   \  /\  / | |/ / / / 
 |___\___/|_|    \/  \/  |_/___/___|
                                     
\033[38;5;208m ⚡ The Hardware Hacker's Playbook v{version} ⚡\033[0m
\033[38;5;245m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[38;5;250m  Author:  {author}
  Modules: {modules} loaded
  Type 'help' for commands, 'ai' for AiWizz assistant
\033[38;5;245m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
"""

from iotwizz.config import Config

# Convenience imports
from iotwizz.base_module import BaseModule, StubModule
from iotwizz.module_loader import ModuleLoader

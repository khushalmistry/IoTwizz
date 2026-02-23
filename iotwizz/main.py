#!/usr/bin/env python3
"""
IoTwizz - IoT Pentesting Framework
Main entry point.

Usage:
    iotwizz          Launch interactive console
    iotwizz --help   Show help
    iotwizz --version Show version
"""

import sys
import argparse
from iotwizz import __version__


def main():
    """Main entry point for IoTwizz."""
    parser = argparse.ArgumentParser(
        prog="iotwizz",
        description="IoTwizz - The Hardware Hacker's Playbook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  iotwizz                    Launch interactive console
  iotwizz --version          Show version info

Inside the console:
  show modules               List all available modules
  use uart/baud_rate_finder   Select a module
  set PORT /dev/ttyUSB0       Set module options
  run                         Execute the module
  search uboot                Search for modules
  help                        Show all commands
        """,
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"IoTwizz v{__version__}",
    )

    args = parser.parse_args()

    # Launch interactive console
    try:
        from iotwizz.console import IoTwizzConsole
        console = IoTwizzConsole()
        console.start()
    except KeyboardInterrupt:
        print("\n\n  ⚡ IoTwizz out. Happy hacking! ⚡\n")
        sys.exit(0)
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()

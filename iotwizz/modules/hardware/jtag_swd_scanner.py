"""
IoTwizz Module: JTAG/SWD Scanner
Scan hardware debug interfaces using OpenOCD with comprehensive detection.
"""

import subprocess
import os
import re
import time
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator


class JtagSwdScanner(BaseModule):
    """Scan hardware debug interfaces using OpenOCD to detect JTAG/SWD."""

    # Common OpenOCD interface configs
    INTERFACE_CONFIGS = {
        "ft232h": "interface/ftdi/ft232h-module-swd.cfg",
        "ft2232": "interface/ftdi/ft2232.cfg",
        "jlink": "interface/jlink.cfg",
        "stlink": "interface/stlink.cfg",
        "stlink-v2": "interface/stlink-v2.cfg",
        "stlink-v2-1": "interface/stlink-v2-1.cfg",
        "cmsis-dap": "interface/cmsis-dap.cfg",
        "buspirate": "interface/buspirate.cfg",
        "ulink": "interface/ulink.cfg",
        "raspberrypi-native": "interface/raspberrypi-native.cfg",
        "sysfsgpio": "interface/sysfsgpio.cfg",
        "parport": "interface/parport.cfg",
    }

    def __init__(self):
        super().__init__()
        self.name = "JTAG/SWD Interface Scanner"
        self.description = "Detect and enumerate JTAG/SWD debug interfaces using OpenOCD"
        self.author = "IoTwizz Team"
        self.category = "hardware"

        self.options = {
            "ADAPTER": {
                "value": "stlink",
                "required": True,
                "description": "Debug adapter (stlink, jlink, ft232h, cmsis-dap, buspirate)",
            },
            "INTERFACE_TYPE": {
                "value": "swd",
                "required": True,
                "description": "Protocol: 'jtag' or 'swd'",
            },
            "SPEED": {
                "value": "1000",
                "required": False,
                "description": "Adapter speed in kHz (default: 1000)",
            },
            "TARGET": {
                "value": "",
                "required": False,
                "description": "Target config (e.g., stm32f4x, nrf52, esp32). Auto-detect if empty.",
            },
            "SCAN_CHAIN": {
                "value": "true",
                "required": False,
                "description": "Scan JTAG chain for connected devices (default: true)",
            },
            "AUTO_PROBE": {
                "value": "true",
                "required": False,
                "description": "Try multiple adapter configs automatically (default: true)",
            },
            "LIST_ADAPTERS": {
                "value": "false",
                "required": False,
                "description": "List available adapter configs and exit",
            },
        }

    def _check_openocd(self) -> bool:
        """Check if OpenOCD is installed."""
        return self._run_command(["openocd", "--version"], timeout=5)[0]

    def _run_command(self, cmd: list, timeout: int = 30) -> tuple:
        """Run a command and return (success, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return True, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except FileNotFoundError:
            return False, "", "Command not found"
        except Exception as e:
            return False, "", str(e)

    def run(self):
        """Run the JTAG/SWD scan."""
        list_adapters = (self.get_option("LIST_ADAPTERS") or "false").lower() == "true"
        
        if list_adapters:
            self._list_adapters()
            return

        adapter = self.get_option("ADAPTER").lower()
        protocol = self.get_option("INTERFACE_TYPE").lower()
        speed = self.get_option("SPEED")
        target = self.get_option("TARGET")
        scan_chain = (self.get_option("SCAN_CHAIN") or "true").lower() == "true"
        auto_probe = (self.get_option("AUTO_PROBE") or "true").lower() == "true"

        # Validate protocol
        if protocol not in ["jtag", "swd"]:
            error("INTERFACE_TYPE must be 'jtag' or 'swd'")
            info("  JTAG: Joint Test Action Group (4-5 wires, older standard)")
            info("  SWD: Serial Wire Debug (2 wires, ARM Cortex)")
            return

        # Check OpenOCD
        if not self._check_openocd():
            error("OpenOCD is not installed!")
            info("")
            info("Install OpenOCD:")
            info("  macOS:   brew install openocd")
            info("  Debian:  sudo apt install openocd")
            info("  Arch:    sudo pacman -S openocd")
            info("  Windows: Download from https://openocd.org/")
            return

        info(f"Protocol: [cyan]{protocol.upper()}[/cyan]")
        info(f"Adapter: [cyan]{adapter}[/cyan]")
        info(f"Speed: [cyan]{speed} kHz[/cyan]")
        console.print()

        if auto_probe:
            # Try multiple adapter configs
            adapters_to_try = [adapter]
            if adapter not in ["stlink", "jlink", "ft232h", "cmsis-dap"]:
                adapters_to_try = ["stlink", "jlink", "ft232h", "cmsis-dap"]
            
            for adapter_name in adapters_to_try:
                info(f"Trying adapter: [cyan]{adapter_name}[/cyan]...")
                
                if self._probe_with_adapter(adapter_name, protocol, speed, target, scan_chain):
                    return  # Success
            
            error("No debug interface detected with any adapter config")
            info("")
            info("Troubleshooting tips:")
            info("  1. Check physical connections (TCK/TMS/TDI/TDO for JTAG, SWDIO/SWCLK for SWD)")
            info("  2. Verify target is powered on")
            info("  3. Check voltage levels (3.3V vs 1.8V)")
            info("  4. Try different SPEED values (lower is safer)")
            info("  5. Ensure proper GND connection")
        else:
            self._probe_with_adapter(adapter, protocol, speed, target, scan_chain)

    def _probe_with_adapter(self, adapter: str, protocol: str, speed: str, 
                           target: str, scan_chain: bool) -> bool:
        """Attempt to probe with a specific adapter."""
        
        # Build OpenOCD commands
        commands = []
        
        # Interface config
        if adapter in self.INTERFACE_CONFIGS:
            config_file = self.INTERFACE_CONFIGS[adapter]
            commands.extend([
                "-f", config_file,
            ])
        else:
            # Try direct interface name
            commands.extend([
                "-c", f"interface {adapter}",
            ])
        
        # Transport
        commands.extend([
            "-c", f"transport select {protocol}",
            "-c", f"adapter speed {speed}",
        ])
        
        # Target config if specified
        if target:
            commands.extend(["-f", f"target/{target}.cfg"])
        
        # Init and scan
        commands.extend([
            "-c", "init",
        ])
        
        if scan_chain and protocol == "jtag":
            commands.extend(["-c", "scan_chain"])
        
        commands.extend([
            "-c", "targets",
            "-c", "exit"
        ])
        
        try:
            with console.status(f"[bold green]Probing with {adapter}...[/bold green]"):
                result = subprocess.run(
                    ["openocd"] + commands,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            output = result.stdout + result.stderr
            output_lower = output.lower()
            
            # Check for critical errors
            if "unable to open" in output_lower or "device not found" in output_lower:
                warning(f"  Adapter '{adapter}' not found or not connected")
                return False
            
            if "no device found" in output_lower:
                warning(f"  No debug device found with {adapter}")
                return False
            
            # Parse output for success indicators
            findings = []
            
            # Look for tap/device found
            tap_patterns = [
                r"tap/device found",
                r"found\s+(\d+)\s+taps?",
                r"idcode\s*=\s*0x([0-9a-fA-F]+)",
                r"detected\s+part\s+([^,\n]+)",
                r"IR\s+length\s+(\d+)",
                r"Target:\s*(\S+)",
                r"([^,\n]+)\s+detected",
            ]
            
            for pattern in tap_patterns:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    findings.extend([(pattern.replace(r"\s*", " ").strip(), m) for m in matches])
            
            # Look for IDCODE
            idcode_match = re.search(r"idcode\s*[=:]\s*0x([0-9a-fA-F]+)", output, re.IGNORECASE)
            if idcode_match:
                idcode = idcode_match.group(1)
                device_info = self._identify_device_from_idcode(int(idcode, 16))
                success(f"  Device IDCODE: [cyan]0x{idcode.upper()}[/cyan]")
                if device_info:
                    result(f"  Identified: [cyan]{device_info}[/cyan]")
            
            # Look for target info
            target_match = re.search(r"target\s+type\s*[=:]\s*(\S+)", output, re.IGNORECASE)
            if target_match:
                result(f"  Target type: [cyan]{target_match.group(1)}[/cyan]")
            
            # Look for CPU info
            cpu_match = re.search(r"cpu\s+type\s*[=:]\s*(\S+)", output, re.IGNORECASE)
            if cpu_match:
                result(f"  CPU type: [cyan]{cpu_match.group(1)}[/cyan]")
            
            if findings or "init mode succeeded" in output_lower:
                success(f"[bold green]Debug interface detected with {adapter}![/bold green]")
                console.print()
                
                # Show relevant output lines
                for line in output.split("\n"):
                    line_lower = line.lower()
                    if any(x in line_lower for x in ["found", "detected", "tap", "target", "idcode", "ir length"]):
                        if "error" not in line_lower and "warning" not in line_lower:
                            console.print(f"  [dim]{line.strip()}[/dim]")
                
                console.print()
                self._show_next_steps(adapter, protocol)
                return True
            
            elif "error" in output_lower:
                warning(f"  Errors detected with {adapter}")
                for line in output.split("\n"):
                    if "error" in line.lower():
                        console.print(f"    [dim red]{line.strip()}[/dim red]")
            else:
                warning(f"  No debug interface detected with {adapter}")
            
            return False
            
        except subprocess.TimeoutExpired:
            warning(f"  OpenOCD timed out with {adapter}")
            return False
        except Exception as e:
            error(f"  Error with {adapter}: {e}")
            return False

    def _identify_device_from_idcode(self, idcode: int) -> str:
        """Try to identify device from JTAG IDCODE."""
        # Common manufacturers and their IDCODE prefixes
        # This is a simplified lookup - full JTAG IDCODE database is much larger
        known_devices = {
            # ARM Cortex-M patterns
            0x0BB11477: "ARM Cortex-M3 (STM32F1)",
            0x1BA01477: "ARM Cortex-M3 r1p1",
            0x2BA01477: "ARM Cortex-M3 r2p0",
            0x0BC11477: "ARM Cortex-M4 (STM32F4)",
            0x0BB41477: "ARM Cortex-M4 r0p1",
            0x2BA01477: "ARM Cortex-M4 r0p0",
            0x0BE01477: "ARM Cortex-M7 (STM32F7)",
            0x5BA02477: "ARM Cortex-M7 r0p1",
            # STMicroelectronics
            0x06410041: "STM32F103xB",
            0x06420041: "STM32F103xE",
            0x06430041: "STM32F103xG",
            0x06460041: "STM32F40x/41x",
            0x06470041: "STM32F42x/43x",
            0x06480041: "STM32F7xx",
            0x06490041: "STM32F76x/77x",
            # Nordic
            0x00440041: "Nordic nRF51822",
            0x00460041: "Nordic nRF52832",
            0x00480041: "Nordic nRF52840",
            # ESP32
            0x00005c25: "ESP32",
            0x120034e5: "ESP32-S2",
            # NXP
            0x4c40417b: "NXP LPC1768",
            # Raspberry Pi Pico
            0x01002927: "Raspberry Pi RP2040",
        }
        
        # Try exact match first
        if idcode in known_devices:
            return known_devices[idcode]
        
        # Try manufacturer code (bits 1-11 of IDCODE)
        mfg_id = (idcode >> 1) & 0x7FF
        
        manufacturers = {
            0x017: "ARM Ltd",
            0x020: "STMicroelectronics",
            0x024: "Nordic Semiconductor",
            0x041: "NXP Semiconductor",
            0x047: "Broadcom (Raspberry Pi)",
            0x142: "Espressif Systems",
            0x01F: "Texas Instruments",
            0x00E: "Atmel/Microchip",
            0x015: "Cypress Semiconductor",
        }
        
        if mfg_id in manufacturers:
            return f"Unknown device by {manufacturers[mfg_id]}"
        
        return None

    def _show_next_steps(self, adapter: str, protocol: str):
        """Show helpful next steps after detection."""
        info("Next steps:")
        info(f"  1. Connect with GDB: [cyan]openocd -f interface/{adapter}.cfg -f target/<device>.cfg[/cyan]")
        info(f"  2. Debug with GDB: [cyan]target remote localhost:3333[/cyan]")
        info("  3. Flash firmware: [cyan]flash write_image erase <firmware.bin> 0x08000000[/cyan]")
        info("  4. Read memory: [cyan]mdw 0x08000000 256[/cyan]")
        console.print()
        result("Use 'help' in OpenOCD for more commands")

    def _list_adapters(self):
        """List available adapter configurations."""
        columns = [
            ("Adapter", "cyan"),
            ("Config File", "white"),
            ("Description", "dim"),
        ]
        
        descriptions = {
            "ft232h": "FTDI FT232H (MPSSE)",
            "ft2232": "FTDI FT2232 (MPSSE)",
            "jlink": "Segger J-Link",
            "stlink": "ST-Link (v2/v3)",
            "stlink-v2": "ST-Link v2",
            "stlink-v2-1": "ST-Link v2-1",
            "cmsis-dap": "CMSIS-DAP (DAPLink)",
            "buspirate": "Bus Pirate",
            "ulink": "Keil ULINK",
            "raspberrypi-native": "Raspberry Pi GPIO",
            "sysfsgpio": "Linux sysfs GPIO",
            "parport": "Parallel Port",
        }
        
        rows = []
        for adapter, config in self.INTERFACE_CONFIGS.items():
            desc = descriptions.get(adapter, "")
            rows.append((adapter, config, desc))
        
        print_table("Available Debug Adapters", columns, rows)
        info("")
        info("Usage: set ADAPTER <name>")
        info("Example: set ADAPTER stlink")

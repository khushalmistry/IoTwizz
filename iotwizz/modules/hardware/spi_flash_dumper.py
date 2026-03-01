"""
IoTwizz Module: SPI Flash Dumper
Read and dump firmware from SPI flash chips using flashrom or pyftdi.
Supports various programmers and chip detection.
"""

import os
import subprocess
import shutil
import time
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator


class SpiFlashDumper(BaseModule):
    """Extract firmware from SPI flash chips."""

    # Common programmers and their configurations
    PROGRAMMERS = {
        "ch341a_spi": {
            "name": "CH341A",
            "description": "CH341A USB programmer (common cheap programmer)",
            "speed": "slow",
        },
        "ft2232_spi": {
            "name": "FT2232/FT232H",
            "description": "FTDI FT2232H/FT232H (MPSSE)",
            "speed": "fast",
            "type_option": "type=232H",
        },
        "ft4232h_spi": {
            "name": "FT4232H",
            "description": "FTDI FT4232H (MPSSE)",
            "speed": "fast",
        },
        "buspirate_spi": {
            "name": "Bus Pirate",
            "description": "Bus Pirate (UART to SPI bridge)",
            "speed": "slow",
            "serial_option": True,
        },
        "usbblaster_spi": {
            "name": "USB-Blaster",
            "description": "Altera USB-Blaster",
            "speed": "medium",
        },
        "linux_spi": {
            "name": "Linux SPI",
            "description": "Linux /dev/spidev (e.g., Raspberry Pi)",
            "speed": "medium",
            "device_option": "/dev/spidev0.0",
        },
        "dediprog": {
            "name": "Dediprog SF100/SF600",
            "description": "Dediprog SF100/SF600",
            "speed": "fast",
        },
        "pickit2_spi": {
            "name": "PICkit2",
            "description": "Microchip PICkit2",
            "speed": "slow",
        },
        "stlinkv3_spi": {
            "name": "ST-Link V3",
            "description": "ST-Link V3 in SPI mode",
            "speed": "fast",
        },
    }

    # Common SPI flash chip signatures (JEDEC ID)
    CHIP_SIGNATURES = {
        # Winbond
        (0xEF, 0x40, 0x14): "W25Q80",
        (0xEF, 0x40, 0x15): "W25Q16",
        (0xEF, 0x40, 0x16): "W25Q32",
        (0xEF, 0x40, 0x17): "W25Q64",
        (0xEF, 0x40, 0x18): "W25Q128",
        (0xEF, 0x40, 0x19): "W25Q256",
        (0xEF, 0x60, 0x14): "W25Q80",
        (0xEF, 0x60, 0x15): "W25Q16",
        (0xEF, 0x60, 0x16): "W25Q32",
        (0xEF, 0x60, 0x17): "W25Q64",
        (0xEF, 0x60, 0x18): "W25Q128",
        # Macronix
        (0xC2, 0x20, 0x14): "MX25L8006E",
        (0xC2, 0x20, 0x15): "MX25L1606E",
        (0xC2, 0x20, 0x16): "MX25L3206E",
        (0xC2, 0x20, 0x17): "MX25L6406E",
        (0xC2, 0x20, 0x18): "MX25L12806E",
        (0xC2, 0x25, 0x36): "MX25L12835F",
        # Micron
        (0x20, 0x20, 0x14): "M25P80",
        (0x20, 0x20, 0x15): "M25P16",
        (0x20, 0x20, 0x16): "M25P32",
        (0x20, 0x20, 0x17): "M25P64",
        (0x20, 0x20, 0x18): "M25P128",
        (0x20, 0xBA, 0x17): "N25Q064",
        (0x20, 0xBA, 0x18): "N25Q128",
        (0x20, 0xBB, 0x18): "N25Q128A",
        # Spansion/Cypress
        (0x01, 0x02, 0x15): "S25FL016K",
        (0x01, 0x02, 0x16): "S25FL032K",
        (0x01, 0x02, 0x17): "S25FL064K",
        (0x01, 0x20, 0x18): "S25FL127S",
        (0x01, 0x40, 0x17): "S25FL064L",
        (0x01, 0x40, 0x18): "S25FL128L",
        # ISSI
        (0x9D, 0x60, 0x14): "IS25LP080D",
        (0x9D, 0x60, 0x15): "IS25LP016D",
        (0x9D, 0x60, 0x16): "IS25LP032D",
        (0x9D, 0x60, 0x17): "IS25LP064D",
        (0x9D, 0x60, 0x18): "IS25LP128D",
        # Adesto/Atmel
        (0x1F, 0x32, 0x15): "AT25SL161",
        (0x1F, 0x42, 0x16): "AT25SL321",
        (0x1F, 0x44, 0x01): "AT25SF041",
        (0x1F, 0x45, 0x01): "AT25SF081",
        (0x1F, 0x46, 0x01): "AT25SF161",
        # GigaDevice
        (0xC8, 0x40, 0x14): "GD25Q80",
        (0xC8, 0x40, 0x15): "GD25Q16",
        (0xC8, 0x40, 0x16): "GD25Q32",
        (0xC8, 0x40, 0x17): "GD25Q64",
        (0xC8, 0x40, 0x18): "GD25Q128",
        (0xC8, 0x60, 0x17): "GD25LQ64",
        (0xC8, 0x60, 0x18): "GD25LQ128",
    }

    # Common chip sizes in bytes
    CHIP_SIZES = {
        "W25Q80": 1 << 20,      # 1 MB
        "W25Q16": 2 << 20,      # 2 MB
        "W25Q32": 4 << 20,      # 4 MB
        "W25Q64": 8 << 20,      # 8 MB
        "W25Q128": 16 << 20,    # 16 MB
        "W25Q256": 32 << 20,    # 32 MB
        "MX25L8006E": 1 << 20,
        "MX25L1606E": 2 << 20,
        "MX25L3206E": 4 << 20,
        "MX25L6406E": 8 << 20,
        "MX25L12806E": 16 << 20,
        "M25P80": 1 << 20,
        "M25P16": 2 << 20,
        "M25P32": 4 << 20,
        "M25P64": 8 << 20,
        "M25P128": 16 << 20,
        "N25Q064": 8 << 20,
        "N25Q128": 16 << 20,
        "GD25Q80": 1 << 20,
        "GD25Q16": 2 << 20,
        "GD25Q32": 4 << 20,
        "GD25Q64": 8 << 20,
        "GD25Q128": 16 << 20,
    }

    def __init__(self):
        super().__init__()
        self.name = "SPI Flash Dumper"
        self.description = "Extract firmware from SPI flash chips using flashrom or direct programmer"
        self.author = "IoTwizz Team"
        self.category = "hardware"

        self.options = {
            "PROGRAMMER": {
                "value": "ch341a_spi",
                "required": True,
                "description": "Programmer type (use LIST_PROGRAMMERS=true to see options)",
            },
            "OUTPUT_FILE": {
                "value": "",
                "required": True,
                "description": "Output file path for dumped firmware",
            },
            "VERIFY": {
                "value": "true",
                "required": False,
                "description": "Verify dump after reading (default: true)",
            },
            "CHIP": {
                "value": "",
                "required": False,
                "description": "Force specific chip model (auto-detected if empty)",
            },
            "SERIAL_PORT": {
                "value": "",
                "required": False,
                "description": "Serial port for Bus Pirate (e.g., /dev/ttyUSB0)",
            },
            "SPI_DEVICE": {
                "value": "/dev/spidev0.0",
                "required": False,
                "description": "SPI device for linux_spi programmer",
            },
            "PROBE_ONLY": {
                "value": "false",
                "required": False,
                "description": "Only probe for chip, don't dump (default: false)",
            },
            "LIST_PROGRAMMERS": {
                "value": "false",
                "required": False,
                "description": "List available programmers and exit",
            },
            "SHOW_INFO": {
                "value": "true",
                "required": False,
                "description": "Show chip info after detection (default: true)",
            },
        }

    def _check_flashrom(self) -> bool:
        """Check if flashrom is installed."""
        return shutil.which("flashrom") is not None

    def run(self):
        """Run the SPI flash dump operation."""
        list_programmers = (self.get_option("LIST_PROGRAMMERS") or "false").lower() == "true"
        
        if list_programmers:
            self._list_programmers()
            return

        programmer = self.get_option("PROGRAMMER").lower()
        output_file = self.get_option("OUTPUT_FILE")
        verify = (self.get_option("VERIFY") or "true").lower() == "true"
        chip = self.get_option("CHIP")
        serial_port = self.get_option("SERIAL_PORT")
        spi_device = self.get_option("SPI_DEVICE")
        probe_only = (self.get_option("PROBE_ONLY") or "false").lower() == "true"
        show_info = (self.get_option("SHOW_INFO") or "true").lower() == "true"

        # Check flashrom
        if not self._check_flashrom():
            error("flashrom is not installed!")
            info("")
            info("Install flashrom:")
            info("  macOS:   brew install flashrom")
            info("  Debian:  sudo apt install flashrom")
            info("  Arch:    sudo pacman -S flashrom")
            info("  Windows: Download from https://flashrom.org/")
            return

        # Get programmer config
        prog_config = self.PROGRAMMERS.get(programmer, {})
        prog_name = prog_config.get("name", programmer)

        info(f"Programmer: [cyan]{prog_name}[/cyan]")
        info(f"Mode: {'Probe only' if probe_only else 'Full dump'}")
        console.print()

        # Build programmer argument
        prog_arg = programmer
        
        # Add programmer-specific options
        if programmer == "ft2232_spi" and prog_config.get("type_option"):
            prog_arg = f"{programmer}:{prog_config['type_option']}"
        elif programmer == "buspirate_spi" and serial_port:
            prog_arg = f"{programmer}:dev={serial_port}"
        elif programmer == "linux_spi" and spi_device:
            prog_arg = f"{programmer}:dev={spi_device}"
        
        # Build flashrom command
        cmd = ["flashrom", "-p", prog_arg]

        # Add chip if specified
        if chip:
            cmd.extend(["-c", chip])

        # Step 1: Probe for chip
        info("[bold]Step 1: Probing for SPI flash chip...[/bold]")
        
        try:
            with console.status("[bold green]Probing chip...[/bold green]"):
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            
            output = result.stdout + result.stderr
            
            # Parse output for detected chips
            detected_chips = []
            chip_lines = []
            
            for line in output.split("\n"):
                line_lower = line.lower()
                if "found" in line_lower and "flash chip" in line_lower:
                    chip_lines.append(line.strip())
                    # Try to extract chip name
                    chip_match = line.split("found")[-1].strip() if "found" in line else ""
                    if chip_match:
                        detected_chips.append(chip_match.split("(")[0].strip())
                elif "multiple flash chips" in line_lower:
                    warning("Multiple flash chips detected! Use CHIP option to specify.")
            
            if result.returncode != 0 and not chip_lines:
                # Check for common errors
                if "no programmer specified" in output.lower():
                    error("Invalid programmer configuration")
                elif "cannot open" in output.lower():
                    error("Cannot access programmer. Check permissions.")
                    if programmer == "linux_spi":
                        info("Try: sudo chmod 666 /dev/spidev0.0")
                    elif programmer == "ch341a_spi":
                        info("Ensure CH341A is connected and drivers are installed")
                elif "no flash chip found" in output.lower():
                    error("No SPI flash chip detected!")
                    info("")
                    info("Troubleshooting:")
                    info("  1. Check chip connections (CS, CLK, MISO, MOSI, VCC, GND)")
                    info("  2. Verify chip is powered (3.3V typically)")
                    info("  3. Check if chip write-protect is enabled")
                    info("  4. Try a different programmer if available")
                else:
                    error(f"Probe failed: {output[:200]}")
                return
            
            if chip_lines:
                for chip_line in chip_lines:
                    success(f"  {chip_line}")
            else:
                success("  Chip detected!")
            
            console.print()
            
            # Show chip info
            if show_info and detected_chips:
                self._show_chip_info(detected_chips[0] if detected_chips else None)
            
            if probe_only:
                console.print()
                success("Probe complete. Chip is accessible.")
                return
            
        except subprocess.TimeoutExpired:
            error("Probe timed out (>60s)")
            return
        except Exception as e:
            error(f"Probe failed: {e}")
            return

        # Step 2: Read chip
        if not output_file:
            error("OUTPUT_FILE is required for dumping")
            return
        
        # Create output directory if needed
        output_path = Path(output_file)
        if output_path.parent and not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        info("[bold]Step 2: Reading flash chip...[/bold]")
        info(f"  Output: [cyan]{os.path.abspath(output_file)}[/cyan]")
        
        read_cmd = cmd + ["-r", output_file]
        
        try:
            start_time = time.time()
            
            with console.status("[bold green]Reading flash... This may take several minutes.[/bold green]"):
                result = subprocess.run(
                    read_cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minute timeout
                )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0 or os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                success(f"  Read complete! ({self._format_size(file_size)} in {elapsed:.1f}s)")
                
                # Calculate hash
                with open(output_file, "rb") as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                result(f"  SHA256: [dim]{file_hash[:16]}...[/dim]")
                console.print()
                
                # Step 3: Verify
                if verify:
                    info("[bold]Step 3: Verifying dump...[/bold]")
                    
                    verify_cmd = cmd + ["-v", output_file]
                    
                    with console.status("[bold green]Verifying...[/bold green]"):
                        verify_result = subprocess.run(
                            verify_cmd,
                            capture_output=True,
                            text=True,
                            timeout=1800
                        )
                    
                    if verify_result.returncode == 0 and "verified" in verify_result.stdout.lower():
                        success("  Verification: [green]PASSED[/green]")
                    else:
                        warning("  Verification: [yellow]Could not verify[/yellow]")
                        if "content mismatch" in verify_result.stdout.lower():
                            error("  Verification: [red]FAILED - Content mismatch![/red]")
                
                console.print()
                print_separator()
                success("[bold green]SPI flash dump complete![/bold green]")
                result(f"  File: [cyan]{os.path.abspath(output_file)}[/cyan]")
                result(f"  Size: [cyan]{self._format_size(file_size)}[/cyan]")
                console.print()
                
                # Next steps
                info("Next steps:")
                info(f"  1. Analyze firmware: [cyan]iotwizz > use firmware/binwalk_analyzer[/cyan]")
                info(f"  2. Set FIRMWARE_FILE: [cyan]set FIRMWARE_FILE {os.path.abspath(output_file)}[/cyan]")
                info(f"  3. Search for strings: [cyan]strings {output_file} | less[/cyan]")
                
            else:
                error("Failed to read flash chip")
                if result.stderr:
                    for line in result.stderr.split("\n")[:5]:
                        if line.strip():
                            error(f"  {line}")
                
        except subprocess.TimeoutExpired:
            error("Read operation timed out (>30 minutes)")
        except Exception as e:
            error(f"Read failed: {e}")

    def _show_chip_info(self, chip_name: str = None):
        """Show information about the detected chip."""
        info("Chip Information:")
        
        if chip_name:
            result(f"  Detected: [cyan]{chip_name}[/cyan]")
            
            # Look up chip size
            for key, size in self.CHIP_SIZES.items():
                if key.lower() in chip_name.lower():
                    result(f"  Capacity: [cyan]{self._format_size(size)}[/cyan]")
                    break
            
            # Check if it's a known chip
            for jedec_id, name in self.CHIP_SIGNATURES.items():
                if name.lower() in chip_name.lower():
                    result(f"  JEDEC ID: [cyan]{jedec_id[0]:02X} {jedec_id[1]:02X} {jedec_id[2]:02X}[/cyan]")
                    break

    def _list_programmers(self):
        """List available programmers."""
        columns = [
            ("Programmer", "cyan"),
            ("Name", "white"),
            ("Description", "dim"),
            ("Speed", "yellow"),
        ]
        
        rows = []
        for prog_id, config in self.PROGRAMMERS.items():
            rows.append((
                prog_id,
                config.get("name", prog_id),
                config.get("description", "")[:40],
                config.get("speed", "unknown"),
            ))
        
        print_table("Available SPI Programmers", columns, rows)
        
        info("")
        info("Usage: set PROGRAMMER <type>")
        info("Examples:")
        info("  set PROGRAMMER ch341a_spi")
        info("  set PROGRAMMER ft2232_spi:type=232H")
        info("  set PROGRAMMER buspirate_spi:dev=/dev/ttyUSB0")
        info("  set PROGRAMMER linux_spi:dev=/dev/spidev0.0")

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

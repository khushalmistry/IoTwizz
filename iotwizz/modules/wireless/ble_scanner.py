"""
IoTwizz Module: BLE Scanner
Comprehensive Bluetooth Low Energy device scanner with service enumeration.
Discovers devices, services, and characteristics for security assessment.
"""

import asyncio
import time
from typing import List, Dict, Optional
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator


class BleScanner(BaseModule):
    """Scan and analyze Bluetooth Low Energy devices."""

    # Common BLE service UUIDs
    SERVICE_UUIDS = {
        "00001800-0000-1000-8000-00805f9b34fb": "Generic Access",
        "00001801-0000-1000-8000-00805f9b34fb": "Generic Attribute",
        "00001802-0000-1000-8000-00805f9b34fb": "Immediate Alert",
        "00001803-0000-1000-8000-00805f9b34fb": "Link Loss",
        "00001804-0000-1000-8000-00805f9b34fb": "Tx Power",
        "00001805-0000-1000-8000-00805f9b34fb": "Current Time Service",
        "00001806-0000-1000-8000-00805f9b34fb": "Reference Time Update",
        "00001807-0000-1000-8000-00805f9b34fb": "Next DST Change",
        "00001808-0000-1000-8000-00805f9b34fb": "Glucose",
        "00001809-0000-1000-8000-00805f9b34fb": "Health Thermometer",
        "0000180a-0000-1000-8000-00805f9b34fb": "Device Information",
        "0000180d-0000-1000-8000-00805f9b34fb": "Heart Rate",
        "0000180f-0000-1000-8000-00805f9b34fb": "Battery Service",
        "00001812-0000-1000-8000-00805f9b34fb": "Human Interface Device",
        "00001813-0000-1000-8000-00805f9b34fb": "Scan Parameters",
        "00001814-0000-1000-8000-00805f9b34fb": "User Data",
        "00001816-0000-1000-8000-00805f9b34fb": "Cycling Speed and Cadence",
        "00001818-0000-1000-8000-00805f9b34fb": "Cycling Power",
        "00001819-0000-1000-8000-00805f9b34fb": "Location and Navigation",
        "0000181a-0000-1000-8000-00805f9b34fb": "Environmental Sensing",
        "0000181b-0000-1000-8000-00805f9b34fb": "Body Composition",
        "0000181c-0000-1000-8000-00805f9b34fb": "User Data",
        "0000181d-0000-1000-8000-00805f9b34fb": "Weight Scale",
        "0000181e-0000-1000-8000-00805f9b34fb": "Bond Management",
        "0000181f-0000-1000-8000-00805f9b34fb": "Continuous Glucose Monitoring",
        "00001820-0000-1000-8000-00805f9b34fb": "Internet Protocol Support",
        "00001821-0000-1000-8000-00805f9b34fb": "Indoor Positioning",
        "00001822-0000-1000-8000-00805f9b34fb": "Pulse Oximeter",
        "00001823-0000-1000-8000-00805f9b34fb": "HTTP Proxy",
        "00001824-0000-1000-8000-00805f9b34fb": "Transport Discovery",
        "00001825-0000-1000-8000-00805f9b34fb": "Object Transfer",
        # Common IoT services
        "0000fef5-0000-1000-8000-00805f9b34fb": "Anki Drive",
        "0000fef6-0000-1000-8000-00805f9b34fb": "Anki Drive",
        "f000ffc0-0451-4000-b000-000000000000": "TI Sensor Tag",
        "f000ffc1-0451-4000-b000-000000000000": "TI Sensor Tag",
        "be15bee0-6186-40e4-9d71-44395f1d0001": "August Smart Lock",
        "9faoofaa-f28b-11e8-b4ef-0ed5f89f718b": "Generic IoT",
    }

    # Characteristic properties flags
    CHAR_PROPS = {
        0x01: "Broadcast",
        0x02: "Read",
        0x04: "Write without Response",
        0x08: "Write",
        0x10: "Notify",
        0x20: "Indicate",
        0x40: "Auth Signed Write",
        0x80: "Extended Properties",
    }

    def __init__(self):
        super().__init__()
        self.name = "Bluetooth LE Scanner"
        self.description = "Comprehensive BLE device discovery, service enumeration, and security analysis"
        self.author = "IoTwizz Team"
        self.category = "wireless"

        self.options = {
            "TIMEOUT": {
                "value": "10",
                "required": False,
                "description": "Scan duration in seconds (default: 10)",
            },
            "ENUMERATE": {
                "value": "true",
                "required": False,
                "description": "Enumerate services and characteristics (default: true)",
            },
            "RSSI_FILTER": {
                "value": "-100",
                "required": False,
                "description": "Minimum RSSI to include (default: -100, all devices)",
            },
            "NAME_FILTER": {
                "value": "",
                "required": False,
                "description": "Filter by device name (substring match)",
            },
            "UUID_FILTER": {
                "value": "",
                "required": False,
                "description": "Filter by service UUID (partial match)",
            },
            "CONNECT": {
                "value": "false",
                "required": False,
                "description": "Connect to devices for deeper enumeration (slower)",
            },
            "READ_CHARS": {
                "value": "false",
                "required": False,
                "description": "Read readable characteristics (requires CONNECT=true)",
            },
            "OUTPUT_FILE": {
                "value": "",
                "required": False,
                "description": "Save results to JSON file",
            },
            "CONTINUOUS": {
                "value": "false",
                "required": False,
                "description": "Continuous scanning mode (Ctrl+C to stop)",
            },
        }

    def run(self):
        """Run the BLE scanner."""
        try:
            import bleak
        except ImportError:
            error("bleak is not installed. Run: pip install bleak")
            return

        timeout = self.get_option_int("TIMEOUT", default=10)
        enumerate_services = (self.get_option("ENUMERATE") or "true").lower() == "true"
        rssi_filter = self.get_option_int("RSSI_FILTER", default=-100)
        name_filter = (self.get_option("NAME_FILTER") or "").lower()
        uuid_filter = (self.get_option("UUID_FILTER") or "").lower()
        connect = (self.get_option("CONNECT") or "false").lower() == "true"
        read_chars = (self.get_option("READ_CHARS") or "false").lower() == "true"
        output_file = self.get_option("OUTPUT_FILE")
        continuous = (self.get_option("CONTINUOUS") or "false").lower() == "true"

        info(f"Scan duration: [cyan]{timeout if not continuous else 'unlimited'} seconds[/cyan]")
        info(f"RSSI filter: [cyan]{rssi_filter} dBm[/cyan]")
        if name_filter:
            info(f"Name filter: [cyan]{name_filter}[/cyan]")
        if uuid_filter:
            info(f"UUID filter: [cyan]{uuid_filter}[/cyan]")
        console.print()

        # Run async scan
        try:
            if continuous:
                self._continuous_scan(enumerate_services, rssi_filter, name_filter, 
                                      uuid_filter, connect, read_chars)
            else:
                asyncio.run(self._scan(timeout, enumerate_services, rssi_filter, 
                                       name_filter, uuid_filter, connect, read_chars))
        except RuntimeError as e:
            if "already running" in str(e):
                error("Cannot run BLE scan: an asyncio event loop is already running.")
                info("Try running IoTwizz from a standard terminal (not Jupyter/IDE).")
            else:
                error(f"BLE Scan failed: {e}")
        except KeyboardInterrupt:
            console.print()
            warning("Scan interrupted by user")
        except Exception as e:
            error(f"BLE Scan failed: {e}")
            info("Ensure Bluetooth is enabled and you have the necessary permissions.")
            info("Linux: sudo may be required, or add user to 'bluetooth' group")
            info("macOS: Grant Bluetooth permission in System Preferences")

    async def _scan(self, timeout: int, enumerate_services: bool, rssi_filter: int,
                    name_filter: str, uuid_filter: str, connect: bool, read_chars: bool):
        """Perform a BLE scan."""
        try:
            from bleak import BleakScanner
        except ImportError:
            error("bleak not installed")
            return

        devices = []
        discovered_devices = {}

        info(f"[bold]Scanning for BLE devices ({timeout}s)...[/bold]")
        console.print()

        try:
            async with console.status("[bold green]Scanning...[/bold green]"):
                # Use detection callback for real-time updates
                def detection_callback(device, advertisement_data):
                    # Apply filters
                    if device.rssi and device.rssi < rssi_filter:
                        return
                    if name_filter and device.name:
                        if name_filter not in device.name.lower():
                            return
                    
                    addr = device.address
                    if addr not in discovered_devices:
                        discovered_devices[addr] = {
                            "address": addr,
                            "name": device.name or "Unknown",
                            "rssi": device.rssi,
                            "metadata": {},
                            "services": [],
                        }
                        result(f"  Found: [cyan]{device.name or 'Unknown'}[/cyan] ({addr}) RSSI: [yellow]{device.rssi} dBm[/yellow]")
                    else:
                        # Update RSSI if we see it again
                        if device.rssi:
                            discovered_devices[addr]["rssi"] = device.rssi
                    
                    # Store advertisement data
                    if advertisement_data:
                        if advertisement_data.service_uuids:
                            discovered_devices[addr]["services"] = list(set(
                                discovered_devices[addr]["services"] + list(advertisement_data.service_uuids)
                            ))
                        if advertisement_data.manufacturer_data:
                            discovered_devices[addr]["metadata"]["manufacturer_data"] = advertisement_data.manufacturer_data

                scanner = BleakScanner(detection_callback)
                await scanner.start()
                await asyncio.sleep(timeout)
                await scanner.stop()

        except Exception as e:
            error(f"Scan error: {e}")
            return

        devices = list(discovered_devices.values())

        if not devices:
            warning("No BLE devices found")
            info("Troubleshooting:")
            info("  1. Ensure Bluetooth is enabled")
            info("  2. Check device is powered on and advertising")
            info("  3. Try moving closer to the device")
            info("  4. Linux: run with sudo or add user to 'bluetooth' group")
            return

        console.print()
        success(f"Found [bold]{len(devices)}[/bold] BLE device(s)")
        console.print()

        # Display results
        columns = [
            ("Address", "cyan"),
            ("Name", "white"),
            ("RSSI", "yellow"),
            ("Services", "dim"),
        ]
        rows = []
        for d in sorted(devices, key=lambda x: x["rssi"] or -100, reverse=True):
            services_preview = ", ".join(d["services"][:3])
            if len(d["services"]) > 3:
                services_preview += f" (+{len(d['services']) - 3})"
            rows.append((
                d["address"],
                d["name"][:25] if d["name"] else "Unknown",
                f"{d['rssi']} dBm" if d['rssi'] else "N/A",
                services_preview[:30],
            ))

        print_table("Discovered BLE Devices", columns, rows)

        # Filter by UUID if specified
        if uuid_filter:
            devices = [d for d in devices if any(uuid_filter in s.lower() for s in d["services"])]

        # Enumerate services if requested
        if enumerate_services and devices:
            console.print()
            info("[bold]Enumerating services...[/bold]")
            
            for device in devices[:5]:  # Limit to first 5 devices for enumeration
                await self._enumerate_device(device, connect, read_chars)

        # Output to file
        if output_file:
            self._save_results(devices, output_file)

    async def _enumerate_device(self, device: dict, connect: bool, read_chars: bool):
        """Enumerate services and characteristics for a device."""
        try:
            from bleak import BleakClient
        except ImportError:
            return

        addr = device["address"]
        name = device["name"]
        
        info(f"\n  [cyan]{name}[/cyan] ({addr})")
        
        if not connect:
            # Just show advertised services
            if device["services"]:
                for uuid in device["services"]:
                    service_name = self.SERVICE_UUIDS.get(uuid.lower(), "Unknown Service")
                    result(f"    • {uuid[:8]}... - {service_name}")
            return

        # Connect and enumerate
        try:
            async with BleakClient(addr, timeout=10) as client:
                success(f"    Connected!")
                
                services = await client.get_services()
                
                for service in services:
                    uuid = service.uuid
                    service_name = self.SERVICE_UUIDS.get(uuid.lower(), "Custom Service")
                    result(f"    • Service: {service_name}")
                    result(f"      UUID: {uuid}")
                    
                    for char in service.characteristics:
                        props = []
                        for bit, prop_name in self.CHAR_PROPS.items():
                            if char.properties & bit:
                                props.append(prop_name)
                        
                        char_info = f"        → {char.uuid[:8]}... [{', '.join(props)}]"
                        console.print(f"      [dim]{char_info}[/dim]")
                        
                        # Try to read if readable
                        if read_chars and "Read" in props:
                            try:
                                value = await client.read_gatt_char(char.uuid)
                                value_str = self._format_value(value)
                                console.print(f"          [green]Value: {value_str}[/green]")
                            except Exception:
                                pass

        except asyncio.TimeoutError:
            warning(f"    Connection timeout")
        except Exception as e:
            warning(f"    Could not connect: {str(e)[:50]}")

    def _format_value(self, value: bytes) -> str:
        """Format a characteristic value for display."""
        if not value:
            return "(empty)"
        
        # Try as UTF-8 string
        try:
            decoded = value.decode('utf-8')
            if decoded.isprintable():
                return f'"{decoded}"'
        except UnicodeDecodeError:
            pass
        
        # Try as hex
        if len(value) <= 8:
            return f"0x{value.hex()}"
        else:
            return f"{value.hex()[:20]}... ({len(value)} bytes)"

    async def _continuous_scan(self, enumerate_services: bool, rssi_filter: int,
                               name_filter: str, uuid_filter: str, connect: bool, read_chars: bool):
        """Continuous BLE scanning mode."""
        try:
            from bleak import BleakScanner
        except ImportError:
            return

        discovered_devices = {}

        info("[bold]Starting continuous scan (Ctrl+C to stop)...[/bold]")
        console.print()

        def detection_callback(device, advertisement_data):
            if device.rssi and device.rssi < rssi_filter:
                return
            if name_filter and device.name:
                if name_filter not in device.name.lower():
                    return

            addr = device.address
            if addr not in discovered_devices:
                discovered_devices[addr] = {
                    "address": addr,
                    "name": device.name or "Unknown",
                    "rssi": device.rssi,
                    "first_seen": time.time(),
                    "last_seen": time.time(),
                }
                result(f"  [+] {device.name or 'Unknown'} ({addr}) RSSI: {device.rssi} dBm")
            else:
                discovered_devices[addr]["last_seen"] = time.time()
                if device.rssi:
                    discovered_devices[addr]["rssi"] = device.rssi

        scanner = BleakScanner(detection_callback)
        
        try:
            await scanner.start()
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await scanner.stop()

        return list(discovered_devices.values())

    def _save_results(self, devices: List[dict], output_file: str):
        """Save scan results to JSON file."""
        import json
        
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "device_count": len(devices),
                    "devices": devices,
                }, f, indent=2)
            success(f"Results saved to [cyan]{output_file}[/cyan]")
        except Exception as e:
            error(f"Failed to save results: {e}")

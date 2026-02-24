"""
IoTwizz Module: BLE Scanner
Scan and discover Bluetooth Low Energy devices.
"""
import asyncio
try:
    from bleak import BleakScanner
except ImportError:
    pass
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, print_table, console

class BleScanner(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "Bluetooth LE Scanner"
        self.description = "Discover nearby Bluetooth Low Energy devices"
        self.author = "IoTwizz Team"
        self.category = "wireless"
        
        self.options = {
            "TIMEOUT": {
                "value": "10",
                "required": True,
                "description": "Scan duration in seconds",
            }
        }
        
    def run(self):
        try:
            import bleak
        except ImportError:
            error("bleak is not installed. Run: pip install bleak")
            return
            
        timeout = int(self.get_option("TIMEOUT"))
        info(f"Scanning for BLE devices for {timeout} seconds...")
        
        async def scan():
            devices = await BleakScanner.discover(timeout=timeout)
            
            if not devices:
                warning("No BLE devices found.")
                return
                
            success(f"Found {len(devices)} devices:")
            
            columns = [
                ("MAC Address / UUID", "cyan"),
                ("Name", "white"),
                ("RSSI", "yellow"),
            ]
            
            rows = []
            for d in devices:
                name = d.name or "Unknown"
                rssi = str(d.rssi) + " dBm"
                rows.append((d.address, name, rssi))
                
            print_table("BLE Devices Discovered", columns, rows)
            
            # Additional details
            console.print("\n[dim]Device Details:[/dim]")
            for d in devices:
                if d.details or d.metadata:
                    console.print(f"  [cyan]{d.address}[/cyan] UUIDs: {d.metadata.get('uuids', [])}")
        
        try:
            asyncio.run(scan())
        except Exception as e:
            error(f"BLE Scan failed: {e}")
            info("Ensure Bluetooth is enabled and you have sufficient privileges.")

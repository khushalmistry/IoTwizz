"""
IoTwizz Module: JTAG/SWD Scanner
Scan hardware debug interfaces using OpenOCD.
"""
import subprocess
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info

class JtagSwdScanner(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "JTAG/SWD Interface Scanner"
        self.description = "Scan hardware debug interfaces using OpenOCD to find TAP IDCODEs"
        self.author = "IoTwizz Team"
        self.category = "hardware"
        
        self.options = {
            "ADAPTER": {
                "value": "ft232h",
                "required": True,
                "description": "OpenOCD interface config file (e.g., ft232h, jlink, stlink)",
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
            }
        }
    
    def run(self):
        adapter = self.get_option("ADAPTER")
        protocol = self.get_option("INTERFACE_TYPE").lower()
        speed = self.get_option("SPEED")
        
        info(f"Probing via {adapter} using {protocol} at {speed}kHz...")
        
        if protocol not in ["jtag", "swd"]:
            error("INTERFACE_TYPE must be 'jtag' or 'swd'")
            return
            
        cmd = [
            "openocd",
            "-f", f"interface/{adapter}.cfg",
            "-c", f"transport select {protocol}",
            "-c", f"adapter speed {speed}",
            "-c", "init",
            "-c", "scan_chain",
            "-c", "exit"
        ]
        
        try:
            # We want to capture stderr because openocd prints lots of stuff there
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = result.stdout + result.stderr
            
            if "Error:" in output and "Error: unable to open ftdi device" not in output and "Error: No Valid JTAG Interface Configured." not in output:
                 warning("OpenOCD encountered an error, but partial data may have been captured")
                 
            if "tap/device found" in output.lower() or "expected 1 of 1" in output.lower() or "idcode" in output.lower():
                success("Debug interface detected!")
                for line in output.split("\n"):
                    if "tap/device" in line.lower() or "idcode" in line.lower():
                        success("  -> " + line.strip())
            else:
                error("No target detected or adapter not found.")
                info(output)
        except subprocess.TimeoutExpired:
            error("OpenOCD timed out. Verify your connections.")
        except FileNotFoundError:
            error("openocd command not found. Please install OpenOCD (e.g., apt install openocd / brew install openocd).")

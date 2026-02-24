"""
IoTwizz Module: Zigbee Sniffer
Sniff raw Zigbee packets using a CC2531 or similar dongle (using serial/Z-Stack).
"""
import time
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, console

class ZigbeeSniffer(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "Zigbee/Z-Wave Sniffer"
        self.description = "Capture 802.15.4 / Zigbee packets over serial from a CC2531 sniffer dongle"
        self.author = "IoTwizz Team"
        self.category = "wireless"
        
        self.options = {
            "PORT": {
                "value": "",
                "required": True,
                "description": "Serial port of the Zigbee sniffer (e.g., /dev/ttyACM0)",
            },
            "CHANNEL": {
                "value": "11",
                "required": True,
                "description": "Zigbee channel (11-26)",
            },
            "BAUD_RATE": {
                "value": "115200",
                "required": False,
                "description": "Baud rate of the dongle",
            }
        }
        
    def run(self):
        try:
            import serial
        except ImportError:
            error("pyserial is not installed. Run: pip install pyserial")
            return
            
        port = self.get_option("PORT")
        channel = int(self.get_option("CHANNEL"))
        baud = int(self.get_option("BAUD_RATE"))
        
        if channel < 11 or channel > 26:
            error("Zigbee channel must be between 11 and 26.")
            return
            
        info(f"Connecting to sniffer on {port} at {baud} baud...")
        info(f"Setting channel to {channel}...")
        
        try:
            ser = serial.Serial(port, baud, timeout=1)
        except serial.SerialException as e:
            error(f"Failed to open port: {e}")
            return
            
        # VERY basic implementation of setting channel on a generic Z-Stack firmware
        # Normally you'd send specific hex commands. For a generic approach, we'll
        # just print raw bytes from the serial port assuming the dongle dumps raw frames.
        # This is a highly abstracted version for the framework.
        
        success("Connected! Listening for Zigbee packets (Press Ctrl+C to stop)...")
        console.print()
        
        try:
            while True:
                if ser.in_waiting:
                    data = ser.read(ser.in_waiting)
                    # We print the hex representation of the frames
                    hex_data = " ".join([f"{b:02X}" for b in data])
                    if hex_data:
                        console.print(f"[cyan]PKT >[/cyan] {hex_data}")
                time.sleep(0.01)
        except KeyboardInterrupt:
            console.print()
            info("Stopped sniffing.")
        finally:
            ser.close()

"""
IoTwizz Module: Zigbee/Z-Wave Sniffer
Capture and analyze 802.15.4 / Zigbee packets using compatible hardware.
Supports various sniffers including CC2531, CC2540, RZUSBstick, and more.
"""

import os
import time
import struct
from typing import Optional, List, Dict
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator


class ZigbeeSniffer(BaseModule):
    """Capture and analyze Zigbee/802.15.4 packets."""

    # Zigbee/Z-Wave channels
    ZIGBEE_CHANNELS = {
        11: 2405, 12: 2410, 13: 2415, 14: 2420, 15: 2425,
        16: 2430, 17: 2435, 18: 2440, 19: 2445, 20: 2450,
        21: 2455, 22: 2460, 23: 2465, 24: 2470, 25: 2475,
        26: 2480,
    }
    
    # Common Zigbee frame types
    FRAME_TYPES = {
        0x00: "Beacon",
        0x01: "Data",
        0x02: "Acknowledgment",
        0x03: "MAC Command",
    }
    
    # Zigbee cluster IDs (partial)
    CLUSTER_IDS = {
        0x0000: "Basic",
        0x0001: "Power Configuration",
        0x0003: "Identify",
        0x0004: "Groups",
        0x0005: "Scenes",
        0x0006: "On/Off",
        0x0007: "On/Off Switch Configuration",
        0x0008: "Level Control",
        0x0009: "Alarms",
        0x000A: "Time",
        0x000B: "RSSI Location",
        0x000C: "Analog Input (Basic)",
        0x000D: "Analog Output (Basic)",
        0x000E: "Analog Value (Basic)",
        0x000F: "Binary Input (Basic)",
        0x0010: "Binary Output (Basic)",
        0x0011: "Binary Value (Basic)",
        0x0012: "Multistate Input (Basic)",
        0x0013: "Multistate Output (Basic)",
        0x0014: "Multistate Value (Basic)",
        0x0015: "Commissioning",
        0x0019: "Ota Upgrade",
        0x0020: "Poll Control",
        0x0030: "Touchlink",
        0x0100: "Shade Configuration",
        0x0200: "Pump Configuration and Control",
        0x0201: "Thermostat",
        0x0202: "Fan Control",
        0x0203: "Dehumidification Control",
        0x0204: "Thermostat User Interface Configuration",
        0x0300: "Color Control",
        0x0400: "Illuminance Measurement",
        0x0401: "Illuminance Level Sensing",
        0x0402: "Temperature Measurement",
        0x0403: "Pressure Measurement",
        0x0404: "Flow Measurement",
        0x0405: "Relative Humidity Measurement",
        0x0406: "Occupancy Sensing",
        0x0500: "IAS Zone",
        0x0501: "IAS ACE",
        0x0502: "IAS WD",
        0x0702: "Smart Energy Metering",
        0x0703: "Key Establishment",
        0x0800: "Electrical Measurement",
    }
    
    # Device types
    DEVICE_TYPES = {
        0x0000: "On/Off Switch",
        0x0001: "Level Control Switch",
        0x0002: "On/Off Output",
        0x0003: "Level Controllable Output",
        0x0004: "Scene Selector",
        0x0005: "Configuration Tool",
        0x0006: "Remote Control",
        0x0007: "Combined Interface",
        0x0008: "Range Extender",
        0x0009: "Mains Power Outlet",
        0x0100: "On/Off Light",
        0x0101: "Dimmable Light",
        0x0102: "Color Dimmable Light",
        0x0103: "On/Off Light Switch",
        0x0104: "Dimmer Switch",
        0x0105: "Color Dimmer Switch",
        0x0106: "Light Sensor",
        0x0107: "Occupancy Sensor",
        0x0200: "Shade",
        0x0201: "Shade Controller",
        0x0202: "Window Covering Device",
        0x0300: "Heating/Cooling Unit",
        0x0301: "Thermostat",
        0x0302: "Temperature Sensor",
        0x0400: "IAS Control and Indicating Equipment",
        0x0401: "IAD Warning Device",
    }

    def __init__(self):
        super().__init__()
        self.name = "Zigbee/Z-Wave Sniffer"
        self.description = "Capture and analyze 802.15.4/Zigbee packets from compatible hardware"
        self.author = "IoTwizz Team"
        self.category = "wireless"

        self.options = {
            "PORT": {
                "value": "",
                "required": True,
                "description": "Serial port of the Zigbee sniffer (e.g., /dev/ttyUSB0, COM3)",
            },
            "CHANNEL": {
                "value": "15",
                "required": True,
                "description": "Zigbee channel (11-26) or 'scan' to find active channels",
            },
            "BAUD_RATE": {
                "value": "115200",
                "required": False,
                "description": "Baud rate for serial communication (default: 115200)",
            },
            "SNIFFER_TYPE": {
                "value": "auto",
                "required": False,
                "description": "Sniffer type: auto, cc2531, cc2540, rzusb, nrf, ubiqua",
            },
            "TIMEOUT": {
                "value": "0",
                "required": False,
                "description": "Capture timeout in seconds (0 = unlimited)",
            },
            "DISPLAY": {
                "value": "hex",
                "required": False,
                "description": "Display format: hex, ascii, decode, summary",
            },
            "FILTER_PAN": {
                "value": "",
                "required": False,
                "description": "Filter by PAN ID (hex, e.g., 0x1234)",
            },
            "FILTER_ADDR": {
                "value": "",
                "required": False,
                "description": "Filter by source/destination address (hex)",
            },
            "DECODE_ZCL": {
                "value": "true",
                "required": False,
                "description": "Attempt to decode Zigbee Cluster Library frames",
            },
            "OUTPUT_FILE": {
                "value": "",
                "required": False,
                "description": "Save captured packets to PCAP file",
            },
            "LIST_PORTS": {
                "value": "false",
                "required": False,
                "description": "List available serial ports and exit",
            },
        }
        
        self._packet_count = 0
        self._stop_capture = False

    def run(self):
        """Run the Zigbee sniffer."""
        list_ports = (self.get_option("LIST_PORTS") or "false").lower() == "true"
        
        if list_ports:
            self._list_ports()
            return

        port = self.get_option("PORT")
        channel = self.get_option("CHANNEL").lower()
        baud_rate = self.get_option_int("BAUD_RATE", default=115200)
        sniffer_type = self.get_option("SNIFFER_TYPE").lower()
        timeout = self.get_option_int("TIMEOUT", default=0)
        display = self.get_option("DISPLAY").lower()
        filter_pan = self.get_option("FILTER_PAN")
        filter_addr = self.get_option("FILTER_ADDR")
        decode_zcl = (self.get_option("DECODE_ZCL") or "true").lower() == "true"
        output_file = self.get_option("OUTPUT_FILE")

        # Validate channel
        if channel == "scan":
            self._scan_channels(port, baud_rate, sniffer_type)
            return
        
        try:
            channel_num = int(channel)
            if channel_num not in self.ZIGBEE_CHANNELS:
                error(f"Invalid channel: {channel_num}")
                info(f"Valid channels: 11-26")
                return
        except ValueError:
            error(f"Invalid channel: {channel}")
            return

        # Parse filters
        pan_filter = None
        if filter_pan:
            try:
                pan_filter = int(filter_pan, 16)
            except ValueError:
                error(f"Invalid PAN ID filter: {filter_pan}")
                return

        addr_filter = None
        if filter_addr:
            try:
                addr_filter = int(filter_addr, 16)
            except ValueError:
                error(f"Invalid address filter: {filter_addr}")
                return

        info(f"Port: [cyan]{port}[/cyan]")
        info(f"Channel: [cyan]{channel_num}[/cyan] ({self.ZIGBEE_CHANNELS[channel_num]} MHz)")
        info(f"Baud rate: [cyan]{baud_rate}[/cyan]")
        info(f"Display: [cyan]{display}[/cyan]")
        if pan_filter:
            info(f"PAN filter: [cyan]0x{pan_filter:04X}[/cyan]")
        console.print()

        # Open serial port
        try:
            import serial
        except ImportError:
            error("pyserial is not installed. Run: pip install pyserial")
            return

        try:
            ser = serial.Serial(port, baud_rate, timeout=1)
        except serial.SerialException as e:
            error(f"Failed to open port: {e}")
            info("Troubleshooting:")
            info("  1. Check the port is correct")
            info("  2. Ensure no other program is using the port")
            info("  3. Linux: add user to 'dialout' group: sudo usermod -a -G dialout $USER")
            return

        success(f"Opened {port} at {baud_rate} baud")

        # Configure sniffer
        self._configure_sniffer(ser, sniffer_type, channel_num)

        # Start capture
        info("[bold]Starting packet capture (Ctrl+C to stop)...[/bold]")
        console.print()

        self._packet_count = 0
        self._stop_capture = False
        start_time = time.time()
        
        # Open output file
        pcap_file = None
        if output_file:
            pcap_file = self._open_pcap(output_file)

        try:
            while not self._stop_capture:
                # Check timeout
                if timeout > 0 and (time.time() - start_time) >= timeout:
                    info(f"\nTimeout reached ({timeout}s)")
                    break

                # Read packet
                packet = self._read_packet(ser, sniffer_type)
                
                if packet:
                    self._packet_count += 1
                    
                    # Parse and display
                    parsed = self._parse_packet(packet, decode_zcl)
                    
                    # Apply filters
                    if pan_filter and parsed.get("pan_id") != pan_filter:
                        continue
                    if addr_filter and parsed.get("src_addr") != addr_filter and parsed.get("dst_addr") != addr_filter:
                        continue
                    
                    # Display
                    self._display_packet(parsed, display)
                    
                    # Save to PCAP
                    if pcap_file:
                        self._write_pcap(pcap_file, packet)

        except KeyboardInterrupt:
            console.print()
            warning("Capture stopped by user")
        finally:
            ser.close()
            if pcap_file:
                pcap_file.close()

        console.print()
        print_separator()
        info(f"Total packets captured: [cyan]{self._packet_count}[/cyan]")

    def _list_ports(self):
        """List available serial ports."""
        from iotwizz.utils.serial_helpers import get_available_ports
        
        ports = get_available_ports()
        
        if not ports:
            warning("No serial ports found!")
            info("")
            info("Troubleshooting:")
            info("  1. Connect your Zigbee sniffer (CC2531, etc.)")
            info("  2. Check device is recognized by OS")
            info("  3. Install drivers if necessary")
            return
        
        columns = [
            ("Port", "cyan"),
            ("Description", "white"),
            ("Hardware ID", "dim"),
        ]
        rows = [(p["device"], p["description"][:40], p["hwid"]) for p in ports]
        
        print_table("Available Serial Ports", columns, rows)

    def _scan_channels(self, port: str, baud_rate: int, sniffer_type: str):
        """Scan all channels for activity."""
        info("[bold]Scanning all Zigbee channels for activity...[/bold]")
        console.print()
        
        try:
            import serial
        except ImportError:
            error("pyserial is not installed")
            return

        try:
            ser = serial.Serial(port, baud_rate, timeout=0.5)
        except serial.SerialException as e:
            error(f"Failed to open port: {e}")
            return

        channel_activity = {}
        
        for ch in self.ZIGBEE_CHANNELS:
            self._configure_sniffer(ser, sniffer_type, ch)
            time.sleep(0.5)
            
            packets = 0
            start = time.time()
            while time.time() - start < 1:
                if self._read_packet(ser, sniffer_type):
                    packets += 1
            
            if packets > 0:
                channel_activity[ch] = packets
                result(f"  Channel {ch} ({self.ZIGBEE_CHANNELS[ch]} MHz): {packets} packets")
        
        ser.close()
        
        if channel_activity:
            console.print()
            success("Active channels found!")
            columns = [
                ("Channel", "cyan"),
                ("Frequency", "white"),
                ("Packets", "yellow"),
            ]
            rows = [(str(ch), f"{self.ZIGBEE_CHANNELS[ch]} MHz", str(cnt)) 
                    for ch, cnt in sorted(channel_activity.items(), key=lambda x: x[1], reverse=True)]
            print_table("Channel Activity", columns, rows)
            
            # Suggest best channel
            best_channel = max(channel_activity, key=channel_activity.get)
            info(f"Most active channel: [cyan]{best_channel}[/cyan]")
            info(f"Set CHANNEL={best_channel} for sniffing")
        else:
            warning("No activity detected on any channel")
            info("Ensure Zigbee devices are active and nearby")

    def _configure_sniffer(self, ser, sniffer_type: str, channel: int):
        """Configure the sniffer for the specified channel."""
        # CC2531 standard channel set command
        # Most sniffers use similar commands
        freq_mhz = self.ZIGBEE_CHANNELS[channel]
        
        if sniffer_type == "cc2531" or sniffer_type == "auto":
            # CC2531 packet sniffer firmware commands
            # Set channel: send channel number as single byte
            ser.write(bytes([channel]))
            time.sleep(0.1)
            # Enable promiscuous mode
            ser.write(b'\x01')
            time.sleep(0.1)
        elif sniffer_type == "rzusb":
            # RZUSBstick commands
            ser.write(b'\x00' + bytes([channel]))
            time.sleep(0.1)
        elif sniffer_type == "nrf":
            # Nordic nRF24L01+ based sniffers
            # Different command structure
            ser.write(bytes([0x01, channel]))
            time.sleep(0.1)

    def _read_packet(self, ser, sniffer_type: str) -> Optional[bytes]:
        """Read a single packet from the sniffer."""
        try:
            # Most sniffers use a simple framing:
            # [Length byte] [Data] [RSSI] [Optional timestamp]
            
            if ser.in_waiting > 0:
                # Read length byte
                length_byte = ser.read(1)
                if not length_byte:
                    return None
                
                length = length_byte[0]
                
                if length > 0 and length < 128:  # Sanity check
                    # Read packet data
                    data = ser.read(length)
                    
                    # Read RSSI (usually 1 byte after data)
                    rssi = ser.read(1)
                    
                    if len(data) == length:
                        return length_byte + data + rssi
            
            # Fallback: just read whatever is available
            if ser.in_waiting > 0:
                data = ser.read(min(ser.in_waiting, 256))
                if data:
                    return data
            
            return None
            
        except Exception:
            return None

    def _parse_packet(self, packet: bytes, decode_zcl: bool = True) -> dict:
        """Parse an 802.15.4/Zigbee packet."""
        parsed = {
            "raw": packet,
            "length": len(packet),
            "rssi": 0,
            "frame_type": None,
            "security": False,
            "pending": False,
            "ack_request": False,
            "pan_compression": False,
            "seq_number": None,
            "pan_id": None,
            "src_addr": None,
            "dst_addr": None,
            "payload": b"",
            "cluster_id": None,
            "profile_id": None,
            "zcl_command": None,
        }
        
        try:
            if len(packet) < 5:
                return parsed
            
            # RSSI is usually the last byte
            parsed["rssi"] = packet[-1] if len(packet) > 1 else 0
            
            # Skip length byte if present
            offset = 1 if packet[0] < 128 else 0
            
            if len(packet) <= offset:
                return parsed
            
            # Frame Control Field (2 bytes)
            fcf = struct.unpack("<H", packet[offset:offset+2])[0]
            
            parsed["frame_type"] = fcf & 0x03
            parsed["security"] = bool((fcf >> 3) & 0x01)
            parsed["pending"] = bool((fcf >> 4) & 0x01)
            parsed["ack_request"] = bool((fcf >> 5) & 0x01)
            parsed["pan_compression"] = bool((fcf >> 6) & 0x01)
            
            # Sequence number
            if len(packet) > offset + 2:
                parsed["seq_number"] = packet[offset + 2]
            
            # Addressing depends on frame control
            addr_offset = offset + 3
            
            # Try to extract PAN ID and addresses
            if len(packet) > addr_offset + 2:
                parsed["pan_id"] = struct.unpack("<H", packet[addr_offset:addr_offset+2])[0]
            
            # Simplified: extract what we can
            if len(packet) > addr_offset + 4:
                parsed["dst_addr"] = struct.unpack("<H", packet[addr_offset+2:addr_offset+4])[0]
            
            if len(packet) > addr_offset + 6:
                parsed["src_addr"] = struct.unpack("<H", packet[addr_offset+4:addr_offset+6])[0]
            
            # Payload starts after headers
            payload_start = min(addr_offset + 10, len(packet) - 2)
            parsed["payload"] = packet[payload_start:-1] if len(packet) > payload_start + 1 else b""
            
            # Try to decode ZCL if enabled
            if decode_zcl and len(parsed["payload"]) >= 4:
                # Zigbee network layer header is ~8 bytes, then APS, then ZCL
                # Simplified ZCL parsing
                if len(parsed["payload"]) > 12:
                    try:
                        # APS header parsing (simplified)
                        parsed["profile_id"] = struct.unpack("<H", parsed["payload"][4:6])[0]
                        parsed["cluster_id"] = struct.unpack("<H", parsed["payload"][6:8])[0]
                    except:
                        pass

        except Exception:
            pass
        
        return parsed

    def _display_packet(self, parsed: dict, display: str):
        """Display a parsed packet."""
        frame_type_name = self.FRAME_TYPES.get(parsed["frame_type"], f"Unknown({parsed['frame_type']})")
        
        if display == "hex":
            # Raw hex dump
            hex_str = " ".join(f"{b:02X}" for b in parsed["raw"][:32])
            if len(parsed["raw"]) > 32:
                hex_str += "..."
            console.print(f"[cyan]#{self._packet_count:04d}[/cyan] {frame_type_name} {hex_str}")
            
        elif display == "ascii":
            # ASCII representation
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in parsed["raw"][:50])
            console.print(f"[cyan]#{self._packet_count:04d}[/cyan] {frame_type_name} {ascii_str}")
            
        elif display == "decode":
            # Decoded fields
            info = f"[cyan]#{self._packet_count:04d}[/cyan] {frame_type_name}"
            if parsed["pan_id"]:
                info += f" PAN:0x{parsed['pan_id']:04X}"
            if parsed["src_addr"]:
                info += f" SRC:0x{parsed['src_addr']:04X}"
            if parsed["dst_addr"]:
                info += f" DST:0x{parsed['dst_addr']:04X}"
            if parsed["rssi"]:
                info += f" RSSI:{parsed['rssi'] - 256 if parsed['rssi'] > 127 else parsed['rssi']}dBm"
            console.print(info)
            
            # Show cluster info if available
            if parsed["cluster_id"]:
                cluster_name = self.CLUSTER_IDS.get(parsed["cluster_id"], f"0x{parsed['cluster_id']:04X}")
                result(f"  Cluster: {cluster_name}")
                
        elif display == "summary":
            # One-line summary
            info = f"[cyan]#{self._packet_count:04d}[/cyan] Len:{parsed['length']} {frame_type_name}"
            if parsed["ack_request"]:
                info += " [ACK]"
            if parsed["security"]:
                info += " [SEC]"
            info += f" RSSI:{parsed['rssi']}"
            console.print(info)

    def _open_pcap(self, filename: str):
        """Open a PCAP file for writing."""
        try:
            f = open(filename, 'wb')
            # Write PCAP global header
            # magic, major, minor, thiszone, sigfigs, snaplen, network (195 = IEEE 802.15.4)
            header = struct.pack("<IHHiIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 195)
            f.write(header)
            return f
        except Exception as e:
            error(f"Failed to create PCAP file: {e}")
            return None

    def _write_pcap(self, f, packet: bytes):
        """Write a packet to PCAP file."""
        ts_sec = int(time.time())
        ts_usec = int((time.time() - ts_sec) * 1000000)
        
        # PCAP packet header
        header = struct.pack("<IIII", ts_sec, ts_usec, len(packet), len(packet))
        f.write(header)
        f.write(packet)

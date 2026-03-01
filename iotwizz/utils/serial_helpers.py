"""
IoTwizz - Serial/UART Helper Utilities
Enhanced serial communication helpers with better error handling and cross-platform support.
"""

import time
import string
import sys
import os
from typing import Tuple, List, Optional


def is_readable(data: bytes, threshold: float = 0.6) -> Tuple[bool, float]:
    """Check if data contains mostly readable ASCII characters.
    
    Args:
        data: Raw bytes to analyze
        threshold: Minimum ratio of printable chars to consider readable
    
    Returns:
        Tuple of (is_readable: bool, ratio: float)
    """
    if not data:
        return False, 0.0
    
    # Count printable characters (alphanumeric, punctuation, space, newline, tab)
    printable_chars = set(
        (string.ascii_letters +
         string.digits +
         string.punctuation +
         ' \n\r\t').encode()
    )
    
    readable_count = sum(1 for byte in data if byte in printable_chars)
    ratio = readable_count / len(data)
    
    return ratio >= threshold, round(ratio, 3)


def get_available_ports() -> List[dict]:
    """List available serial ports on the system.
    
    Returns:
        List of dicts with port info: {device, description, hwid}
    """
    try:
        from serial.tools import list_ports
        ports = []
        for port in list_ports.comports():
            ports.append({
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid or "N/A",
                "vid": f"{port.vid:04X}" if port.vid else None,
                "pid": f"{port.pid:04X}" if port.pid else None,
                "manufacturer": port.manufacturer or "Unknown",
                "product": port.product or "Unknown",
            })
        return ports
    except ImportError:
        return []


def find_port_by_vid_pid(vid: str, pid: str) -> Optional[str]:
    """Find a serial port by Vendor ID and Product ID.
    
    Args:
        vid: Vendor ID (hex string, e.g., "10C4")
        pid: Product ID (hex string, e.g., "EA60")
    
    Returns:
        Device path or None
    """
    ports = get_available_ports()
    vid_upper = vid.upper()
    pid_upper = pid.upper()
    
    for port in ports:
        if port.get("vid") == vid_upper and port.get("pid") == pid_upper:
            return port["device"]
    return None


def auto_detect_port() -> Optional[str]:
    """Try to auto-detect the most likely serial port for IoT devices.
    
    Returns:
        Device path or None
    """
    ports = get_available_ports()
    
    if not ports:
        return None
    
    # Common IoT adapter patterns
    iot_keywords = [
        "usbserial", "USB Serial", "UART", "CH340", "CH341", "CP210",
        "FTDI", "USB-Serial", "TTL", "Arduino", "ESP", "STM32",
        "Silicon Labs", "FT232", "PL2303", "TUSB3410", "MOSCHIP"
    ]
    
    for port in ports:
        desc = port.get("description", "").lower()
        device = port.get("device", "").lower()
        
        for keyword in iot_keywords:
            if keyword.lower() in desc or keyword.lower() in device:
                return port["device"]
    
    # On macOS, prefer /dev/cu.* over /dev/tty.*
    if sys.platform == "darwin":
        for port in ports:
            if port["device"].startswith("/dev/cu."):
                return port["device"]
    
    # On Linux, prefer /dev/ttyUSB* or /dev/ttyACM*
    if sys.platform.startswith("linux"):
        for port in ports:
            if "ttyUSB" in port["device"] or "ttyACM" in port["device"]:
                return port["device"]
    
    # On Windows, prefer lower COM port numbers
    if sys.platform == "win32":
        com_ports = [p for p in ports if "COM" in p["device"]]
        if com_ports:
            com_ports.sort(key=lambda x: int(''.join(filter(str.isdigit, x["device"])) or 999))
            return com_ports[0]["device"]
    
    # Return first port if nothing else matches
    return ports[0]["device"] if ports else None


def open_serial(port: str, baud_rate: int, timeout: float = 2, **kwargs):
    """Open a serial connection with cross-platform support.
    
    Args:
        port: Serial port path (e.g., /dev/ttyUSB0, COM3)
        baud_rate: Baud rate
        timeout: Read timeout in seconds
        **kwargs: Additional serial parameters
    
    Returns:
        serial.Serial instance
    
    Raises:
        serial.SerialException: If port cannot be opened
        PermissionError: If port is locked or permission denied
    """
    import serial
    
    # Default serial settings for IoT
    defaults = {
        "bytesize": serial.EIGHTBITS,
        "parity": serial.PARITY_NONE,
        "stopbits": serial.STOPBITS_ONE,
        "xonxoff": False,
        "rtscts": False,
        "dsrdtr": False,
    }
    defaults.update(kwargs)
    
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud_rate,
            timeout=timeout,
            **defaults
        )
        # Give the port time to settle
        time.sleep(0.1)
        return ser
    except serial.SerialException as e:
        error_msg = str(e).lower()
        
        # Provide helpful error messages
        if "permission denied" in error_msg or "access is denied" in error_msg:
            if sys.platform == "linux":
                hint = "Try: sudo chmod 666 {port} OR add your user to 'dialout' group: sudo usermod -a -G dialout $USER"
            elif sys.platform == "darwin":
                hint = "Check if another application is using the port, or try: sudo chmod 666 {port}"
            elif sys.platform == "win32":
                hint = "Close any other applications using the COM port (Arduino IDE, etc.)"
            else:
                hint = "Check port permissions"
            raise PermissionError(f"Permission denied for {port}. {hint.format(port=port)}") from e
        
        if "could not open port" in error_msg or "port not found" in error_msg:
            raise serial.SerialException(
                f"Could not open {port}. Ensure the device is connected. "
                f"Use 'LIST_PORTS=true' to see available ports."
            ) from e
        
        raise


def read_serial_data(ser, duration: float = 2.0, chunk_size: int = 1024) -> bytes:
    """Read data from serial port for a specified duration.
    
    Args:
        ser: serial.Serial instance
        duration: How long to read (seconds)
        chunk_size: Read buffer size
    
    Returns:
        Bytes read from port
    """
    data = b""
    start = time.time()
    while time.time() - start < duration:
        try:
            if ser.in_waiting > 0:
                chunk = ser.read(min(ser.in_waiting, chunk_size))
                if chunk:
                    data += chunk
            else:
                time.sleep(0.01)
        except Exception:
            break
    return data


def send_serial_data(ser, data: bytes, delay: float = 0.001, flush: bool = True):
    """Send data to serial port with optional per-byte delay.
    
    Args:
        ser: serial.Serial instance
        data: Bytes to send
        delay: Delay between bytes (for slow devices)
        flush: Whether to flush after writing
    """
    if delay > 0:
        for byte in data:
            ser.write(bytes([byte]))
            time.sleep(delay)
    else:
        ser.write(data)
    
    if flush:
        ser.flush()


def send_and_read(ser, data: bytes, read_duration: float = 1.0, delay: float = 0.001) -> bytes:
    """Send data and read response.
    
    Args:
        ser: serial.Serial instance
        data: Bytes to send
        read_duration: How long to read response (seconds)
        delay: Inter-byte delay
    
    Returns:
        Response bytes
    """
    # Clear buffers
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception:
        pass
    
    # Send data
    send_serial_data(ser, data, delay=delay)
    
    # Read response
    return read_serial_data(ser, duration=read_duration)


def analyze_uart_pattern(data: bytes) -> dict:
    """Analyze UART data for patterns that might indicate correct baud rate.
    
    Args:
        data: Raw bytes to analyze
    
    Returns:
        Dict with analysis results
    """
    if not data:
        return {
            "has_pattern": False,
            "pattern_type": None,
            "confidence": 0.0,
            "details": "No data to analyze"
        }
    
    analysis = {
        "has_pattern": False,
        "pattern_type": None,
        "confidence": 0.0,
        "details": "",
        "contains_newline": False,
        "contains_null": False,
        "avg_byte_value": 0,
        "unique_bytes": 0,
    }
    
    analysis["unique_bytes"] = len(set(data))
    analysis["avg_byte_value"] = sum(data) / len(data) if data else 0
    analysis["contains_newline"] = b'\n' in data or b'\r' in data
    analysis["contains_null"] = b'\x00' in data
    
    # Check for common IoT patterns
    text_data = data.decode("utf-8", errors="replace")
    
    # Look for shell prompts
    prompt_patterns = ["#", "$", ">", "login:", "password:", "root@", "~]"]
    for pattern in prompt_patterns:
        if pattern in text_data:
            analysis["has_pattern"] = True
            analysis["pattern_type"] = f"Shell prompt detected: '{pattern}'"
            analysis["confidence"] = 0.95
            return analysis
    
    # Look for U-Boot patterns
    uboot_patterns = ["U-Boot", "Hit any key", "autoboot", "bootcmd", "UBoot"]
    for pattern in uboot_patterns:
        if pattern.lower() in text_data.lower():
            analysis["has_pattern"] = True
            analysis["pattern_type"] = f"U-Boot detected: '{pattern}'"
            analysis["confidence"] = 0.95
            return analysis
    
    # Look for log messages
    log_patterns = ["[    ", "Linux version", "Starting kernel", "init:", "systemd"]
    for pattern in log_patterns:
        if pattern in text_data:
            analysis["has_pattern"] = True
            analysis["pattern_type"] = f"Linux boot log detected"
            analysis["confidence"] = 0.9
            return analysis
    
    # Check for repeating patterns
    if len(data) > 4:
        for pattern_len in [1, 2, 4, 8]:
            if len(data) >= pattern_len * 3:
                pattern = data[:pattern_len]
                repeat_count = data.count(pattern)
                if repeat_count > len(data) / (pattern_len * 2):
                    analysis["has_pattern"] = True
                    analysis["pattern_type"] = f"Repeating pattern (len={pattern_len})"
                    analysis["confidence"] = 0.6
                    return analysis
    
    # General readability check
    readable, ratio = is_readable(data)
    if readable:
        analysis["has_pattern"] = True
        analysis["pattern_type"] = "Mostly printable ASCII"
        analysis["confidence"] = ratio
    
    analysis["details"] = f"Unique bytes: {analysis['unique_bytes']}, Avg: {analysis['avg_byte_value']:.1f}"
    return analysis


def get_platform_port_hints() -> str:
    """Get platform-specific hints for serial ports.
    
    Returns:
        Helpful string for the current platform
    """
    if sys.platform == "darwin":
        return (
            "macOS: Use /dev/cu.* (call-out) or /dev/tty.* (dial-in)\n"
            "  Common: /dev/cu.usbserial-*, /dev/cu.SLAB_USBtoUART, /dev/cu.usbmodem*"
        )
    elif sys.platform.startswith("linux"):
        return (
            "Linux: Use /dev/ttyUSB* (USB-Serial) or /dev/ttyACM* (USB-CDC)\n"
            "  If permission denied: sudo usermod -a -G dialout $USER && logout"
        )
    elif sys.platform == "win32":
        return (
            "Windows: Use COM ports (e.g., COM1, COM3, COM5)\n"
            "  Check Device Manager > Ports (COM & LPT) for available ports"
        )
    else:
        return "Check your OS documentation for serial port naming conventions"

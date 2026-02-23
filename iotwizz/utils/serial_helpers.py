"""
IoTwizz - Serial/UART Helper Utilities
"""

import time
import string


def is_readable(data: bytes, threshold: float = 0.6) -> tuple:
    """Check if data contains mostly readable ASCII characters.

    Args:
        data: Raw bytes to analyze
        threshold: Minimum ratio of printable chars to consider readable

    Returns:
        Tuple of (is_readable: bool, ratio: float)
    """
    if not data:
        return False, 0.0

    printable = set(string.printable.encode())
    printable_count = sum(1 for byte in data if byte in printable)
    ratio = printable_count / len(data)

    return ratio >= threshold, round(ratio, 3)


def get_available_ports() -> list:
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
                "hwid": port.hwid,
            })
        return ports
    except ImportError:
        return []


def open_serial(port: str, baud_rate: int, timeout: float = 2):
    """Open a serial connection.

    Args:
        port: Serial port path (e.g., /dev/ttyUSB0)
        baud_rate: Baud rate
        timeout: Read timeout in seconds

    Returns:
        serial.Serial instance

    Raises:
        serial.SerialException: If port cannot be opened
    """
    import serial
    return serial.Serial(
        port=port,
        baudrate=baud_rate,
        timeout=timeout,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )


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
        chunk = ser.read(chunk_size)
        if chunk:
            data += chunk
        else:
            time.sleep(0.05)
    return data


def send_serial_data(ser, data: bytes, delay: float = 0.01):
    """Send data to serial port with optional per-byte delay.

    Args:
        ser: serial.Serial instance
        data: Bytes to send
        delay: Delay between bytes (for slow devices)
    """
    for byte in data:
        ser.write(bytes([byte]))
        if delay:
            time.sleep(delay)
    ser.flush()

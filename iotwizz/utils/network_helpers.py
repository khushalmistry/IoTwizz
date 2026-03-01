"""
IoTwizz - Network Helper Utilities
"""

import socket
import subprocess


def is_host_alive(host: str, timeout: float = 3) -> bool:
    """Check if a host is reachable via ping.

    Args:
        host: IP address or hostname
        timeout: Timeout in seconds

    Returns:
        True if host responds to ping
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(int(timeout)), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_port_open(host: str, port: int, timeout: float = 3) -> bool:
    """Check if a TCP port is open on a host.

    Args:
        host: IP address or hostname
        port: TCP port number
        timeout: Connection timeout in seconds

    Returns:
        True if port is open
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.error, OSError):
        return False


def resolve_hostname(hostname: str) -> str:
    """Resolve a hostname to an IP address.

    Args:
        hostname: Hostname to resolve

    Returns:
        IP address string, or the original hostname if resolution fails
    """
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return hostname


def get_service_banner(host: str, port: int, timeout: float = 5) -> str:
    """Grab the service banner from a port.

    Args:
        host: IP address or hostname
        port: TCP port number
        timeout: Connection timeout

    Returns:
        Banner string, or empty string if no banner
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        # Send a newline to trigger banner
        sock.send(b"\r\n")
        banner = sock.recv(1024).decode("utf-8", errors="replace").strip()
        sock.close()
        return banner
    except (socket.error, OSError):
        return ""


def scan_common_ports(host: str, timeout: float = 2) -> list:
    """Scan common IoT ports on a host.

    Args:
        host: IP address or hostname
        timeout: Per-port timeout

    Returns:
        List of open port dicts: {port, service}
    """
    common_ports = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        443: "HTTPS",
        554: "RTSP",
        1883: "MQTT",
        1900: "UPnP",
        3000: "Node.js",
        5683: "CoAP",
        8080: "HTTP-Alt",
        8443: "HTTPS-Alt",
        8883: "MQTT-TLS",
        9100: "Printer",
        49152: "UPnP",
    }

    open_ports = []
    for port, service in common_ports.items():
        if is_port_open(host, port, timeout):
            open_ports.append({"port": port, "service": service})

    return open_ports

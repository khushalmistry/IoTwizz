"""
IoTwizz Module: CoAP Fuzzer
Comprehensive CoAP protocol fuzzer for IoT device testing.
Tests for parsing vulnerabilities, DoS conditions, and protocol violations.
"""

import socket
import struct
import random
import time
from typing import List, Tuple, Optional
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator


class CoapFuzzer(BaseModule):
    """Fuzz CoAP endpoints for security vulnerabilities."""

    # CoAP message types
    TYPES = {
        "CON": 0,  # Confirmable
        "NON": 1,  # Non-confirmable
        "ACK": 2,  # Acknowledgement
        "RST": 3,  # Reset
    }

    # CoAP method codes
    METHODS = {
        "GET": 1,
        "POST": 2,
        "PUT": 3,
        "DELETE": 4,
    }

    # CoAP response codes
    RESPONSE_CODES = {
        "Created": (2, 1),
        "Deleted": (2, 2),
        "Valid": (2, 3),
        "Changed": (2, 4),
        "Content": (2, 5),
        "BadRequest": (4, 0),
        "Unauthorized": (4, 1),
        "BadOption": (4, 2),
        "Forbidden": (4, 3),
        "NotFound": (4, 4),
        "MethodNotAllowed": (4, 5),
        "NotAcceptable": (4, 6),
        "RequestEntityIncomplete": (4, 8),
        "PreconditionFailed": (4, 12),
        "RequestEntityTooLarge": (4, 13),
        "UnsupportedContentFormat": (4, 15),
        "InternalServerError": (5, 0),
        "NotImplemented": (5, 1),
        "BadGateway": (5, 2),
        "ServiceUnavailable": (5, 3),
        "GatewayTimeout": (5, 4),
        "ProxyingNotSupported": (5, 5),
    }

    # CoAP options
    OPTIONS = {
        "If-Match": 1,
        "Uri-Host": 3,
        "ETag": 4,
        "If-None-Match": 5,
        "Uri-Port": 7,
        "Location-Path": 8,
        "Uri-Path": 11,
        "Content-Format": 12,
        "Max-Age": 14,
        "Uri-Query": 15,
        "Accept": 17,
        "Location-Query": 20,
        "Size2": 28,
        "Proxy-Uri": 35,
        "Proxy-Scheme": 39,
        "Size1": 60,
    }

    # Content formats
    CONTENT_FORMATS = {
        "text/plain": 0,
        "application/link-format": 40,
        "application/xml": 41,
        "application/octet-stream": 42,
        "application/exi": 47,
        "application/json": 50,
        "application/cbor": 60,
    }

    def __init__(self):
        super().__init__()
        self.name = "CoAP Protocol Fuzzer"
        self.description = "Comprehensive CoAP endpoint fuzzer for security testing"
        self.author = "IoTwizz Team"
        self.category = "protocol"

        self.options = {
            "TARGET": {
                "value": "",
                "required": True,
                "description": "Target IP address or hostname",
            },
            "PORT": {
                "value": "5683",
                "required": False,
                "description": "CoAP port (default: 5683, CoAPS: 5684)",
            },
            "MODE": {
                "value": "fuzz",
                "required": False,
                "description": "Mode: fuzz, discover, stress, all",
            },
            "PATH": {
                "value": "/",
                "required": False,
                "description": "CoAP resource path (e.g., /api/v1/device)",
            },
            "COUNT": {
                "value": "100",
                "required": False,
                "description": "Number of packets to send",
            },
            "INTERVAL": {
                "value": "0.01",
                "required": False,
                "description": "Interval between packets in seconds",
            },
            "METHOD": {
                "value": "random",
                "required": False,
                "description": "CoAP method: GET, POST, PUT, DELETE, random",
            },
            "PAYLOAD_TYPE": {
                "value": "mixed",
                "required": False,
                "description": "Payload type: random, format, json, overflow, mixed",
            },
            "FUZZ_OPTIONS": {
                "value": "true",
                "required": False,
                "description": "Fuzz CoAP options (default: true)",
            },
            "FUZZ_HEADER": {
                "value": "true",
                "required": False,
                "description": "Fuzz CoAP header fields (default: true)",
            },
            "TIMEOUT": {
                "value": "2",
                "required": False,
                "description": "Response timeout in seconds",
            },
            "VERBOSE": {
                "value": "false",
                "required": False,
                "description": "Show each packet sent",
            },
        }
        
        self._stats = {
            "sent": 0,
            "received": 0,
            "errors": 0,
            "timeouts": 0,
            "malformed_responses": 0,
        }

    def run(self):
        """Run the CoAP fuzzer."""
        target = self.get_option("TARGET")
        port = self.get_option_int("PORT", default=5683)
        mode = self.get_option("MODE").lower()
        path = self.get_option("PATH") or "/"
        count = self.get_option_int("COUNT", default=100)
        interval = self.get_option_float("INTERVAL", default=0.01)
        method = self.get_option("METHOD").upper()
        payload_type = self.get_option("PAYLOAD_TYPE").lower()
        fuzz_options = (self.get_option("FUZZ_OPTIONS") or "true").lower() == "true"
        fuzz_header = (self.get_option("FUZZ_HEADER") or "true").lower() == "true"
        timeout = self.get_option_float("TIMEOUT", default=2.0)
        verbose = (self.get_option("VERBOSE") or "false").lower() == "true"

        # Validate port
        if not (1 <= port <= 65535):
            error(f"Invalid port: {port}")
            return

        info(f"Target: [cyan]{target}:{port}[/cyan]")
        info(f"Mode: [cyan]{mode}[/cyan] | Count: {count} | Interval: {interval}s")
        info(f"Path: [cyan]{path}[/cyan] | Method: {method}")
        console.print()

        # Resolve hostname
        try:
            target_ip = socket.gethostbyname(target)
            if target_ip != target:
                info(f"Resolved: [cyan]{target}[/cyan] -> [cyan]{target_ip}[/cyan]")
        except socket.gaierror:
            error(f"Could not resolve hostname: {target}")
            return

        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        # Reset stats
        self._stats = {
            "sent": 0,
            "received": 0,
            "errors": 0,
            "timeouts": 0,
            "malformed_responses": 0,
        }

        # Run based on mode
        if mode == "discover":
            self._discover_resources(sock, target_ip, port, timeout, verbose)
        elif mode == "stress":
            self._stress_test(sock, target_ip, port, count, interval, verbose)
        elif mode == "fuzz":
            self._fuzz_packets(sock, target_ip, port, count, interval, path, method,
                              payload_type, fuzz_options, fuzz_header, verbose)
        elif mode == "all":
            self._discover_resources(sock, target_ip, port, timeout, verbose)
            self._fuzz_packets(sock, target_ip, port, count, interval, path, method,
                              payload_type, fuzz_options, fuzz_header, verbose)
            self._stress_test(sock, target_ip, port, count, interval, verbose)

        # Show summary
        console.print()
        print_separator()
        self._show_summary()

        sock.close()

    def _discover_resources(self, sock: socket.socket, target: str, port: int,
                           timeout: float, verbose: bool):
        """Discover CoAP resources using .well-known/core."""
        info("[bold]Phase: Resource Discovery[/bold]")
        console.print()
        
        # Create a proper CoAP GET request for .well-known/core
        msg_id = random.randint(0, 65535)
        token = bytes([random.randint(0, 255) for _ in range(4)])
        
        # Build CoAP packet
        packet = self._build_coap_packet(
            msg_type=self.TYPES["CON"],
            msg_code=self.METHODS["GET"],
            msg_id=msg_id,
            token=token,
            options=[(self.OPTIONS["Uri-Path"], ".well-known"), 
                     (self.OPTIONS["Uri-Path"], "core")],
            payload=b""
        )
        
        try:
            sock.sendto(packet, (target, port))
            self._stats["sent"] += 1
            
            if verbose:
                info(f"  Sent discovery request to /.well-known/core")
            
            response, addr = sock.recvfrom(4096)
            self._stats["received"] += 1
            
            # Parse response
            resp_info = self._parse_coap_response(response)
            
            if resp_info["code_class"] == 2:
                success(f"  Discovery successful: {resp_info['code_detail']}")
                
                # Parse link format
                if resp_info["payload"]:
                    resources = self._parse_link_format(resp_info["payload"])
                    
                    if resources:
                        columns = [
                            ("Path", "cyan"),
                            ("Attributes", "white"),
                        ]
                        print_table("Discovered Resources", columns, resources)
                    else:
                        info(f"  Payload: {resp_info['payload'][:200]}")
            else:
                warning(f"  Discovery response: {resp_info['code_class']}.{resp_info['code_detail']}")
                
        except socket.timeout:
            self._stats["timeouts"] += 1
            warning("  No response to discovery request")
        except Exception as e:
            self._stats["errors"] += 1
            error(f"  Discovery error: {e}")
        
        console.print()

    def _fuzz_packets(self, sock: socket.socket, target: str, port: int, count: int,
                     interval: float, path: str, method: str, payload_type: str,
                     fuzz_options: bool, fuzz_header: bool, verbose: bool):
        """Send fuzzed CoAP packets."""
        info("[bold]Phase: Packet Fuzzing[/bold]")
        console.print()
        
        for i in range(count):
            try:
                # Generate fuzzed packet
                packet = self._generate_fuzz_packet(path, method, payload_type,
                                                    fuzz_options, fuzz_header)
                
                # Send packet
                sock.sendto(packet, (target, port))
                self._stats["sent"] += 1
                
                if verbose:
                    info(f"  [{i+1}/{count}] Sent {len(packet)} bytes")
                elif (i + 1) % 20 == 0 or i == 0:
                    console.print(f"[{i+1}/{count}] Fuzzing... (Ctrl+C to stop)", end="\r")
                
                # Try to receive response
                try:
                    response, addr = sock.recvfrom(4096)
                    self._stats["received"] += 1
                    
                    # Parse and check response
                    resp_info = self._parse_coap_response(response)
                    
                    if verbose:
                        result(f"  Response: {resp_info['code_class']}.{resp_info['code_detail']}")
                    
                except socket.timeout:
                    self._stats["timeouts"] += 1
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                console.print()
                warning("Fuzzing interrupted by user")
                break
            except Exception as e:
                self._stats["errors"] += 1
                if verbose:
                    error(f"  Error: {e}")
        
        console.print()

    def _stress_test(self, sock: socket.socket, target: str, port: int,
                    count: int, interval: float, verbose: bool):
        """Stress test with rapid packet sending."""
        info("[bold]Phase: Stress Testing[/bold]")
        info("Sending rapid packets to test DoS resilience...")
        console.print()
        
        for i in range(count):
            try:
                # Create simple valid packet
                msg_id = random.randint(0, 65535)
                token = bytes([random.randint(0, 255) for _ in range(2)])
                
                packet = self._build_coap_packet(
                    msg_type=self.TYPES["NON"],
                    msg_code=self.METHODS["GET"],
                    msg_id=msg_id,
                    token=token,
                    options=[(self.OPTIONS["Uri-Path"], "test")],
                    payload=b""
                )
                
                sock.sendto(packet, (target, port))
                self._stats["sent"] += 1
                
                if (i + 1) % 50 == 0:
                    console.print(f"[{i+1}/{count}] Stress testing...", end="\r")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                console.print()
                warning("Stress test interrupted")
                break
            except Exception as e:
                self._stats["errors"] += 1
        
        console.print()

    def _build_coap_packet(self, msg_type: int, msg_code: int, msg_id: int,
                          token: bytes, options: List[Tuple[int, bytes]],
                          payload: bytes) -> bytes:
        """Build a valid CoAP packet."""
        # Header: Ver=1, Type, TKL, Code, Message ID
        version = 1
        tkl = len(token)
        
        header = struct.pack(
            "!BBH",
            (version << 6) | (msg_type << 4) | tkl,
            msg_code,
            msg_id
        )
        
        # Token
        token_bytes = token[:8]  # Max 8 bytes
        
        # Options (simplified - no option delta/length encoding optimization)
        options_bytes = b""
        prev_option = 0
        
        for option_num, option_value in sorted(options):
            if isinstance(option_value, str):
                option_value = option_value.encode('utf-8')
            
            delta = option_num - prev_option
            length = len(option_value)
            
            # Encode delta and length
            first_byte = 0
            extended_delta = b""
            extended_length = b""
            
            if delta < 13:
                first_byte = (delta << 4) | (length if length < 13 else 13)
            elif delta < 269:
                first_byte = (13 << 4) | (length if length < 13 else 13)
                extended_delta = struct.pack("!B", delta - 13)
            else:
                first_byte = (14 << 4) | (length if length < 13 else 13)
                extended_delta = struct.pack("!H", delta - 269)
            
            if length >= 13 and length < 269:
                extended_length = struct.pack("!B", length - 13)
            elif length >= 269:
                extended_length = struct.pack("!H", length - 269)
            
            options_bytes += bytes([first_byte]) + extended_delta + extended_length + option_value
            prev_option = option_num
        
        # Payload marker and payload
        if payload:
            payload_bytes = b"\xff" + payload
        else:
            payload_bytes = b""
        
        return header + token_bytes + options_bytes + payload_bytes

    def _generate_fuzz_packet(self, path: str, method: str, payload_type: str,
                              fuzz_options: bool, fuzz_header: bool) -> bytes:
        """Generate a fuzzed CoAP packet."""
        
        # Determine fuzzing approach
        fuzz_type = random.choice(["valid", "header", "options", "payload", "malformed"])
        
        if fuzz_type == "valid" or (not fuzz_header and not fuzz_options):
            # Build mostly valid packet
            msg_type = random.choice(list(self.TYPES.values()))
            
            if method == "RANDOM":
                msg_code = random.choice(list(self.METHODS.values()))
            else:
                msg_code = self.METHODS.get(method, self.METHODS["GET"])
            
            msg_id = random.randint(0, 65535)
            token = bytes([random.randint(0, 255) for _ in range(random.randint(0, 8))])
            
            # Build options
            options = []
            path_parts = path.strip("/").split("/")
            for part in path_parts:
                if part:
                    options.append((self.OPTIONS["Uri-Path"], part))
            
            payload = self._generate_payload(payload_type)
            
            return self._build_coap_packet(msg_type, msg_code, msg_id, token, options, payload)
        
        elif fuzz_type == "header":
            return self._fuzz_header()
        elif fuzz_type == "options":
            return self._fuzz_options(path)
        elif fuzz_type == "payload":
            return self._fuzz_payload(path, payload_type)
        else:
            return self._fuzz_malformed()

    def _fuzz_header(self) -> bytes:
        """Fuzz CoAP header fields."""
        # Invalid version
        if random.random() < 0.3:
            version = random.choice([0, 2, 3])
        else:
            version = 1
        
        # Invalid type
        msg_type = random.randint(0, 15)
        
        # Invalid token length
        tkl = random.choice([random.randint(9, 255), random.randint(0, 15)])
        
        # Random code
        msg_code = random.randint(0, 255)
        
        # Random message ID
        msg_id = random.randint(0, 65535)
        
        header = struct.pack("!BBH", (version << 6) | (msg_type << 4) | (tkl & 0x0F), msg_code, msg_id)
        
        # Random token (may not match TKL)
        token = bytes([random.randint(0, 255) for _ in range(random.randint(0, 20))])
        
        return header + token + bytes([random.randint(0, 255) for _ in range(random.randint(0, 100))])

    def _fuzz_options(self, path: str) -> bytes:
        """Fuzz CoAP options."""
        msg_id = random.randint(0, 65535)
        token = bytes([random.randint(0, 255) for _ in range(4)])
        
        # Build options with fuzzed values
        options = []
        
        # Add valid path
        path_parts = path.strip("/").split("/")
        for part in path_parts:
            if part:
                options.append((self.OPTIONS["Uri-Path"], part))
        
        # Add fuzzed options
        fuzzed_options = [
            (self.OPTIONS["Uri-Host"], b"A" * random.randint(1, 255)),
            (self.OPTIONS["Uri-Port"], struct.pack("!H", random.randint(0, 65535))),
            (self.OPTIONS["Uri-Query"], b"=" * random.randint(1, 100)),
            (self.OPTIONS["Content-Format"], struct.pack("!H", random.randint(0, 65535))),
            (self.OPTIONS["Accept"], struct.pack("!H", random.randint(0, 65535))),
            (self.OPTIONS["Max-Age"], struct.pack("!I", random.randint(0, 2**32 - 1))),
            (random.randint(100, 65535), b"fuzz"),  # Unknown option
        ]
        
        options.extend(random.sample(fuzzed_options, k=random.randint(0, len(fuzzed_options))))
        
        return self._build_coap_packet(
            self.TYPES["CON"], self.METHODS["POST"], msg_id, token, options,
            self._generate_payload("random")
        )

    def _fuzz_payload(self, path: str, payload_type: str) -> bytes:
        """Fuzz with various payload types."""
        msg_id = random.randint(0, 65535)
        token = bytes([random.randint(0, 255) for _ in range(4)])
        
        options = []
        path_parts = path.strip("/").split("/")
        for part in path_parts:
            if part:
                options.append((self.OPTIONS["Uri-Path"], part))
        
        payload = self._generate_payload(payload_type)
        
        return self._build_coap_packet(
            self.TYPES["CON"], self.METHODS["POST"], msg_id, token, options, payload
        )

    def _fuzz_malformed(self) -> bytes:
        """Generate completely malformed packets."""
        patterns = [
            b"\x00" * random.randint(1, 100),
            b"\xff" * random.randint(1, 100),
            bytes([random.randint(0, 255) for _ in range(random.randint(1, 200))]),
            b"\x40\x00\x00\x00",  # Minimal but invalid
            b"\x40\x01\x00\x00\xff",  # Payload marker but no payload
            b"\x44\x01\x00\x00\xff\xff\xff\xff" + b"A" * 1000,
        ]
        return random.choice(patterns)

    def _generate_payload(self, payload_type: str) -> bytes:
        """Generate fuzzing payload."""
        if payload_type == "random":
            return bytes([random.randint(0, 255) for _ in range(random.randint(0, 500))])
        elif payload_type == "format":
            return b"%s%n%p%x%d" * 10
        elif payload_type == "json":
            return b'{"test":"' + b"A" * random.randint(0, 500) + b'"}'
        elif payload_type == "overflow":
            return b"A" * random.randint(1000, 10000)
        else:  # mixed
            return random.choice([
                lambda: bytes([random.randint(0, 255) for _ in range(random.randint(10, 200))]),
                lambda: b"%s%n%p" * 20,
                lambda: b'{"fuzz":true}' * 10,
                lambda: b"A" * random.randint(100, 1000),
            ])()

    def _parse_coap_response(self, data: bytes) -> dict:
        """Parse a CoAP response."""
        info = {
            "version": 0,
            "type": 0,
            "tkl": 0,
            "code_class": 0,
            "code_detail": 0,
            "msg_id": 0,
            "token": b"",
            "options": [],
            "payload": b"",
        }
        
        try:
            if len(data) < 4:
                return info
            
            # Parse header
            first_byte = data[0]
            info["version"] = (first_byte >> 6) & 0x03
            info["type"] = (first_byte >> 4) & 0x03
            info["tkl"] = first_byte & 0x0F
            
            info["code_class"] = (data[1] >> 5) & 0x07
            info["code_detail"] = data[1] & 0x1F
            info["msg_id"] = struct.unpack("!H", data[2:4])[0]
            
            # Parse token
            if len(data) >= 4 + info["tkl"]:
                info["token"] = data[4:4 + info["tkl"]]
            
            # Find payload marker
            payload_start = data.find(b"\xff", 4 + info["tkl"])
            if payload_start != -1:
                info["payload"] = data[payload_start + 1:]
            
        except Exception:
            self._stats["malformed_responses"] += 1
        
        return info

    def _parse_link_format(self, payload: bytes) -> List[Tuple[str, str]]:
        """Parse CoRE Link Format response."""
        resources = []
        
        try:
            links = payload.decode('utf-8', errors='replace').split(',')
            
            for link in links:
                link = link.strip()
                if link.startswith('<') and '>' in link:
                    path_end = link.index('>')
                    path = link[1:path_end]
                    attrs = link[path_end + 1:].strip()
                    resources.append((path, attrs))
        except Exception:
            pass
        
        return resources

    def _show_summary(self):
        """Show fuzzing summary."""
        columns = [
            ("Metric", "cyan"),
            ("Count", "white"),
        ]
        rows = [
            ("Packets Sent", str(self._stats["sent"])),
            ("Responses Received", str(self._stats["received"])),
            ("Timeouts", str(self._stats["timeouts"])),
            ("Errors", str(self._stats["errors"])),
            ("Malformed Responses", str(self._stats["malformed_responses"])),
        ]
        print_table("Fuzzing Summary", columns, rows)
        
        if self._stats["received"] > 0:
            info("Target appears responsive to CoAP traffic")
        elif self._stats["sent"] > 0:
            warning("No responses received — target may be filtering or not running CoAP")

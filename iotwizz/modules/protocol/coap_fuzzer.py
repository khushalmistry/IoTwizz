"""
IoTwizz Module: CoAP Fuzzer
Send malformed CoAP packets to test IoT servers.
"""
import random
import socket
import struct
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, console

class CoapFuzzer(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "CoAP Protocol Fuzzer"
        self.description = "Test CoAP endpoints for parsing vulnerabilities and DoS"
        self.author = "IoTwizz Team"
        self.category = "protocol"
        
        self.options = {
            "TARGET": {
                "value": "",
                "required": True,
                "description": "Target IP/Hostname",
            },
            "PORT": {
                "value": "5683",
                "required": True,
                "description": "CoAP Port",
            },
            "COUNT": {
                "value": "100",
                "required": True,
                "description": "Number of mutated packets to send",
            }
        }
        
    def _create_malformed_coap(self) -> bytes:
        # CoAP header is 4 bytes minimum
        # [Ver|Type|TKL] [Code] [Message ID (2 bytes)]
        version = random.choice([0, 1, 2, 3]) # Valid is 1
        mtype = random.randint(0, 3) 
        tkl = random.randint(0, 15)
        
        byte1 = (version << 6) | (mtype << 4) | tkl
        code = random.randint(0, 255)
        msg_id = random.randint(0, 65535)
        
        header = struct.pack("!BBH", byte1, code, msg_id)
        
        # Token
        token = bytes([random.randint(0, 255) for _ in range(tkl)])
        
        # Options and payload
        payload_marker = b"\xff"
        payload = ("A" * random.randint(0, 500)).encode()
        
        return header + token + payload_marker + payload

    def run(self):
        target = self.get_option("TARGET")
        port = int(self.get_option("PORT"))
        count = int(self.get_option("COUNT"))
        
        info(f"Fuzzing CoAP endpoint {target}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        
        success_count = 0
        try:
            for i in range(count):
                packet = self._create_malformed_coap()
                sock.sendto(packet, (target, port))
                console.print(f"[{i+1}/{count}] Sent malformed CoAP packet ({len(packet)} bytes)", end="\r")
                success_count += 1
                time.sleep(0.01)
                
            console.print()
            success(f"Successfully sent {success_count} mutated CoAP packets!")
            info("Check the target system logs/uptime to see if it crashed.")
        except socket.gaierror:
            error("Could not resolve target hostname.")
        except KeyboardInterrupt:
            console.print()
            warning("Fuzzing aborted by user.")
        finally:
            sock.close()

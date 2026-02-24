"""
IoTwizz Module: MQTT Fuzzer
Rapidly publish malformed data to MQTT topics.
"""
import time
import random
import string
try:
    import paho.mqtt.client as mqtt
except ImportError:
    pass
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, console

class MqttFuzzer(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "MQTT Protocol Fuzzer"
        self.description = "Fuzz MQTT brokers and subscribers with malformed payloads"
        self.author = "IoTwizz Team"
        self.category = "protocol"
        
        self.options = {
            "HOST": {
                "value": "",
                "required": True,
                "description": "MQTT Broker Host IP/Hostname",
            },
            "PORT": {
                "value": "1883",
                "required": True,
                "description": "MQTT Broker Port",
            },
            "TOPIC": {
                "value": "#",
                "required": True,
                "description": "Topic to fuzz (e.g., cmd/device/1, #)",
            },
            "COUNT": {
                "value": "100",
                "required": True,
                "description": "Number of fuzzing payloads to send",
            }
        }
        
    def _generate_payload(self) -> bytes:
        payload_type = random.choice(["large_string", "format_string", "binary", "empty", "json_malformed"])
        
        if payload_type == "large_string":
            return ("A" * random.randint(1000, 10000)).encode()
        elif payload_type == "format_string":
            return b"%s%n%p%x%d%s" * 10
        elif payload_type == "binary":
            return bytes([random.randint(0, 255) for _ in range(random.randint(10, 500))])
        elif payload_type == "empty":
            return b""
        elif payload_type == "json_malformed":
            return b'{"cmd": "on", "value": {"test": ' + ("A" * 100).encode() + b'}, '
            
        return b"FUZZ"

    def run(self):
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            error("paho-mqtt is not installed. Run: pip install paho-mqtt")
            return
            
        host = self.get_option("HOST")
        port = int(self.get_option("PORT"))
        topic = self.get_option("TOPIC")
        count = int(self.get_option("COUNT"))
        
        info(f"Connecting to MQTT Broker at {host}:{port}...")
        
        client = mqtt.Client(client_id=f"iotwizz_fuzzer_{random.randint(1000,9999)}")
        
        try:
            client.connect(host, port, 10)
        except Exception as e:
            error(f"Failed to connect to broker: {e}")
            return
            
        client.loop_start()
        success("Connected! Starting fuzzing...")
        
        try:
            for i in range(count):
                payload = self._generate_payload()
                # Determine QOS, randomly 0, 1, or 2
                qos = random.choice([0, 1, 2])
                
                # Fuzz topic itself sometimes if the user put #
                fuzz_topic = topic
                if topic == "#" or random.random() < 0.2:
                    fuzz_topic = topic.replace("#", f"fuzz/{random.choice(string.ascii_letters)}") + "".join(random.choices(string.ascii_letters, k=5))
                
                console.print(f"[{i+1}/{count}] Publishing [cyan]{len(payload)} bytes[/cyan] to [yellow]{fuzz_topic}[/yellow] (QoS {qos})", end="\r")
                client.publish(fuzz_topic, payload, qos=qos)
                time.sleep(0.05)
                
            console.print()
            success("Fuzzing complete!")
        except KeyboardInterrupt:
            console.print()
            warning("Fuzzing aborted by user.")
        finally:
            client.disconnect()
            client.loop_stop()

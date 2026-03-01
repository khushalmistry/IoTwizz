"""
IoTwizz Module: MQTT Fuzzer
Comprehensive MQTT protocol fuzzer for IoT device testing.
Tests for vulnerabilities, authentication bypass, and DoS conditions.
"""

import time
import random
import string
import socket
import threading
from typing import Optional, List, Dict
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator


class MqttFuzzer(BaseModule):
    """Fuzz MQTT brokers and clients for vulnerabilities."""

    def __init__(self):
        super().__init__()
        self.name = "MQTT Protocol Fuzzer"
        self.description = "Comprehensive MQTT broker/client fuzzer for security testing"
        self.author = "IoTwizz Team"
        self.category = "protocol"

        self.options = {
            "HOST": {
                "value": "",
                "required": True,
                "description": "MQTT broker hostname or IP",
            },
            "PORT": {
                "value": "1883",
                "required": False,
                "description": "MQTT broker port (default: 1883, TLS: 8883)",
            },
            "MODE": {
                "value": "publish",
                "required": True,
                "description": "Fuzz mode: publish, subscribe, connect, all",
            },
            "CLIENT_ID": {
                "value": "",
                "required": False,
                "description": "Client ID prefix (random if empty)",
            },
            "USERNAME": {
                "value": "",
                "required": False,
                "description": "MQTT username (if required)",
            },
            "PASSWORD": {
                "value": "",
                "required": False,
                "description": "MQTT password (if required)",
            },
            "TOPIC": {
                "value": "#",
                "required": False,
                "description": "Topic to fuzz (default: # for all)",
            },
            "COUNT": {
                "value": "100",
                "required": False,
                "description": "Number of fuzzing iterations",
            },
            "INTERVAL": {
                "value": "0.05",
                "required": False,
                "description": "Interval between messages in seconds",
            },
            "PAYLOAD_TYPE": {
                "value": "mixed",
                "required": False,
                "description": "Payload type: random, format, overflow, json, mixed",
            },
            "QOS": {
                "value": "random",
                "required": False,
                "description": "QoS level: 0, 1, 2, random",
            },
            "TOPIC_FUZZ": {
                "value": "true",
                "required": False,
                "description": "Fuzz topic names as well as payloads",
            },
            "ANONYMOUS_LOGIN": {
                "value": "true",
                "required": False,
                "description": "Try anonymous login before fuzzing",
            },
            "TEST_ACL": {
                "value": "false",
                "required": False,
                "description": "Test for ACL bypass (read/write protected topics)",
            },
            "VERBOSE": {
                "value": "false",
                "required": False,
                "description": "Show each message sent",
            },
        }
        
        self._stop_flag = threading.Event()
        self._stats = {
            "connects": 0,
            "publishes": 0,
            "subscribes": 0,
            "errors": 0,
            "disconnects": 0,
        }

    def run(self):
        """Run the MQTT fuzzer."""
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            error("paho-mqtt is not installed. Run: pip install paho-mqtt")
            return

        host = self.get_option("HOST")
        port = self.get_option_int("PORT", default=1883)
        mode = self.get_option("MODE").lower()
        client_id_prefix = self.get_option("CLIENT_ID")
        username = self.get_option("USERNAME")
        password = self.get_option("PASSWORD")
        topic = self.get_option("TOPIC") or "#"
        count = self.get_option_int("COUNT", default=100)
        interval = self.get_option_float("INTERVAL", default=0.05)
        payload_type = self.get_option("PAYLOAD_TYPE").lower()
        qos_setting = self.get_option("QOS").lower()
        topic_fuzz = (self.get_option("TOPIC_FUZZ") or "true").lower() == "true"
        anonymous_login = (self.get_option("ANONYMOUS_LOGIN") or "true").lower() == "true"
        test_acl = (self.get_option("TEST_ACL") or "false").lower() == "true"
        verbose = (self.get_option("VERBOSE") or "false").lower() == "true"

        info(f"Target: [cyan]{host}:{port}[/cyan]")
        info(f"Mode: [cyan]{mode}[/cyan] | Count: {count} | Interval: {interval}s")
        info(f"Payload type: [cyan]{payload_type}[/cyan] | Topic fuzz: {topic_fuzz}")
        console.print()

        # Test connection first
        info("Testing connection...")
        
        client = mqtt.Client(
            client_id=self._generate_client_id(client_id_prefix),
            protocol=mqtt.MQTTv311
        )
        
        # Set credentials if provided
        if username:
            client.username_pw_set(username, password or "")
        
        # Connection result tracking
        conn_result = {"code": None, "message": ""}
        
        def on_connect(c, userdata, flags, rc, properties=None):
            conn_result["code"] = rc
            conn_result["message"] = mqtt.connack_string(rc) if hasattr(mqtt, 'connack_string') else str(rc)
        
        client.on_connect = on_connect
        
        try:
            client.connect(host, port, keepalive=60)
            client.loop_start()
            time.sleep(2)
            client.loop_stop()
        except mqtt.MQTTException as e:
            conn_result["code"] = -1
            conn_result["message"] = str(e)
        except socket.timeout:
            conn_result["code"] = -1
            conn_result["message"] = "Connection timeout"
        except socket.error as e:
            conn_result["code"] = -1
            conn_result["message"] = str(e)
        except Exception as e:
            conn_result["code"] = -1
            conn_result["message"] = str(e)

        if conn_result["code"] == 0:
            success(f"Connected successfully: {conn_result['message']}")
        elif conn_result["code"] == 5:
            warning("Connection refused: Not authorized")
            if not username and anonymous_login:
                warning("Anonymous login rejected. Try providing USERNAME and PASSWORD.")
        elif conn_result["code"] in [1, 2, 3, 4]:
            error(f"Connection refused: {conn_result['message']}")
            return
        else:
            error(f"Failed to connect: {conn_result['message']}")
            return

        console.print()
        
        # Reset stats
        self._stats = {
            "connects": 0,
            "publishes": 0,
            "subscribes": 0,
            "errors": 0,
            "disconnects": 0,
        }

        # Run fuzzing based on mode
        if mode == "publish" or mode == "all":
            self._fuzz_publish(host, port, username, password, client_id_prefix,
                              topic, count, interval, payload_type, qos_setting,
                              topic_fuzz, verbose)
        
        if mode == "subscribe" or mode == "all":
            self._fuzz_subscribe(host, port, username, password, client_id_prefix,
                                count, verbose)
        
        if mode == "connect" or mode == "all":
            self._fuzz_connect(host, port, count, verbose)
        
        # Test ACL bypass
        if test_acl:
            self._test_acl_bypass(host, port, username, password, client_id_prefix)

        # Summary
        console.print()
        print_separator()
        self._show_summary()

    def _fuzz_publish(self, host: str, port: int, username: str, password: str,
                      client_id_prefix: str, topic: str, count: int, interval: float,
                      payload_type: str, qos_setting: str, topic_fuzz: bool, verbose: bool):
        """Fuzz by publishing malformed messages."""
        info("[bold]Phase: Publish Fuzzing[/bold]")
        console.print()
        
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            return
        
        client = mqtt.Client(
            client_id=self._generate_client_id(client_id_prefix),
            protocol=mqtt.MQTTv311
        )
        
        if username:
            client.username_pw_set(username, password or "")
        
        try:
            client.connect(host, port, keepalive=60)
            client.loop_start()
            time.sleep(0.5)
        except Exception as e:
            error(f"Failed to connect for publish fuzzing: {e}")
            return
        
        try:
            for i in range(count):
                if self._stop_flag.is_set():
                    break
                
                # Generate topic
                fuzz_topic = topic
                if topic_fuzz and (topic == "#" or random.random() < 0.3):
                    fuzz_topic = self._generate_fuzz_topic(topic)
                
                # Generate payload
                payload = self._generate_payload(payload_type)
                
                # Determine QoS
                if qos_setting == "random":
                    qos = random.choice([0, 1, 2])
                else:
                    try:
                        qos = int(qos_setting)
                    except ValueError:
                        qos = 0
                
                if verbose:
                    info(f"[{i+1}/{count}] Topic: {fuzz_topic[:30]} | Payload: {len(payload)} bytes | QoS: {qos}")
                else:
                    if (i + 1) % 10 == 0 or i == 0:
                        console.print(f"[{i+1}/{count}] Publishing... (Ctrl+C to stop)", end="\r")
                
                try:
                    result = client.publish(fuzz_topic, payload, qos=qos)
                    self._stats["publishes"] += 1
                    
                    if result.rc != mqtt.MQTT_ERR_SUCCESS:
                        self._stats["errors"] += 1
                        
                except Exception as e:
                    self._stats["errors"] += 1
                    if verbose:
                        error(f"  Publish error: {e}")
                
                time.sleep(interval)
            
            console.print()
            
        except KeyboardInterrupt:
            console.print()
            warning("Fuzzing interrupted by user")
        finally:
            client.loop_stop()
            client.disconnect()
        
        success(f"Published {self._stats['publishes']} messages")

    def _fuzz_subscribe(self, host: str, port: int, username: str, password: str,
                        client_id_prefix: str, count: int, verbose: bool):
        """Fuzz by subscribing to unusual topics."""
        info("[bold]Phase: Subscribe Fuzzing[/bold]")
        console.print()
        
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            return
        
        # Topics to test
        fuzz_topics = [
            "#", "$SYS/#", "$CONTROL/#", "$share/#",
            "/#", "//", "/./", "/../", "/\x00/",
            "admin/#", "system/#", "debug/#",
            "device/+/command", "device/+/config",
            "\x00", "\xff", "A" * 1000,  # Edge cases
            "../../../etc/passwd", "..\\..\\..\\windows\\system32",
        ]
        
        client = mqtt.Client(
            client_id=self._generate_client_id(client_id_prefix),
            protocol=mqtt.MQTTv311
        )
        
        if username:
            client.username_pw_set(username, password or "")
        
        try:
            client.connect(host, port, keepalive=60)
            client.loop_start()
            time.sleep(0.5)
        except Exception as e:
            error(f"Failed to connect for subscribe fuzzing: {e}")
            return
        
        try:
            for i, topic in enumerate(fuzz_topics[:count]):
                if self._stop_flag.is_set():
                    break
                
                # Try different QoS levels
                for qos in [0, 1, 2]:
                    try:
                        result, mid = client.subscribe(topic, qos=qos)
                        self._stats["subscribes"] += 1
                        
                        if result == mqtt.MQTT_ERR_SUCCESS:
                            if verbose:
                                success(f"  Subscribed to: {topic[:50]} (QoS {qos})")
                        else:
                            if verbose:
                                warning(f"  Subscribe failed: {topic[:30]} (QoS {qos})")
                                
                    except Exception as e:
                        self._stats["errors"] += 1
                        if verbose:
                            error(f"  Subscribe error: {e}")
                
                time.sleep(0.1)
            
            console.print()
            
        except KeyboardInterrupt:
            console.print()
            warning("Fuzzing interrupted")
        finally:
            client.loop_stop()
            client.disconnect()
        
        success(f"Subscribed to {self._stats['subscribes']} topic patterns")

    def _fuzz_connect(self, host: str, port: int, count: int, verbose: bool):
        """Fuzz connection handling with malformed packets."""
        info("[bold]Phase: Connect Fuzzing[/bold]")
        info("Testing connection handling with various payloads...")
        console.print()
        
        # We'll use raw socket for this to send malformed packets
        connect_payloads = [
            b"\x00",  # Too short
            b"\x10\x00",  # Minimal CONNECT
            b"\x10\xff\xff",  # Wrong remaining length
            b"\x10\x10\x00\x04MQTT\x05\x00\x00<",  # Malformed protocol
            b"\x10\x0e\x00\x04MQTT\x04\x00\x00\x3c\x00\x00",  # No client ID
            b"\x10\x20" + b"\x00" * 30,  # Null bytes
            b"\x10\x20" + b"\xff" * 30,  # High bytes
            b"\x10\x10\x00\x06MQIsdp\x03\x02\x00<\x00\x00",  # MQTT 3.1
        ]
        
        for i, payload in enumerate(connect_payloads[:count]):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((host, port))
                sock.send(payload)
                
                try:
                    response = sock.recv(4)
                    if verbose:
                        info(f"  [{i+1}] Sent {len(payload)} bytes, got response: {response.hex()}")
                except socket.timeout:
                    if verbose:
                        info(f"  [{i+1}] Sent {len(payload)} bytes, no response (timeout)")
                
                self._stats["connects"] += 1
                
            except Exception as e:
                self._stats["errors"] += 1
                if verbose:
                    error(f"  [{i+1}] Connection error: {e}")
            finally:
                try:
                    sock.close()
                except:
                    pass
            
            time.sleep(0.1)
        
        success(f"Sent {self._stats['connects']} connect fuzz packets")

    def _test_acl_bypass(self, host: str, port: int, username: str, password: str,
                         client_id_prefix: str):
        """Test for ACL bypass vulnerabilities."""
        info("[bold]Phase: ACL Bypass Testing[/bold]")
        console.print()
        
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            return
        
        # Common restricted topics
        test_topics = [
            ("$SYS/#", "System info (often restricted)"),
            ("$CONTROL/#", "Control channel"),
            ("admin/#", "Admin topics"),
            ("config/#", "Configuration topics"),
            ("device/+/command", "Device commands"),
            ("device/+/config", "Device configuration"),
            ("internal/#", "Internal topics"),
            ("debug/#", "Debug topics"),
            ("secret/#", "Secret topics"),
            ("private/#", "Private topics"),
            ("../", "Path traversal attempt"),
            ("//", "Double slash"),
        ]
        
        client = mqtt.Client(
            client_id=self._generate_client_id(client_id_prefix),
            protocol=mqtt.MQTTv311
        )
        
        if username:
            client.username_pw_set(username, password or "")
        
        received_messages = []
        
        def on_message(c, userdata, msg):
            received_messages.append({
                "topic": msg.topic,
                "payload": msg.payload[:100],
                "qos": msg.qos,
            })
        
        client.on_message = on_message
        
        try:
            client.connect(host, port, keepalive=60)
            client.loop_start()
            time.sleep(0.5)
        except Exception as e:
            error(f"Failed to connect for ACL test: {e}")
            return
        
        acl_results = []
        
        try:
            for topic, desc in test_topics:
                # Try to subscribe
                result, mid = client.subscribe(topic, qos=0)
                
                if result == mqtt.MQTT_ERR_SUCCESS:
                    acl_results.append((topic, desc, "SUBSCRIBE OK", "Check access"))
                else:
                    acl_results.append((topic, desc, "SUBSCRIBE DENIED", ""))
                
                # Try to publish
                pub_result = client.publish(topic, "ACL_TEST", qos=0)
                time.sleep(0.1)
            
            # Wait for potential messages
            time.sleep(1)
            
            console.print()
            if acl_results:
                columns = [
                    ("Topic", "cyan"),
                    ("Description", "white"),
                    ("Status", "yellow"),
                    ("Note", "dim"),
                ]
                print_table("ACL Test Results", columns, acl_results)
            
            if received_messages:
                warning(f"Received {len(received_messages)} messages from restricted topics!")
                for msg in received_messages[:5]:
                    result(f"  Topic: {msg['topic']} | Payload: {msg['payload']}")
            
        except KeyboardInterrupt:
            warning("ACL test interrupted")
        finally:
            client.loop_stop()
            client.disconnect()

    def _generate_client_id(self, prefix: str = "") -> str:
        """Generate a random client ID."""
        if prefix:
            return f"{prefix}_{random.randint(1000, 9999)}"
        return f"iotwizz_fuzzer_{random.randint(10000, 99999)}"

    def _generate_payload(self, payload_type: str) -> bytes:
        """Generate fuzzing payload based on type."""
        if payload_type == "random":
            return self._payload_random()
        elif payload_type == "format":
            return self._payload_format_string()
        elif payload_type == "overflow":
            return self._payload_overflow()
        elif payload_type == "json":
            return self._payload_json_fuzz()
        else:  # mixed
            return random.choice([
                self._payload_random,
                self._payload_format_string,
                self._payload_overflow,
                self._payload_json_fuzz,
            ])()

    def _payload_random(self) -> bytes:
        """Random bytes payload."""
        size = random.choice([10, 100, 1000, random.randint(1, 5000)])
        return bytes([random.randint(0, 255) for _ in range(size)])

    def _payload_format_string(self) -> bytes:
        """Format string payload."""
        formats = [
            b"%s" * 10,
            b"%n" * 10,
            b"%x" * 20,
            b"%p" * 20,
            b"%s%n%p%x%d",
            b"AAAA%08x.%08x.%08x.%08x",
            b"%s%s%s%s%s%s%s%s%s%s",
        ]
        return random.choice(formats)

    def _payload_overflow(self) -> bytes:
        """Buffer overflow payload."""
        size = random.choice([100, 500, 1000, 5000, 10000])
        char = random.choice([b"A", b"\x00", b"\xff", b"\x41"])
        return char * size

    def _payload_json_fuzz(self) -> bytes:
        """Malformed JSON payload."""
        json_payloads = [
            b'{"cmd": "on"}',
            b'{"cmd": "on", "value": ' + b'"' + b"A" * 1000 + b'"}',
            b'{"cmd": "on", "value": null}',
            b'{"' + b'"' * 100 + b'": "test"}',
            b'{"cmd": "' + b"\x00" * 50 + b'"}',
            b'{"nested": {"deep": {"value": ' + b'"' + b"A" * 500 + b'"}}}',
            b'[' + b'"test",' * 100 + b'"end"]',
            b'{"overflow": "' + b"A" * 10000 + b'"}',
        ]
        return random.choice(json_payloads)

    def _generate_fuzz_topic(self, base_topic: str) -> str:
        """Generate a fuzzed topic name."""
        fuzz_chars = string.ascii_letters + string.digits + "/_+$#"
        
        patterns = [
            lambda: "".join(random.choices(fuzz_chars, k=random.randint(1, 50))),
            lambda: base_topic.replace("#", "".join(random.choices(string.ascii_letters, k=5))),
            lambda: "/" * random.randint(1, 10),
            lambda: "device/" + "/".join(random.choices(string.ascii_lowercase, k=random.randint(2, 5))),
            lambda: "$SYS/" + "".join(random.choices(string.ascii_letters, k=10)),
        ]
        
        return random.choice(patterns)()

    def _show_summary(self):
        """Show fuzzing summary."""
        columns = [
            ("Metric", "cyan"),
            ("Count", "white"),
        ]
        rows = [
            ("Publish Messages", str(self._stats["publishes"])),
            ("Subscribe Requests", str(self._stats["subscribes"])),
            ("Connect Attempts", str(self._stats["connects"])),
            ("Errors", str(self._stats["errors"])),
        ]
        print_table("Fuzzing Summary", columns, rows)

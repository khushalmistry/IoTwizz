"""
IoTwizz Module: Default Credential Checker
Check IoT devices for default/known credentials over SSH, Telnet, HTTP, FTP.
"""

import socket
import json
import os
import time
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console
from iotwizz.config import Config


class DefaultCreds(BaseModule):
    """Check IoT devices for default credentials."""

    def __init__(self):
        super().__init__()
        self.name = "Default Credential Checker"
        self.description = "Test IoT devices for default/known credentials (SSH, Telnet, HTTP, FTP)"
        self.author = "IoTwizz Team"
        self.category = "recon"

        self.options = {
            "TARGET": {
                "value": "",
                "required": True,
                "description": "Target IP address or hostname",
            },
            "SERVICE": {
                "value": "ssh",
                "required": True,
                "description": "Service to test: ssh, telnet, http, ftp",
            },
            "PORT": {
                "value": "",
                "required": False,
                "description": "Port number (auto-detected based on service if empty)",
            },
            "CREDS_FILE": {
                "value": "",
                "required": False,
                "description": "Custom credentials file (JSON). Uses built-in DB if empty",
            },
            "DELAY": {
                "value": "1",
                "required": False,
                "description": "Delay between attempts in seconds (default: 1)",
            },
            "STOP_ON_SUCCESS": {
                "value": "true",
                "required": False,
                "description": "Stop after first successful login (default: true)",
            },
        }

    def _get_default_port(self, service: str) -> int:
        """Get default port for a service."""
        ports = {
            "ssh": 22,
            "telnet": 23,
            "http": 80,
            "https": 443,
            "ftp": 21,
        }
        return ports.get(service, 0)

    def _load_credentials(self) -> list:
        """Load credentials database."""
        creds_file = self.get_option("CREDS_FILE")
        if not creds_file:
            creds_file = Config.CREDS_FILE

        if not os.path.isfile(creds_file):
            warning(f"Credentials file not found: {creds_file}")
            # Return a basic built-in set
            return self._builtin_creds()

        try:
            with open(creds_file, "r") as f:
                data = json.load(f)
            return data.get("credentials", [])
        except (json.JSONDecodeError, IOError) as e:
            error(f"Error loading credentials: {e}")
            return self._builtin_creds()

    def _builtin_creds(self) -> list:
        """Return built-in default credentials."""
        return [
            {"username": "root", "password": "root", "device": "Generic Linux"},
            {"username": "admin", "password": "admin", "device": "Generic Router"},
            {"username": "admin", "password": "password", "device": "Generic"},
            {"username": "admin", "password": "1234", "device": "Generic"},
            {"username": "admin", "password": "", "device": "Generic"},
            {"username": "root", "password": "", "device": "Embedded Linux"},
            {"username": "root", "password": "toor", "device": "Generic Linux"},
            {"username": "user", "password": "user", "device": "Generic"},
            {"username": "admin", "password": "12345", "device": "Generic"},
            {"username": "root", "password": "12345", "device": "Generic"},
            {"username": "ubnt", "password": "ubnt", "device": "Ubiquiti"},
            {"username": "admin", "password": "ubnt", "device": "Ubiquiti"},
            {"username": "pi", "password": "raspberry", "device": "Raspberry Pi"},
            {"username": "admin", "password": "default", "device": "Generic Router"},
            {"username": "admin", "password": "changeme", "device": "Generic"},
            {"username": "root", "password": "password", "device": "Generic"},
            {"username": "admin", "password": "admin123", "device": "Generic"},
            {"username": "service", "password": "service", "device": "Generic"},
            {"username": "guest", "password": "guest", "device": "Generic"},
            {"username": "root", "password": "admin", "device": "Generic"},
        ]

    def run(self):
        """Test credentials against the target."""
        target = self.get_option("TARGET")
        service = (self.get_option("SERVICE") or "ssh").lower()
        port = self.get_option("PORT")
        delay = float(self.get_option("DELAY") or 1)
        stop_on_success = (self.get_option("STOP_ON_SUCCESS") or "true").lower() == "true"

        if not port:
            port = self._get_default_port(service)
        else:
            port = int(port)

        if not port:
            error(f"Unknown service: {service}")
            info("Supported services: ssh, telnet, http, ftp")
            return

        creds = self._load_credentials()
        info(f"Target: [cyan]{target}:{port}[/cyan] ({service.upper()})")
        info(f"Loaded [cyan]{len(creds)}[/cyan] credential pairs")
        info(f"Delay: {delay}s | Stop on success: {stop_on_success}")
        console.print()

        # Check if target is reachable
        info("Checking target connectivity...")
        from iotwizz.utils.network_helpers import is_port_open
        if not is_port_open(target, port):
            error(f"Port {port} is not open on {target}")
            info("Check target IP and ensure the service is running")
            return

        success(f"Port {port} is open — starting credential test")
        console.print()

        # Select the right checker
        checkers = {
            "ssh": self._check_ssh,
            "telnet": self._check_telnet,
            "ftp": self._check_ftp,
            "http": self._check_http,
        }

        checker = checkers.get(service)
        if not checker:
            error(f"Service '{service}' is not supported yet")
            return

        found_creds = []
        total = len(creds)

        for idx, cred in enumerate(creds, 1):
            username = cred["username"]
            password = cred["password"]
            device = cred.get("device", "Unknown")

            info(f"[{idx}/{total}] Trying: [cyan]{username}[/cyan]:[cyan]{password or '(blank)'}[/cyan]")

            try:
                if checker(target, port, username, password):
                    console.print()
                    success(f"[bold green]🎯 VALID CREDENTIALS FOUND![/bold green]")
                    result(f"  Username: [cyan]{username}[/cyan]")
                    result(f"  Password: [cyan]{password or '(blank)'}[/cyan]")
                    result(f"  Device:   [yellow]{device}[/yellow]")
                    console.print()

                    found_creds.append((username, password, device))

                    if stop_on_success:
                        break
            except Exception as e:
                error(f"  Error: {e}")

            time.sleep(delay)

        # Summary
        console.print()
        if found_creds:
            columns = [
                ("Username", "cyan"),
                ("Password", "green"),
                ("Device Type", "yellow"),
            ]
            print_table("Valid Credentials Found", columns, found_creds)
            warning("⚠ Default credentials are a critical security risk!")
        else:
            info("No default credentials found for this target")
            info("Device may be using custom credentials")

    def _check_ssh(self, host, port, username, password) -> bool:
        """Test SSH credentials."""
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=5,
                allow_agent=False,
                look_for_keys=False,
            )
            client.close()
            return True
        except ImportError:
            error("paramiko not installed. Run: pip install paramiko")
            return False
        except Exception:
            return False

    def _check_telnet(self, host, port, username, password) -> bool:
        """Test Telnet credentials."""
        try:
            import telnetlib
            tn = telnetlib.Telnet(host, port, timeout=5)

            tn.read_until(b"login: ", timeout=5)
            tn.write(username.encode() + b"\n")

            tn.read_until(b"assword: ", timeout=5)
            tn.write(password.encode() + b"\n")

            time.sleep(1)
            result_data = tn.read_very_eager().decode("utf-8", errors="replace")
            tn.close()

            # Check for success indicators
            fail_indicators = ["incorrect", "failed", "denied", "invalid", "error", "login:"]
            success_indicators = ["$", "#", ">", "welcome", "last login"]

            result_lower = result_data.lower()
            if any(f in result_lower for f in fail_indicators):
                return False
            if any(s in result_lower for s in success_indicators):
                return True
            return False
        except Exception:
            return False

    def _check_ftp(self, host, port, username, password) -> bool:
        """Test FTP credentials."""
        try:
            import ftplib
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=5)
            ftp.login(username, password)
            ftp.quit()
            return True
        except Exception:
            return False

    def _check_http(self, host, port, username, password) -> bool:
        """Test HTTP Basic Auth credentials."""
        try:
            import requests
            url = f"http://{host}:{port}/"
            response = requests.get(
                url,
                auth=(username, password),
                timeout=5,
                verify=False,
            )
            # 200 or 301/302 = success, 401/403 = failed
            return response.status_code not in [401, 403, 407]
        except ImportError:
            error("requests not installed. Run: pip install requests")
            return False
        except Exception:
            return False

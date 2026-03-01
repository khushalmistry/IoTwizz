"""
IoTwizz Module: Default Credential Checker
Test IoT devices for default/known credentials over SSH, Telnet, HTTP, FTP, and more.
Supports threading for faster testing and multiple authentication methods.
"""

import socket
import json
import os
import time
import threading
import concurrent.futures
from typing import Optional, List, Dict, Tuple
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator
from iotwizz.config import Config


class DefaultCreds(BaseModule):
    """Check IoT devices for default credentials with threading support."""

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
                "description": "Service to test: ssh, telnet, http, https, ftp, all",
            },
            "PORT": {
                "value": "",
                "required": False,
                "description": "Port number (auto-detected based on service if empty)",
            },
            "CREDS_FILE": {
                "value": "",
                "required": False,
                "description": "Custom credentials JSON file (uses built-in DB if empty)",
            },
            "THREADS": {
                "value": "5",
                "required": False,
                "description": "Number of concurrent threads (default: 5)",
            },
            "DELAY": {
                "value": "0.5",
                "required": False,
                "description": "Delay between attempts in seconds (default: 0.5)",
            },
            "TIMEOUT": {
                "value": "10",
                "required": False,
                "description": "Connection timeout in seconds (default: 10)",
            },
            "STOP_ON_SUCCESS": {
                "value": "true",
                "required": False,
                "description": "Stop after first successful login (default: true)",
            },
            "VERBOSE": {
                "value": "false",
                "required": False,
                "description": "Show all attempts including failures (default: false)",
            },
            "HTTP_PATH": {
                "value": "/",
                "required": False,
                "description": "HTTP path for web auth (default: /)",
            },
            "HTTP_METHOD": {
                "value": "basic",
                "required": False,
                "description": "HTTP auth method: basic, digest, form (default: basic)",
            },
            "USER_AS_PASSWORD": {
                "value": "true",
                "required": False,
                "description": "Try username as password (default: true)",
            },
            "BLANK_PASSWORD": {
                "value": "true",
                "required": False,
                "description": "Try blank passwords (default: true)",
            },
        }
        
        # Thread-safe result collection
        self._results_lock = threading.Lock()
        self._found_creds = []
        self._stop_flag = threading.Event()

    def _get_default_port(self, service: str) -> int:
        """Get default port for a service."""
        ports = {
            "ssh": 22,
            "telnet": 23,
            "http": 80,
            "https": 443,
            "ftp": 21,
        }
        return ports.get(service.lower(), 0)

    def _load_credentials(self) -> List[Dict]:
        """Load credentials database."""
        creds_file = self.get_option("CREDS_FILE")
        if not creds_file:
            creds_file = Config.CREDS_FILE

        try:
            with open(creds_file, "r") as f:
                data = json.load(f)
            creds = data.get("credentials", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if creds_file != Config.CREDS_FILE:
                warning(f"Could not load credentials file: {e}")
            creds = None

        if not creds:
            creds = self._builtin_creds()
        
        # Add variations if enabled
        user_as_pass = (self.get_option("USER_AS_PASSWORD") or "true").lower() == "true"
        blank_pass = (self.get_option("BLANK_PASSWORD") or "true").lower() == "true"
        
        expanded_creds = []
        seen = set()
        
        for cred in creds:
            key = (cred["username"], cred["password"])
            if key not in seen:
                seen.add(key)
                expanded_creds.append(cred)
            
            # Add username as password variation
            if user_as_pass and cred["username"]:
                key = (cred["username"], cred["username"])
                if key not in seen:
                    seen.add(key)
                    expanded_creds.append({
                        "username": cred["username"],
                        "password": cred["username"],
                        "device": f"{cred.get('device', 'Generic')} (user=pass)"
                    })
        
        # Add common blank password attempts
        if blank_pass:
            for username in ["admin", "root", "user", "guest", ""]:
                key = (username, "")
                if key not in seen:
                    seen.add(key)
                    expanded_creds.append({
                        "username": username,
                        "password": "",
                        "device": "Blank password test"
                    })
        
        return expanded_creds

    def _builtin_creds(self) -> List[Dict]:
        """Return built-in default credentials."""
        return [
            # Generic
            {"username": "root", "password": "root", "device": "Generic Linux"},
            {"username": "admin", "password": "admin", "device": "Generic Router"},
            {"username": "admin", "password": "password", "device": "Generic"},
            {"username": "admin", "password": "1234", "device": "Generic"},
            {"username": "admin", "password": "12345", "device": "Generic"},
            {"username": "admin", "password": "123456", "device": "Generic"},
            {"username": "admin", "password": "admin123", "device": "Generic"},
            {"username": "admin", "password": "administrator", "device": "Generic"},
            {"username": "admin", "password": "changeme", "device": "Generic"},
            {"username": "admin", "password": "default", "device": "Generic"},
            {"username": "root", "password": "toor", "device": "Generic Linux"},
            {"username": "root", "password": "pass", "device": "Generic"},
            {"username": "root", "password": "password", "device": "Generic"},
            {"username": "user", "password": "user", "device": "Generic"},
            {"username": "guest", "password": "guest", "device": "Generic"},
            {"username": "guest", "password": "", "device": "Guest Account"},
            {"username": "service", "password": "service", "device": "Generic"},
            {"username": "support", "password": "support", "device": "Generic"},
            {"username": "test", "password": "test", "device": "Test Account"},
            {"username": "debug", "password": "debug", "device": "Debug Account"},
            
            # Embedded/IoT specific
            {"username": "root", "password": "", "device": "Embedded Linux"},
            {"username": "admin", "password": "", "device": "IoT Device"},
            {"username": "", "password": "admin", "device": "No username device"},
            {"username": "", "password": "", "device": "No auth device"},
            
            # Raspberry Pi
            {"username": "pi", "password": "raspberry", "device": "Raspberry Pi"},
            {"username": "pi", "password": "raspberrypi", "device": "Raspberry Pi"},
            
            # Routers
            {"username": "admin", "password": "ubnt", "device": "Ubiquiti"},
            {"username": "ubnt", "password": "ubnt", "device": "Ubiquiti"},
            {"username": "admin", "password": "linksys", "device": "Linksys"},
            {"username": "admin", "password": "default", "device": "Linksys"},
            {"username": "admin", "password": "motorola", "device": "Motorola"},
            {"username": "admin", "password": "cisco", "device": "Cisco"},
            {"username": "cisco", "password": "cisco", "device": "Cisco"},
            {"username": "admin", "password": "Cisco", "device": "Cisco"},
            {"username": "admin", "password": "netgear1", "device": "Netgear"},
            {"username": "admin", "password": "password1", "device": "Netgear"},
            {"username": "admin", "password": "tplink", "device": "TP-Link"},
            {"username": "admin", "password": "ttnet", "device": "TP-Link"},
            {"username": "admin", "password": "superadmin", "device": "Huawei"},
            {"username": "telecomadmin", "password": "admintelecom", "device": "Huawei"},
            {"username": "admin", "password": "smcadmin", "device": "SMC Router"},
            
            # IP Cameras
            {"username": "root", "password": "vizxv", "device": "Dahua IP Camera"},
            {"username": "root", "password": "xc3511", "device": "IP Camera"},
            {"username": "root", "password": "xmhdipc", "device": "XM IP Camera"},
            {"username": "admin", "password": "7ujMko0admin", "device": "Dahua DVR"},
            {"username": "admin", "password": "admin123", "device": "Hikvision"},
            {"username": "admin", "password": "12345", "device": "Hikvision"},
            {"username": "888888", "password": "888888", "device": "Dahua DVR"},
            {"username": "666666", "password": "666666", "device": "Dahua DVR"},
            
            # ISP Routers
            {"username": "admin", "password": "comcast", "device": "Comcast"},
            {"username": "cusadmin", "password": "highspeed", "device": "Comcast"},
            {"username": "admin", "password": "sky", "device": "Sky Router"},
            {"username": "admin", "password": "telus", "device": "Telus"},
            {"username": "admin", "password": "att", "device": "AT&T"},
            
            # NAS
            {"username": "admin", "password": "synology", "device": "Synology NAS"},
            {"username": "admin", "password": "qnap", "device": "QNAP NAS"},
        ]

    def run(self):
        """Test credentials against the target."""
        target = self.get_option("TARGET")
        service = (self.get_option("SERVICE") or "ssh").lower()
        port = self.get_option_int("PORT")
        threads = self.get_option_int("THREADS", default=5)
        delay = self.get_option_float("DELAY", default=0.5)
        timeout = self.get_option_float("TIMEOUT", default=10.0)
        stop_on_success = (self.get_option("STOP_ON_SUCCESS") or "true").lower() == "true"
        verbose = (self.get_option("VERBOSE") or "false").lower() == "true"

        # Handle "all" service mode
        if service == "all":
            self._run_all_services(target, threads, delay, timeout, stop_on_success, verbose)
            return

        if not port:
            port = self._get_default_port(service)

        if not port:
            error(f"Unknown service: {service}")
            info("Supported services: ssh, telnet, http, https, ftp, all")
            return

        # Load credentials
        creds = self._load_credentials()
        
        info(f"Target: [cyan]{target}:{port}[/cyan] ({service.upper()})")
        info(f"Credential pairs: [cyan]{len(creds)}[/cyan] | Threads: {threads} | Timeout: {timeout}s")
        info(f"Delay: {delay}s | Stop on success: {stop_on_success}")
        console.print()

        # Check connectivity
        info("Checking target connectivity...")
        from iotwizz.utils.network_helpers import is_port_open
        
        if not is_port_open(target, port, timeout=5):
            error(f"Port {port} is not open on {target}")
            info("Check target IP and ensure the service is running")
            return

        success(f"Port {port} is open — starting credential test")
        console.print()

        # Reset state
        self._found_creds = []
        self._stop_flag.clear()

        # Select checker
        checkers = {
            "ssh": self._check_ssh,
            "telnet": self._check_telnet,
            "ftp": self._check_ftp,
            "http": self._check_http,
            "https": self._check_http,
        }

        checker = checkers.get(service)
        if not checker:
            error(f"Service '{service}' is not supported yet")
            return

        # Use https for https service
        use_ssl = service == "https"

        # Run with thread pool
        start_time = time.time()
        total = len(creds)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {}
            for idx, cred in enumerate(creds, 1):
                if self._stop_flag.is_set():
                    break
                future = executor.submit(
                    self._test_credential,
                    checker, target, port, cred, idx, total, 
                    timeout, delay, verbose, use_ssl
                )
                futures[future] = cred
            
            for future in concurrent.futures.as_completed(futures):
                if self._stop_flag.is_set():
                    break
                try:
                    future.result()
                except Exception as e:
                    if verbose:
                        error(f"Thread error: {e}")

        elapsed = time.time() - start_time

        # Summary
        console.print()
        print_separator()
        
        if self._found_creds:
            columns = [
                ("Username", "cyan"),
                ("Password", "green"),
                ("Device Type", "yellow"),
            ]
            print_table("Valid Credentials Found", columns, self._found_creds)
            warning("⚠ Default credentials are a CRITICAL security risk!")
            warning("⚠ Change passwords immediately or disable the service!")
        else:
            info(f"No valid credentials found (tested {total} combinations in {elapsed:.1f}s)")
            info("Device may be using custom credentials or have account lockout enabled")

    def _run_all_services(self, target: str, threads: int, delay: float, 
                          timeout: float, stop_on_success: bool, verbose: bool):
        """Test all services on common ports."""
        info(f"Target: [cyan]{target}[/cyan] — Testing all services")
        console.print()

        from iotwizz.utils.network_helpers import scan_common_ports
        
        info("Scanning common ports...")
        open_ports = scan_common_ports(target, timeout=3)
        
        if not open_ports:
            error("No common ports are open on target")
            return

        success(f"Found {len(open_ports)} open ports")
        for p in open_ports:
            info(f"  → {p['port']}/{p['service']}")
        console.print()

        # Map services to checkers
        service_map = {
            21: ("ftp", self._check_ftp),
            22: ("ssh", self._check_ssh),
            23: ("telnet", self._check_telnet),
            80: ("http", self._check_http),
            443: ("https", self._check_http),
            8080: ("http", self._check_http),
            8443: ("https", self._check_http),
        }

        all_found = []
        
        for port_info in open_ports:
            port = port_info["port"]
            if port not in service_map:
                continue
            
            service_name, checker = service_map[port]
            use_ssl = service_name == "https"
            
            info(f"\n[cyan]Testing {service_name.upper()} on port {port}...[/cyan]")
            
            self._found_creds = []
            self._stop_flag.clear()
            
            creds = self._load_credentials()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                futures = {}
                for idx, cred in enumerate(creds, 1):
                    if self._stop_flag.is_set():
                        break
                    future = executor.submit(
                        self._test_credential, checker, target, port, cred, 
                        idx, len(creds), timeout, delay, verbose, use_ssl
                    )
                    futures[future] = cred
                
                for future in concurrent.futures.as_completed(futures):
                    if self._stop_flag.is_set():
                        break
                    try:
                        future.result()
                    except Exception:
                        pass
            
            if self._found_creds:
                for found in self._found_creds:
                    all_found.append((found[0], found[1], f"{found[2]} ({service_name})"))
                if stop_on_success:
                    break

        console.print()
        print_separator()
        
        if all_found:
            columns = [
                ("Username", "cyan"),
                ("Password", "green"),
                ("Service", "yellow"),
            ]
            print_table("All Valid Credentials Found", columns, all_found)
        else:
            info("No valid credentials found on any service")

    def _test_credential(self, checker, target: str, port: int, cred: Dict,
                         idx: int, total: int, timeout: float, delay: float,
                         verbose: bool, use_ssl: bool = False) -> bool:
        """Test a single credential pair."""
        if self._stop_flag.is_set():
            return False
        
        username = cred["username"]
        password = cred["password"]
        device = cred.get("device", "Unknown")
        
        if verbose:
            info(f"[{idx}/{total}] Trying: [cyan]{username}[/cyan]:[cyan]{password or '(blank)'}[/cyan]")
        
        try:
            result = checker(target, port, username, password, timeout, use_ssl)
            
            if result:
                with self._results_lock:
                    self._found_creds.append((username, password or "(blank)", device))
                
                console.print()
                success(f"[bold green]🎯 VALID CREDENTIALS FOUND![/bold green]")
                result(f"  Service:    [cyan]{cred.get('service', 'unknown')}[/cyan]")
                result(f"  Username:   [cyan]{username}[/cyan]")
                result(f"  Password:   [cyan]{password or '(blank)'}[/cyan]")
                result(f"  Device:     [yellow]{device}[/yellow]")
                console.print()
                
                self._stop_flag.set()
                return True
                
        except Exception as e:
            if verbose:
                error(f"  Error: {e}")
        
        time.sleep(delay)
        return False

    def _check_ssh(self, host: str, port: int, username: str, password: str, 
                   timeout: float = 10, use_ssl: bool = False) -> bool:
        """Test SSH credentials."""
        client = None
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=timeout,
            )
            return True
        except ImportError:
            raise ImportError("paramiko not installed. Run: pip install paramiko")
        except paramiko.AuthenticationException:
            return False
        except paramiko.SSHException:
            return False
        except socket.timeout:
            return False
        except Exception:
            return False
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def _check_telnet(self, host: str, port: int, username: str, password: str,
                      timeout: float = 10, use_ssl: bool = False) -> bool:
        """Test Telnet credentials."""
        tn = None
        try:
            import telnetlib
            tn = telnetlib.Telnet(host, port, timeout=timeout)

            # Try multiple login prompts
            login_prompts = [b"login: ", b"Login: ", b"username: ", b"Username: ", 
                           b"user: ", b"User: ", b"name: "]
            matched = False
            for prompt in login_prompts:
                try:
                    tn.read_until(prompt, timeout=timeout / 2)
                    matched = True
                    break
                except Exception:
                    continue
            
            if not matched:
                return False

            tn.write(username.encode() + b"\r\n")
            time.sleep(0.5)

            # Try multiple password prompts
            pass_prompts = [b"assword: ", b"Password: ", b"passwd: ", b"PASS: "]
            matched = False
            for prompt in pass_prompts:
                try:
                    tn.read_until(prompt, timeout=timeout / 2)
                    matched = True
                    break
                except Exception:
                    continue
            
            if not matched:
                return False

            tn.write(password.encode() + b"\r\n")
            time.sleep(1)

            result_data = tn.read_very_eager().decode("utf-8", errors="replace").lower()

            # Check for failure indicators
            fail_indicators = ["incorrect", "failed", "denied", "invalid", "error", 
                            "login:", "password:", "wrong", "bad"]
            if any(f in result_data for f in fail_indicators):
                return False

            # Check for success indicators
            success_indicators = ["$", "#", ">", "welcome", "last login", 
                                "busybox", "~", "@", "shell"]
            if any(s in result_data for s in success_indicators):
                return True

            # If we got output without failure indicators, might be success
            return len(result_data) > 10 and not any(f in result_data for f in fail_indicators)

        except Exception:
            return False
        finally:
            if tn:
                try:
                    tn.close()
                except Exception:
                    pass

    def _check_ftp(self, host: str, port: int, username: str, password: str,
                   timeout: float = 10, use_ssl: bool = False) -> bool:
        """Test FTP credentials."""
        ftp = None
        try:
            import ftplib
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(username, password)
            return True
        except ftplib.error_perm:
            return False
        except Exception:
            return False
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass

    def _check_http(self, host: str, port: int, username: str, password: str,
                    timeout: float = 10, use_ssl: bool = False) -> bool:
        """Test HTTP/HTTPS credentials."""
        try:
            import requests
            from requests.auth import HTTPBasicAuth, HTTPDigestAuth
            
            http_path = self.get_option("HTTP_PATH") or "/"
            http_method = (self.get_option("HTTP_METHOD") or "basic").lower()
            
            scheme = "https" if use_ssl else "http"
            url = f"{scheme}://{host}:{port}{http_path}"
            
            # Disable SSL warnings for testing
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            if http_method == "digest":
                auth = HTTPDigestAuth(username, password)
            else:
                auth = HTTPBasicAuth(username, password)
            
            response = requests.get(
                url,
                auth=auth,
                timeout=timeout,
                verify=False,
                allow_redirects=True,
            )
            
            # 200-299 = success, 301/302 redirects handled
            # 401/403 = auth failed
            return response.status_code < 400 and response.status_code not in [401, 403]
            
        except ImportError:
            raise ImportError("requests not installed. Run: pip install requests")
        except requests.exceptions.SSLError:
            # SSL error might mean wrong port or protocol
            return False
        except requests.exceptions.ConnectionError:
            return False
        except requests.exceptions.Timeout:
            return False
        except Exception:
            return False

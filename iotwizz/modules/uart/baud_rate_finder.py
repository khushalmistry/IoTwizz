"""
IoTwizz Module: UART Baud Rate Finder
Auto-detect baud rate of UART serial connections with intelligent analysis.

Tests common baud rates by connecting at each rate and analyzing
the readability and patterns in received data to determine the correct baud rate.
"""

import time
import sys
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator
from iotwizz.utils.serial_helpers import (
    is_readable, get_available_ports, auto_detect_port, 
    open_serial, read_serial_data, analyze_uart_pattern, get_platform_port_hints
)
from iotwizz.config import Config


class BaudRateFinder(BaseModule):
    """Auto-detect UART baud rate with intelligent pattern analysis."""

    def __init__(self):
        super().__init__()
        self.name = "UART Baud Rate Finder"
        self.description = "Auto-detect baud rate of UART serial connections with intelligent analysis"
        self.author = "IoTwizz Team"
        self.category = "uart"

        self.options = {
            "PORT": {
                "value": "",
                "required": True,
                "description": "Serial port (e.g., /dev/ttyUSB0, COM3, /dev/cu.usbserial-*)",
            },
            "AUTO_DETECT": {
                "value": "true",
                "required": False,
                "description": "Auto-detect port if PORT is empty (default: true)",
            },
            "TIMEOUT": {
                "value": "2",
                "required": False,
                "description": "Read timeout per baud rate in seconds (default: 2)",
            },
            "READ_DURATION": {
                "value": "2",
                "required": False,
                "description": "How long to read data at each baud rate (seconds)",
            },
            "SEND_PROMPT": {
                "value": "",
                "required": False,
                "description": "Optional bytes to send (hex: \\x0d or text: press_enter)",
            },
            "STIMULUS": {
                "value": "false",
                "required": False,
                "description": "Send newline to stimulate output (helps with silent devices)",
            },
            "BAUD_RATES": {
                "value": "",
                "required": False,
                "description": "Custom baud rates (comma-separated, e.g., 9600,115200,460800)",
            },
            "STOP_ON_HIGH_CONFIDENCE": {
                "value": "true",
                "required": False,
                "description": "Stop testing when high confidence match is found",
            },
            "LIST_PORTS": {
                "value": "false",
                "required": False,
                "description": "List available serial ports and exit",
            },
        }

    def run(self):
        """Test common baud rates and identify the correct one."""
        list_ports = (self.get_option("LIST_PORTS") or "").lower() == "true"
        
        # List ports mode
        if list_ports:
            self._list_ports()
            return
        
        # Get options
        port = self.get_option("PORT")
        auto_detect = (self.get_option("AUTO_DETECT") or "true").lower() == "true"
        timeout = self.get_option_float("TIMEOUT", default=2.0)
        read_duration = self.get_option_float("READ_DURATION", default=2.0)
        send_prompt = self.get_option("SEND_PROMPT")
        stimulus = (self.get_option("STIMULUS") or "false").lower() == "true"
        custom_bauds = self.get_option("BAUD_RATES")
        stop_on_high = (self.get_option("STOP_ON_HIGH_CONFIDENCE") or "true").lower() == "true"

        # Auto-detect port if not specified
        if not port and auto_detect:
            port = auto_detect_port()
            if port:
                info(f"Auto-detected port: [cyan]{port}[/cyan]")
            else:
                error("No serial port specified and auto-detection failed")
                self._list_ports()
                return
        
        if not port:
            error("No serial port specified. Set PORT option or use LIST_PORTS=true")
            info(get_platform_port_hints())
            return

        # Parse baud rates
        if custom_bauds:
            try:
                baud_rates = [int(b.strip()) for b in custom_bauds.split(",") if b.strip().isdigit()]
                baud_rates = sorted(set(baud_rates))
            except ValueError:
                error("Invalid baud rates format. Use comma-separated integers (e.g., 9600,115200)")
                return
        else:
            baud_rates = Config.DEFAULT_BAUD_RATES

        info(f"Target port: [cyan]{port}[/cyan]")
        info(f"Testing {len(baud_rates)} baud rates: {', '.join(str(b) for b in baud_rates[:5])}{'...' if len(baud_rates) > 5 else ''}")
        info(f"Read duration: {read_duration}s | Timeout: {timeout}s | Stimulus: {'Yes' if stimulus else 'No'}")
        console.print()

        # Import serial here for better error handling
        try:
            import serial
        except ImportError:
            error("pyserial is not installed. Run: pip install pyserial")
            return

        # Prepare stimulus data
        stimulus_data = None
        if stimulus:
            stimulus_data = b"\r\n"
        if send_prompt:
            # Parse hex escapes and special strings
            prompt_str = send_prompt.lower()
            if prompt_str in ("enter", "newline", "cr", "press_enter"):
                stimulus_data = b"\r\n"
            elif prompt_str in ("space", " "):
                stimulus_data = b" "
            elif "\\x" in send_prompt:
                # Parse hex escapes like \x0d\x0a
                try:
                    stimulus_data = send_prompt.encode().decode("unicode_escape").encode("latin-1")
                except Exception:
                    stimulus_data = send_prompt.encode()
            else:
                stimulus_data = send_prompt.encode()

        results_data = []
        best_rate = None
        best_score = 0.0
        best_analysis = None
        high_confidence_found = False

        with console.status("[bold green]Scanning baud rates...[/bold green]") as status:
            for idx, baud in enumerate(baud_rates):
                status.update(f"[bold green]Testing baud rate: {baud} ({idx+1}/{len(baud_rates)})[/bold green]")
                
                ser = None
                try:
                    ser = open_serial(port, baud, timeout=timeout)
                    
                    # Flush buffers
                    try:
                        ser.reset_input_buffer()
                        ser.reset_output_buffer()
                    except Exception:
                        pass
                    
                    time.sleep(0.1)
                    
                    # Send stimulus if configured
                    if stimulus_data:
                        try:
                            ser.write(stimulus_data)
                            ser.flush()
                            time.sleep(0.2)
                        except Exception:
                            pass
                    
                    # Read data
                    data = read_serial_data(ser, duration=read_duration)
                    
                    if data:
                        readable, ratio = is_readable(data)
                        analysis = analyze_uart_pattern(data)
                        
                        # Determine status
                        if analysis.get("has_pattern") and analysis.get("confidence", 0) > 0.8:
                            status_str = "[bold green]PATTERN FOUND[/bold green]"
                            if stop_on_high:
                                high_confidence_found = True
                        elif readable:
                            status_str = "[green]READABLE[/green]"
                        elif ratio > 0.3:
                            status_str = "[yellow]PARTIAL[/yellow]"
                        else:
                            status_str = "[red]GARBLED[/red]"
                        
                        # Create preview
                        preview = data[:50].decode("utf-8", errors="replace").replace("\n", "\\n").replace("\r", "\\r")
                        if len(data) > 50:
                            preview += "..."
                        
                        results_data.append((
                            str(baud),
                            str(len(data)),
                            f"{ratio:.1%}",
                            f"{analysis.get('confidence', 0):.0%}",
                            status_str,
                            preview[:35],
                        ))
                        
                        # Track best match
                        combined_score = (ratio * 0.4) + (analysis.get("confidence", 0) * 0.6)
                        if combined_score > best_score:
                            best_score = combined_score
                            best_rate = baud
                            best_analysis = analysis
                        
                        if readable or analysis.get("has_pattern"):
                            result(f"  → {baud}: {len(data)} bytes, {ratio:.1%} readable, confidence: {analysis.get('confidence', 0):.0%}")
                    else:
                        results_data.append((
                            str(baud), "0", "N/A", "N/A", "[dim]NO DATA[/dim]", "-",
                        ))
                    
                    # Stop if high confidence found
                    if high_confidence_found:
                        break
                        
                except PermissionError as e:
                    error(f"  → Permission denied: {e}")
                    break  # No point trying other baud rates if we can't open the port
                except Exception as e:
                    error_str = str(e)
                    if "could not open" in error_str.lower() or "not found" in error_str.lower():
                        error(f"  → Cannot open port: {e}")
                        break  # Port doesn't exist
                    results_data.append((str(baud), "ERR", "N/A", "N/A", "[red]ERROR[/red]", str(e)[:30]))
                finally:
                    if ser is not None:
                        try:
                            if ser.is_open:
                                ser.close()
                        except Exception:
                            pass

        # Display results table
        console.print()
        if results_data:
            columns = [
                ("Baud Rate", "cyan"),
                ("Bytes", "white"),
                ("Readable", "yellow"),
                ("Confidence", "magenta"),
                ("Status", "white"),
                ("Preview", "dim"),
            ]
            print_table("Baud Rate Scan Results", columns, results_data, show_lines=True)

        # Report best match
        print_separator()
        
        if best_rate and best_score > 0.5:
            console.print()
            success(f"[bold]Most likely baud rate: [cyan]{best_rate}[/cyan][/bold]")
            info(f"Confidence: {best_score:.0%}")
            
            if best_analysis:
                if best_analysis.get("pattern_type"):
                    result(f"Pattern detected: {best_analysis['pattern_type']}")
            
            console.print()
            info(f"Connect with: [cyan]screen {port} {best_rate}[/cyan]")
            info(f"Or use minicom: [cyan]minicom -D {port} -b {best_rate}[/cyan]")
            if sys.platform == "linux":
                info(f"Or picocom: [cyan]picocom -b {best_rate} {port}[/cyan]")
            
        elif best_rate and best_score > 0.2:
            console.print()
            warning(f"Best candidate: [cyan]{best_rate}[/cyan] (confidence: {best_score:.0%})")
            warning("Low confidence — device may be silent or wiring may be incorrect")
            info("Tips:")
            info("  1. Check TX/RX connections (swap them)")
            info("  2. Ensure device is powered and transmitting")
            info("  3. Try enabling STIMULUS=true to send newline")
            info("  4. Increase READ_DURATION for slower devices")
        else:
            console.print()
            error("Could not determine baud rate — no readable data at any rate")
            info("Troubleshooting tips:")
            info("  1. Check wiring (TX→RX, RX→TX, GND→GND)")
            info("  2. Verify device is powered on")
            info("  3. Device may be silent — try STIMULUS=true")
            info("  4. Check voltage levels (3.3V vs 5V)")
            info("  5. Try pressing buttons on the device to trigger output")

    def _list_ports(self):
        """List available serial ports with detailed information."""
        ports = get_available_ports()
        
        if not ports:
            warning("No serial ports found!")
            info("")
            info("Troubleshooting:")
            if sys.platform == "linux":
                info("  - Check if device is connected: lsusb")
                info("  - Check kernel messages: dmesg | tail")
                info("  - Load USB-serial driver: sudo modprobe usbserial")
            elif sys.platform == "darwin":
                info("  - Check System Information > USB")
                info("  - Try: ls /dev/cu.* /dev/tty.*")
            elif sys.platform == "win32":
                info("  - Check Device Manager > Ports (COM & LPT)")
                info("  - Install FTDI/CH340 drivers if needed")
            return
        
        columns = [
            ("Port", "cyan"),
            ("Description", "white"),
            ("Manufacturer", "dim"),
            ("VID:PID", "yellow"),
        ]
        rows = []
        for p in ports:
            vid_pid = f"{p.get('vid', '?')}:{p.get('pid', '?')}" if p.get("vid") else "N/A"
            rows.append((
                p["device"],
                p["description"][:40],
                p.get("manufacturer", "Unknown")[:20],
                vid_pid,
            ))
        
        print_table("Available Serial Ports", columns, rows)
        
        info(get_platform_port_hints())

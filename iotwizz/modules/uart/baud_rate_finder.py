"""
IoTwizz Module: UART Baud Rate Finder
Automatically detect the baud rate of a UART serial connection.

Tests common baud rates by connecting at each rate and analyzing
the readability of received data to determine the correct baud rate.
"""

import time
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console
from iotwizz.utils.serial_helpers import is_readable, get_available_ports
from iotwizz.config import Config


class BaudRateFinder(BaseModule):
    """Auto-detect UART baud rate by testing common rates."""

    def __init__(self):
        super().__init__()
        self.name = "UART Baud Rate Finder"
        self.description = "Auto-detect baud rate of a UART serial connection"
        self.author = "IoTwizz Team"
        self.category = "uart"

        self.options = {
            "PORT": {
                "value": "",
                "required": True,
                "description": "Serial port (e.g., /dev/ttyUSB0, /dev/tty.usbserial-*)",
            },
            "TIMEOUT": {
                "value": "3",
                "required": False,
                "description": "Read timeout per baud rate in seconds (default: 3)",
            },
            "READ_DURATION": {
                "value": "2",
                "required": False,
                "description": "How long to read data at each baud rate (seconds)",
            },
            "LIST_PORTS": {
                "value": "false",
                "required": False,
                "description": "Set to 'true' to list available serial ports first",
            },
        }

    def run(self):
        """Test common baud rates and identify the correct one."""
        port = self.get_option("PORT")
        timeout = float(self.get_option("TIMEOUT") or 3)
        read_duration = float(self.get_option("READ_DURATION") or 2)
        list_ports = (self.get_option("LIST_PORTS") or "").lower() == "true"

        # List available ports if requested
        if list_ports:
            self._list_ports()

        info(f"Target port: [cyan]{port}[/cyan]")
        info(f"Testing {len(Config.DEFAULT_BAUD_RATES)} baud rates...")
        info(f"Read duration: {read_duration}s per rate | Timeout: {timeout}s")
        console.print()

        try:
            import serial
        except ImportError:
            error("pyserial is not installed. Run: pip install pyserial")
            return

        results_data = []
        best_rate = None
        best_score = 0.0

        for baud in Config.DEFAULT_BAUD_RATES:
            try:
                info(f"Testing baud rate: [bold]{baud}[/bold]...", )

                ser = serial.Serial(
                    port=port,
                    baudrate=baud,
                    timeout=timeout,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                )

                # Flush any stale data
                ser.reset_input_buffer()
                time.sleep(0.1)

                # Read data for the specified duration
                data = b""
                start_time = time.time()
                while time.time() - start_time < read_duration:
                    chunk = ser.read(1024)
                    if chunk:
                        data += chunk
                    else:
                        time.sleep(0.05)

                ser.close()

                if data:
                    readable, ratio = is_readable(data)
                    status = "[green]READABLE[/green]" if readable else "[red]GARBLED[/red]"
                    preview = data[:60].decode("utf-8", errors="replace").replace("\n", "\\n")

                    results_data.append((
                        str(baud),
                        str(len(data)),
                        f"{ratio:.1%}",
                        status,
                        preview[:40],
                    ))

                    if ratio > best_score:
                        best_score = ratio
                        best_rate = baud

                    if readable:
                        result(f"  → {baud}: {len(data)} bytes, {ratio:.1%} readable ✓")
                    else:
                        info(f"  → {baud}: {len(data)} bytes, {ratio:.1%} readable")
                else:
                    results_data.append((
                        str(baud), "0", "N/A", "[dim]NO DATA[/dim]", "-",
                    ))
                    info(f"  → {baud}: No data received")

            except serial.SerialException as e:
                error(f"  → {baud}: Serial error - {e}")
                results_data.append((
                    str(baud), "ERR", "N/A", "[red]ERROR[/red]", str(e)[:40],
                ))
            except Exception as e:
                error(f"  → {baud}: {e}")

        # Display results table
        console.print()
        columns = [
            ("Baud Rate", "cyan"),
            ("Bytes", "white"),
            ("Readable %", "yellow"),
            ("Status", "white"),
            ("Preview", "dim"),
        ]
        print_table("Baud Rate Scan Results", columns, results_data, show_lines=True)

        # Report best match
        if best_rate and best_score > 0.3:
            console.print()
            success(f"[bold]Most likely baud rate: [cyan]{best_rate}[/cyan] "
                    f"(confidence: {best_score:.1%})[/bold]")
            info(f"Connect with: screen {port} {best_rate}")
        elif best_rate:
            warning(f"Best candidate: {best_rate} ({best_score:.1%} readable)")
            warning("Low confidence — device may not be transmitting or wiring may be incorrect")
        else:
            error("Could not determine baud rate — no readable data at any rate")
            info("Tips: Check wiring (TX/RX), ensure device is powered & transmitting")

    def _list_ports(self):
        """List available serial ports."""
        ports = get_available_ports()
        if ports:
            columns = [
                ("Port", "cyan"),
                ("Description", "white"),
                ("Hardware ID", "dim"),
            ]
            rows = [(p["device"], p["description"], p["hwid"]) for p in ports]
            print_table("Available Serial Ports", columns, rows)
        else:
            warning("No serial ports found. Is your adapter connected?")
        console.print()

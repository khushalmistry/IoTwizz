"""
IoTwizz Module: Firmware Analyzer (Binwalk Wrapper)
Analyze firmware images using binwalk for signatures, entropy, and extraction.
"""

import os
import subprocess
import shutil
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console


class BinwalkAnalyzer(BaseModule):
    """Analyze firmware images using binwalk."""

    def __init__(self):
        super().__init__()
        self.name = "Firmware Analyzer (Binwalk)"
        self.description = "Analyze firmware images — signature scan, entropy analysis, extraction"
        self.author = "IoTwizz Team"
        self.category = "firmware"

        self.options = {
            "FIRMWARE_FILE": {
                "value": "",
                "required": True,
                "description": "Path to firmware image file",
            },
            "OUTPUT_DIR": {
                "value": "",
                "required": False,
                "description": "Extraction output directory (default: ./<firmware>_extracted)",
            },
            "EXTRACT": {
                "value": "true",
                "required": False,
                "description": "Extract files from firmware (default: true)",
            },
            "ENTROPY": {
                "value": "true",
                "required": False,
                "description": "Run entropy analysis (default: true)",
            },
            "SIGNATURE": {
                "value": "true",
                "required": False,
                "description": "Run signature scan (default: true)",
            },
            "HEXDUMP": {
                "value": "false",
                "required": False,
                "description": "Show hex dump of first 256 bytes (default: false)",
            },
            "STRINGS_SEARCH": {
                "value": "true",
                "required": False,
                "description": "Search for interesting strings like passwords, keys (default: true)",
            },
        }

    def _check_binwalk(self) -> bool:
        """Check if binwalk is installed."""
        return shutil.which("binwalk") is not None

    def run(self):
        """Analyze firmware using binwalk."""
        firmware_file = self.get_option("FIRMWARE_FILE")
        output_dir = self.get_option("OUTPUT_DIR")
        do_extract = (self.get_option("EXTRACT") or "true").lower() == "true"
        do_entropy = (self.get_option("ENTROPY") or "true").lower() == "true"
        do_signature = (self.get_option("SIGNATURE") or "true").lower() == "true"
        do_hexdump = (self.get_option("HEXDUMP") or "false").lower() == "true"
        do_strings = (self.get_option("STRINGS_SEARCH") or "true").lower() == "true"

        # Validate firmware file
        if not os.path.isfile(firmware_file):
            error(f"Firmware file not found: {firmware_file}")
            return

        file_size = os.path.getsize(firmware_file)
        info(f"Firmware: [cyan]{firmware_file}[/cyan]")
        info(f"File size: [cyan]{self._format_size(file_size)}[/cyan]")
        console.print()

        # Check binwalk
        if not self._check_binwalk():
            error("binwalk is not installed!")
            info("Install it:")
            info("  macOS:  brew install binwalk")
            info("  Debian: sudo apt install binwalk")
            info("  Arch:   sudo pacman -S binwalk")
            console.print()

            # Fall back to basic analysis
            warning("Falling back to basic analysis (no binwalk)...")
            self._basic_analysis(firmware_file)
            return

        # 1. Signature Scan
        if do_signature:
            self._signature_scan(firmware_file)

        # 2. Entropy Analysis
        if do_entropy:
            self._entropy_analysis(firmware_file)

        # 3. Extract
        if do_extract:
            self._extract(firmware_file, output_dir)

        # 4. Hex Dump
        if do_hexdump:
            self._hexdump(firmware_file)

        # 5. String Search
        if do_strings:
            self._strings_search(firmware_file)

        console.print()
        success("Firmware analysis complete!")

    def _signature_scan(self, firmware_file: str):
        """Run binwalk signature scan."""
        info("[bold]Running signature scan...[/bold]")
        console.print()

        try:
            result_data = subprocess.run(
                ["binwalk", firmware_file],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result_data.stdout:
                # Parse binwalk output into table
                lines = result_data.stdout.strip().split("\n")
                console.print("[yellow]── Signature Scan Results ──[/yellow]")
                for line in lines:
                    console.print(f"  [dim]{line}[/dim]")
                console.print("[yellow]── End Results ──[/yellow]")
                console.print()

                # Count findings
                data_lines = [l for l in lines if l.strip() and not l.startswith("-") and not l.startswith("DECIMAL")]
                if data_lines:
                    success(f"Found {len(data_lines)} signatures/components")
                else:
                    warning("No signatures detected")
            else:
                warning("No signatures found in firmware")

        except subprocess.TimeoutExpired:
            error("Signature scan timed out")
        except Exception as e:
            error(f"Signature scan failed: {e}")

    def _entropy_analysis(self, firmware_file: str):
        """Run binwalk entropy analysis."""
        info("[bold]Running entropy analysis...[/bold]")

        try:
            result_data = subprocess.run(
                ["binwalk", "-E", "--nplot", firmware_file],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result_data.stdout:
                lines = result_data.stdout.strip().split("\n")
                console.print("[yellow]── Entropy Analysis ──[/yellow]")
                for line in lines:
                    console.print(f"  [dim]{line}[/dim]")
                console.print("[yellow]── End Analysis ──[/yellow]")
                console.print()

                # Check for high entropy (encrypted/compressed)
                for line in lines:
                    if "Rising" in line or "High" in line:
                        warning("High entropy detected — firmware may contain encrypted or compressed sections")
                        break
            else:
                info("No entropy data generated")

        except subprocess.TimeoutExpired:
            error("Entropy analysis timed out")
        except Exception as e:
            error(f"Entropy analysis failed: {e}")

    def _extract(self, firmware_file: str, output_dir: str = None):
        """Extract firmware contents."""
        if not output_dir:
            base = os.path.splitext(os.path.basename(firmware_file))[0]
            output_dir = os.path.join(os.path.dirname(firmware_file) or ".", f"{base}_extracted")

        info(f"[bold]Extracting firmware to: [cyan]{output_dir}[/cyan][/bold]")

        try:
            result_data = subprocess.run(
                ["binwalk", "-e", "-C", output_dir, firmware_file],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if os.path.isdir(output_dir):
                # Count extracted files
                file_count = sum(len(files) for _, _, files in os.walk(output_dir))
                success(f"Extracted {file_count} files to {output_dir}")

                # List top-level contents
                try:
                    contents = os.listdir(output_dir)
                    if contents:
                        info("Extracted contents:")
                        for item in sorted(contents)[:20]:
                            item_path = os.path.join(output_dir, item)
                            if os.path.isdir(item_path):
                                result(f"  📁 {item}/")
                            else:
                                size = os.path.getsize(item_path)
                                result(f"  📄 {item} ({self._format_size(size)})")
                        if len(contents) > 20:
                            info(f"  ... and {len(contents) - 20} more items")
                except Exception:
                    pass
            else:
                warning("Extraction completed but no files were extracted")

            if result_data.stderr:
                for line in result_data.stderr.strip().split("\n"):
                    if line.strip():
                        warning(f"  {line}")

        except subprocess.TimeoutExpired:
            error("Extraction timed out (>5 minutes)")
        except Exception as e:
            error(f"Extraction failed: {e}")

        console.print()

    def _hexdump(self, firmware_file: str, num_bytes: int = 256):
        """Show hex dump of firmware header."""
        info(f"[bold]Hex dump (first {num_bytes} bytes):[/bold]")

        try:
            with open(firmware_file, "rb") as f:
                data = f.read(num_bytes)

            console.print("[yellow]── Hex Dump ──[/yellow]")
            for i in range(0, len(data), 16):
                hex_part = " ".join(f"{b:02x}" for b in data[i:i+16])
                ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i+16])
                console.print(f"  [dim]{i:08x}[/dim]  {hex_part:<48}  [cyan]{ascii_part}[/cyan]")
            console.print("[yellow]── End Dump ──[/yellow]")
            console.print()

        except Exception as e:
            error(f"Hex dump failed: {e}")

    def _strings_search(self, firmware_file: str):
        """Search firmware for interesting strings."""
        info("[bold]Searching for interesting strings...[/bold]")

        interesting_patterns = [
            "password", "passwd", "secret", "key", "token",
            "api_key", "apikey", "private", "admin",
            "root:", "ssh", "telnet", "http://", "https://",
            "ftp://", "BEGIN RSA", "BEGIN CERTIFICATE",
            "BEGIN EC PRIVATE", "BEGIN DSA",
            "/etc/shadow", "/etc/passwd",
            "busybox", "dropbear", "openssl",
        ]

        try:
            # Use strings command
            result_data = subprocess.run(
                ["strings", firmware_file],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result_data.stdout:
                all_strings = result_data.stdout.split("\n")
                info(f"Total strings found: {len(all_strings)}")

                findings = {}
                for pattern in interesting_patterns:
                    matches = [s.strip() for s in all_strings
                               if pattern.lower() in s.lower() and len(s.strip()) > 3]
                    if matches:
                        findings[pattern] = matches[:5]  # Max 5 matches per pattern

                if findings:
                    console.print()
                    warning("⚠ Interesting strings found:")
                    for pattern, matches in findings.items():
                        result(f"  Pattern: [cyan]{pattern}[/cyan]")
                        for match in matches:
                            console.print(f"    [dim]{match[:80]}[/dim]")
                    console.print()
                else:
                    info("No particularly interesting strings found")
            else:
                info("No strings extracted from firmware")

        except subprocess.TimeoutExpired:
            error("String search timed out")
        except FileNotFoundError:
            warning("'strings' command not found — skipping string search")
        except Exception as e:
            error(f"String search failed: {e}")

    def _basic_analysis(self, firmware_file: str):
        """Basic firmware analysis without binwalk."""
        info("Performing basic analysis...")

        # File type
        try:
            result_data = subprocess.run(
                ["file", firmware_file],
                capture_output=True,
                text=True,
            )
            if result_data.stdout:
                result(f"File type: {result_data.stdout.strip()}")
        except Exception:
            pass

        # Hex dump header
        self._hexdump(firmware_file, 128)

        # String search
        self._strings_search(firmware_file)

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

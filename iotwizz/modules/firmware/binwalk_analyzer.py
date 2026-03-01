"""
IoTwizz Module: Firmware Analyzer
Comprehensive firmware analysis using binwalk, file magic, and entropy analysis.
Extracts filesystems, finds secrets, and identifies vulnerabilities.
"""

import os
import re
import struct
import math
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, print_table, console, print_separator


class BinwalkAnalyzer(BaseModule):
    """Analyze firmware images with comprehensive feature set."""

    # Common firmware signatures for detection
    FIRMWARE_SIGNATURES = {
        b"\x27\x05\x19\x56": "U-Boot legacy image",
        b"\x7fELF": "ELF executable",
        b"\x50\x4b\x03\x04": "ZIP archive",
        b"\x1f\x8b\x08": "GZIP compressed",
        b"\x42\x5a\x68": "BZIP2 compressed",
        b"\xfd\x37\x7a\x58\x5a": "XZ compressed",
        b"\x5d\x00\x00": "LZMA compressed",
        b"\x04\x22\x4d\x18": "LZ4 compressed",
        b"\x28\xb5\x2f\xfd": "ZSTD compressed",
        b"Rar!": "RAR archive",
        b"\x89PNG": "PNG image",
        b"\xff\xd8\xff": "JPEG image",
        b"GIF8": "GIF image",
        b"JFIF": "JPEG image",
        b"hsqs": "SquashFS filesystem",
        b"sqsh": "SquashFS filesystem (big-endian)",
        b"JFFS2": "JFFS2 filesystem",
        b"\x19\x85\x20\x01": "JFFS2 filesystem",
        b"UBI#": "UBI image",
        b"UBI!": "UBI image",
        b"CSYS": "CramFS filesystem",
        b"\x28\xcd\x3d\x45": "zImage (ARM Linux kernel)",
        b"\x00\x00\xa0\xe1": "ARM executable",
        b"CMVP": "VMware disk",
        b"KVM": "KVM disk",
        b"QFI": "QEMU disk",
        b"\x7f\x43\x4b": "CramFS filesystem",
    }

    # Interesting string patterns for secrets
    SECRET_PATTERNS = [
        (r"password\s*[=:]\s*['\"]?([^'\"\s\n]+)", "Password"),
        (r"passwd\s*[=:]\s*['\"]?([^'\"\s\n]+)", "Password"),
        (r"secret\s*[=:]\s*['\"]?([^'\"\s\n]+)", "Secret"),
        (r"api_key\s*[=:]\s*['\"]?([^'\"\s\n]+)", "API Key"),
        (r"apikey\s*[=:]\s*['\"]?([^'\"\s\n]+)", "API Key"),
        (r"token\s*[=:]\s*['\"]?([^'\"\s\n]+)", "Token"),
        (r"private_key\s*[=:]\s*['\"]?([^'\"\s\n]+)", "Private Key"),
        (r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "RSA/EC/DSA Private Key"),
        (r"-----BEGIN CERTIFICATE-----", "Certificate"),
        (r"-----BEGIN OPENSSH PRIVATE KEY-----", "OpenSSH Private Key"),
        (r"ssh-rsa\s+AAAA", "SSH Public Key"),
        (r"aws_access_key_id\s*[=:]\s*['\"]?([A-Z0-9]{20})", "AWS Access Key"),
        (r"aws_secret_access_key\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})", "AWS Secret Key"),
        (r"mysql://[^:]+:[^@]+@", "MySQL Connection String"),
        (r"postgres://[^:]+:[^@]+@", "PostgreSQL Connection String"),
        (r"mongodb://[^:]+:[^@]+@", "MongoDB Connection String"),
        (r"redis://[^:]*:[^@]+@", "Redis Connection String"),
        (r"Authorization:\s*Bearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer Token"),
        (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer Token"),
        (r"[a-f0-9]{32,64}", "Possible Hash/Key"),
        (r"/etc/shadow", "/etc/shadow Reference"),
        (r"/etc/passwd", "/etc/passwd Reference"),
        (r"/root:[^:]*:[0-9]+:[0-9]+:", "Shadow Entry"),
    ]

    def __init__(self):
        super().__init__()
        self.name = "Firmware Analyzer"
        self.description = "Comprehensive firmware analysis — signatures, entropy, extraction, secrets"
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
            "STRINGS_SEARCH": {
                "value": "true",
                "required": False,
                "description": "Search for interesting strings/secrets (default: true)",
            },
            "HEXDUMP": {
                "value": "false",
                "required": False,
                "description": "Show hex dump of first 512 bytes (default: false)",
            },
            "FILE_INFO": {
                "value": "true",
                "required": False,
                "description": "Show detailed file information (default: true)",
            },
            "DEEP_SCAN": {
                "value": "false",
                "required": False,
                "description": "Perform deep scan with recursive extraction (default: false)",
            },
        }

    def _check_binwalk(self) -> bool:
        """Check if binwalk is installed."""
        return shutil.which("binwalk") is not None

    def _check_file_cmd(self) -> bool:
        """Check if file command is installed."""
        return shutil.which("file") is not None

    def run(self):
        """Analyze firmware comprehensively."""
        firmware_file = self.get_option("FIRMWARE_FILE")
        output_dir = self.get_option("OUTPUT_DIR")
        do_extract = (self.get_option("EXTRACT") or "true").lower() == "true"
        do_entropy = (self.get_option("ENTROPY") or "true").lower() == "true"
        do_signature = (self.get_option("SIGNATURE") or "true").lower() == "true"
        do_strings = (self.get_option("STRINGS_SEARCH") or "true").lower() == "true"
        do_hexdump = (self.get_option("HEXDUMP") or "false").lower() == "true"
        do_file_info = (self.get_option("FILE_INFO") or "true").lower() == "true"
        do_deep_scan = (self.get_option("DEEP_SCAN") or "false").lower() == "true"

        # Validate firmware file
        if not os.path.isfile(firmware_file):
            error(f"Firmware file not found: {firmware_file}")
            return

        file_size = os.path.getsize(firmware_file)
        
        console.print()
        info(f"Firmware: [cyan]{os.path.abspath(firmware_file)}[/cyan]")
        info(f"File size: [cyan]{self._format_size(file_size)}[/cyan] ({file_size:,} bytes)")
        console.print()

        # File info
        if do_file_info:
            self._show_file_info(firmware_file)

        # Hex dump
        if do_hexdump:
            self._hexdump(firmware_file, num_bytes=512)

        # Built-in signature scan (always runs for quick detection)
        self._builtin_signature_scan(firmware_file)

        # Check binwalk
        has_binwalk = self._check_binwalk()
        
        if not has_binwalk:
            warning("binwalk is not installed — some features limited")
            info("Install: macOS: brew install binwalk | Debian: sudo apt install binwalk")
            console.print()
            
            # Run basic analysis without binwalk
            if do_entropy:
                self._builtin_entropy_analysis(firmware_file)
            if do_strings:
                self._strings_search(firmware_file)
            if do_extract:
                warning("Extraction requires binwalk")
            return

        # 1. Signature Scan with binwalk
        if do_signature:
            self._binwalk_signature_scan(firmware_file)

        # 2. Entropy Analysis
        if do_entropy:
            self._binwalk_entropy_analysis(firmware_file)

        # 3. Extract
        if do_extract:
            self._extract_firmware(firmware_file, output_dir, do_deep_scan)

        # 4. String/Secret Search
        if do_strings:
            self._strings_search(firmware_file)

        console.print()
        print_separator()
        success("Firmware analysis complete!")

    def _show_file_info(self, firmware_file: str):
        """Show detailed file information."""
        info("[bold]File Information[/bold]")
        
        file_info = {
            "Size": self._format_size(os.path.getsize(firmware_file)),
            "Path": os.path.abspath(firmware_file),
        }
        
        # Use file command if available
        if self._check_file_cmd():
            try:
                result = subprocess.run(
                    ["file", "-b", firmware_file],
                    capture_output=True, text=True, timeout=10
                )
                if result.stdout:
                    file_info["Type"] = result.stdout.strip()
            except Exception:
                pass
        
        # Check file extension
        ext = os.path.splitext(firmware_file)[1].lower()
        if ext:
            file_info["Extension"] = ext
        
        # Read magic bytes
        try:
            with open(firmware_file, "rb") as f:
                magic = f.read(16)
                
            # Detect known signatures
            for sig, name in self.FIRMWARE_SIGNATURES.items():
                if magic.startswith(sig):
                    file_info["Detected Format"] = name
                    break
            
            # Show hex magic
            file_info["Magic Bytes"] = magic[:8].hex().upper()
            
        except Exception:
            pass
        
        # Display
        for key, value in file_info.items():
            result(f"  {key}: [cyan]{value}[/cyan]")
        console.print()

    def _builtin_signature_scan(self, firmware_file: str):
        """Built-in firmware signature detection."""
        info("[bold]Scanning for embedded signatures...[/bold]")
        
        findings = []
        
        try:
            with open(firmware_file, "rb") as f:
                data = f.read()
            
            # Search for signatures in file
            for sig, name in self.FIRMWARE_SIGNATURES.items():
                offset = 0
                while True:
                    offset = data.find(sig, offset)
                    if offset == -1:
                        break
                    findings.append((hex(offset), name, sig[:8].hex()))
                    offset += 1
            
            # Look for common strings
            common_strings = [
                (b"U-Boot", "U-Boot bootloader"),
                (b"Linux-", "Linux kernel"),
                (b"busybox", "BusyBox"),
                (b"OpenWrt", "OpenWrt"),
                (b"DD-WRT", "DD-WRT"),
                (b"Tomato", "Tomato firmware"),
                (b"kernel", "Kernel reference"),
                (b"rootfs", "Root filesystem"),
                (b"squashfs", "SquashFS reference"),
                (b"jffs2", "JFFS2 reference"),
                (b"mtd", "MTD partition"),
            ]
            
            for pattern, name in common_strings:
                offset = 0
                while True:
                    offset = data.find(pattern, offset)
                    if offset == -1:
                        break
                    findings.append((hex(offset), name, pattern.decode('utf-8', errors='replace')[:15]))
                    offset += 1
                    if len(findings) > 100:  # Limit findings
                        break
            
            if findings:
                # Deduplicate and sort by offset
                seen = set()
                unique_findings = []
                for f in findings:
                    if f[0] not in seen:
                        seen.add(f[0])
                        unique_findings.append(f)
                unique_findings.sort(key=lambda x: int(x[0], 16))
                
                columns = [
                    ("Offset", "cyan"),
                    ("Description", "white"),
                    ("Pattern", "dim"),
                ]
                print_table(f"Embedded Signatures ({len(unique_findings)} found)", columns, 
                           unique_findings[:50])  # Limit display
                if len(unique_findings) > 50:
                    info(f"  ... and {len(unique_findings) - 50} more findings")
            else:
                warning("No known signatures detected")
                
        except Exception as e:
            error(f"Signature scan failed: {e}")
        console.print()

    def _builtin_entropy_analysis(self, firmware_file: str, block_size: int = 1024):
        """Built-in entropy calculation without binwalk."""
        info("[bold]Calculating entropy...[/bold]")
        
        try:
            with open(firmware_file, "rb") as f:
                data = f.read()
            
            entropy_values = []
            num_blocks = len(data) // block_size
            
            for i in range(num_blocks):
                block = data[i * block_size:(i + 1) * block_size]
                entropy = self._calculate_entropy(block)
                entropy_values.append(entropy)
            
            if entropy_values:
                avg_entropy = sum(entropy_values) / len(entropy_values)
                min_entropy = min(entropy_values)
                max_entropy = max(entropy_values)
                
                result(f"  Average entropy: [cyan]{avg_entropy:.4f}[/cyan] bits/byte (max: 8.0)")
                result(f"  Min entropy: [cyan]{min_entropy:.4f}[/cyan]")
                result(f"  Max entropy: [cyan]{max_entropy:.4f}[/cyan]")
                
                # Interpret results
                if avg_entropy > 7.5:
                    warning("  High entropy detected — firmware may be encrypted or compressed")
                elif avg_entropy < 4.0:
                    success("  Low entropy — firmware likely contains plain text/data")
                else:
                    info("  Mixed entropy — firmware contains varied content")
                
                # Show entropy histogram
                console.print()
                self._show_entropy_histogram(entropy_values)
                
        except Exception as e:
            error(f"Entropy analysis failed: {e}")
        console.print()

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0.0
        
        # Count byte frequencies
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        for count in freq.values():
            p = count / len(data)
            entropy -= p * math.log2(p)
        
        return entropy

    def _show_entropy_histogram(self, values: List[float], width: int = 50):
        """Display a simple ASCII entropy histogram."""
        if not values:
            return
        
        info("Entropy distribution:")
        console.print()
        
        # Create histogram with 10 bins
        bins = 10
        bin_counts = [0] * bins
        
        for v in values:
            bin_idx = min(int(v / 8.0 * bins), bins - 1)
            bin_counts[bin_idx] += 1
        
        max_count = max(bin_counts) if bin_counts else 1
        
        labels = ["0.0-0.8", "0.8-1.6", "1.6-2.4", "2.4-3.2", "3.2-4.0",
                  "4.0-4.8", "4.8-5.6", "5.6-6.4", "6.4-7.2", "7.2-8.0"]
        
        for i, (label, count) in enumerate(zip(labels, bin_counts)):
            bar_len = int(count / max_count * width) if max_count > 0 else 0
            bar = "█" * bar_len
            entropy_level = i / bins * 8
            
            # Color based on entropy level
            if entropy_level < 3:
                color = "green"
            elif entropy_level < 5:
                color = "yellow"
            else:
                color = "red"
            
            console.print(f"  [{color}]{label}[/{color}] │ {bar} {count}")
        
        console.print()
        info("  Low entropy = plain text/data | High entropy = encrypted/compressed")

    def _binwalk_signature_scan(self, firmware_file: str):
        """Run binwalk signature scan."""
        info("[bold]Running binwalk signature scan...[/bold]")
        
        try:
            result = subprocess.run(
                ["binwalk", firmware_file],
                capture_output=True, text=True, timeout=300
            )
            
            output = result.stdout + result.stderr
            
            if output:
                # Parse and display results
                lines = output.strip().split("\n")
                findings = []
                
                for line in lines:
                    if line.strip() and not line.startswith("-") and not line.startswith("DECIMAL"):
                        parts = line.split(None, 3)
                        if len(parts) >= 2:
                            offset = parts[0]
                            desc = " ".join(parts[2:]) if len(parts) > 2 else parts[1]
                            findings.append((offset, desc[:60]))
                
                if findings:
                    columns = [("Offset", "cyan"), ("Description", "white")]
                    print_table(f"Binwalk Signatures ({len(findings)} found)", columns, findings[:50])
                else:
                    warning("No signatures found by binwalk")
            else:
                warning("No output from binwalk")
                
        except subprocess.TimeoutExpired:
            error("Binwalk signature scan timed out")
        except Exception as e:
            error(f"Binwalk scan failed: {e}")
        console.print()

    def _binwalk_entropy_analysis(self, firmware_file: str):
        """Run binwalk entropy analysis."""
        info("[bold]Running binwalk entropy analysis...[/bold]")
        
        try:
            result = subprocess.run(
                ["binwalk", "-E", "--nplot", firmware_file],
                capture_output=True, text=True, timeout=300
            )
            
            output = result.stdout + result.stderr
            if output:
                for line in output.split("\n"):
                    if line.strip():
                        console.print(f"  [dim]{line}[/dim]")
            else:
                info("Entropy analysis completed")
                
        except subprocess.TimeoutExpired:
            error("Entropy analysis timed out")
        except Exception as e:
            error(f"Entropy analysis failed: {e}")
        console.print()

    def _extract_firmware(self, firmware_file: str, output_dir: str, deep: bool = False):
        """Extract firmware contents."""
        if not output_dir:
            base = os.path.splitext(os.path.basename(firmware_file))[0]
            output_dir = os.path.join(os.path.dirname(firmware_file) or ".", f"{base}_extracted")
        
        info(f"[bold]Extracting firmware to: [cyan]{output_dir}[/cyan][/bold]")
        
        cmd = ["binwalk", "-e", "-C", output_dir]
        if deep:
            cmd.append("-M")  # Matryoshka (recursive)
        
        cmd.append(firmware_file)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=600
            )
            
            if os.path.isdir(output_dir):
                # Count extracted files
                file_count = 0
                dir_count = 0
                total_size = 0
                
                for root, dirs, files in os.walk(output_dir):
                    dir_count += len(dirs)
                    file_count += len(files)
                    for f in files:
                        total_size += os.path.getsize(os.path.join(root, f))
                
                success(f"Extracted {file_count} files, {dir_count} directories ({self._format_size(total_size)})")
                
                # List top-level contents
                try:
                    contents = sorted(os.listdir(output_dir))[:20]
                    if contents:
                        info("Extracted contents:")
                        for item in contents:
                            item_path = os.path.join(output_dir, item)
                            if os.path.isdir(item_path):
                                result(f"  📁 {item}/")
                            else:
                                size = os.path.getsize(item_path)
                                result(f"  📄 {item} ({self._format_size(size)})")
                        
                        if len(os.listdir(output_dir)) > 20:
                            info(f"  ... and {len(os.listdir(output_dir)) - 20} more items")
                except Exception:
                    pass
            else:
                warning("Extraction completed but no output directory created")
                
        except subprocess.TimeoutExpired:
            error("Extraction timed out (>10 minutes)")
        except Exception as e:
            error(f"Extraction failed: {e}")
        console.print()

    def _strings_search(self, firmware_file: str):
        """Search firmware for interesting strings and secrets."""
        info("[bold]Searching for interesting strings and secrets...[/bold]")
        
        all_findings = {}
        
        try:
            # Use strings command
            result = subprocess.run(
                ["strings", "-n", "8", firmware_file],
                capture_output=True, text=True, timeout=120
            )
            
            if result.stdout:
                string_output = result.stdout
                
                # Search for each pattern
                for pattern, name in self.SECRET_PATTERNS:
                    matches = re.findall(pattern, string_output, re.IGNORECASE)
                    if matches:
                        # Deduplicate and limit
                        unique_matches = list(set(str(m) for m in matches))[:5]
                        all_findings[name] = unique_matches
                
                # Count total strings
                total_strings = len(string_output.split("\n"))
                info(f"Analyzed {total_strings:,} strings")
                
                if all_findings:
                    console.print()
                    warning("⚠ Potential secrets/sensitive data found:")
                    
                    for name, matches in all_findings.items():
                        console.print(f"\n  [bold yellow]{name}:[/bold yellow]")
                        for match in matches:
                            # Truncate long matches
                            display = match[:80] + "..." if len(match) > 80 else match
                            result(f"    • {display}")
                    
                    console.print()
                    warning("⚠ Review these findings and ensure sensitive data is removed!")
                else:
                    success("No obvious secrets found in strings")
            else:
                info("No strings extracted")
                
        except FileNotFoundError:
            warning("'strings' command not found — skipping string search")
        except subprocess.TimeoutExpired:
            error("String search timed out")
        except Exception as e:
            error(f"String search failed: {e}")
        console.print()

    def _hexdump(self, firmware_file: str, num_bytes: int = 512):
        """Show hex dump of firmware header."""
        info(f"[bold]Hex dump (first {num_bytes} bytes):[/bold]")
        console.print()
        
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

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

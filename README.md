# 🔧 IoTwizz — The Hardware Hacker's Playbook

<p align="center">
  <strong>A modular IoT security testing framework inspired by Metasploit.</strong><br>
  Built for hardware hackers, firmware analysts, and IoT security researchers.
</p>

## 📖 About IoTwizz

**IoTwizz** is a comprehensive, open-source penetration testing framework specifically engineered for the Internet of Things (IoT) landscape. Inspired by the modular and extensible architecture of Metasploit, IoTwizz serves as a "Swiss Army Knife" for security researchers, hardware hackers, and penetration testers who need a unified toolkit to audit embedded devices, analyze firmware, and test hardware-level protocols.

As the IoT ecosystem expands, the attack surface grows exponentially—from exposed UART and JTAG debug interfaces on circuit boards to hardcoded credentials and vulnerable bootloaders. IoTwizz bridges the gap between hardware and software exploitation by providing an interactive, centralized console (powered by `prompt-toolkit` and `rich`) to manage complex security assessments. Out of the box, the framework includes a suite of powerful core modules: a **Baud Rate Finder** to seamlessly auto-detect UART serial communication speeds, a **U-Boot Breaker** designed to interrupt bootloader sequences and acquire low-level hardware root shells, a universal **Default Credential Checker** loaded with hundreds of known IoT default logins to test against SSH, Telnet, HTTP, and FTP, and a **Firmware Analyzer** that leverages Binwalk for signature scanning and entropy analysis.

Moreover, IoTwizz introduces **AiWizz** — a cutting-edge interactive hacking assistant powered by Large Language Models (supporting Gemini, OpenAI, Claude, and Ollama). This AI agent acts as your copilot, integrating directly into the console to accept natural language commands. AiWizz can autonomously select, configure, and execute internal IoTwizz modules on your behalf, subsequently parsing the tool output to provide actionable intelligence, vulnerability explanations, and step-by-step remediation advice.

Designed with a highly robust and dynamic plugin architecture, developers and researchers can easily write and drop new Python modules into the framework to support specialized attack vectors like JTAG/SWD scanning, SPI flash dumping, Bluetooth Low Energy (BLE) sniffing, and MQTT/CoAP protocol fuzzing. Whether you are reverse-engineering a rogue smart camera, assessing a fleet of enterprise routers, or securing an industrial control system, IoTwizz delivers the automation, flexibility, and AI-driven intelligence required to uncover critical vulnerabilities at the edge.


---

## ⚡ Features

| Category | Module | Status | Description |
|----------|--------|--------|-------------|
| **UART** | `uart/baud_rate_finder` | ✅ Ready | Auto-detect UART baud rates |
| **Exploit** | `exploit/uboot_breaker` | ✅ Ready | Intercept U-Boot & gain shell |
| **Recon** | `recon/default_creds` | ✅ Ready | Test IoT default credentials (SSH/Telnet/HTTP/FTP) |
| **Firmware** | `firmware/binwalk_analyzer` | ✅ Ready | Firmware analysis, extraction & string search |
| **AI** | `ai/aiwizz` | ✅ Ready | Interactive AI hacking assistant (Gemini/OpenAI/Claude/Ollama) |
| **Hardware** | `hardware/jtag_swd_scanner` | ✅ Ready | JTAG/SWD debug interface scanner |
| **Hardware** | `hardware/spi_flash_dumper` | ✅ Ready | SPI flash firmware dumper |
| **Protocol** | `protocol/mqtt_fuzzer` | ✅ Ready | MQTT protocol fuzzer |
| **Protocol** | `protocol/coap_fuzzer` | ✅ Ready | CoAP protocol fuzzer |
| **Wireless** | `wireless/ble_scanner` | ✅ Ready | Bluetooth Low Energy scanner |
| **Wireless** | `wireless/zigbee_sniffer` | ✅ Ready | Zigbee/Z-Wave sniffer |

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/khushalmistry/iotwizz.git
cd iotwizz

# Install dependencies
pip install -r requirements.txt

# Install IoTwizz
pip install -e .

# Launch!
iotwizz
```

### Usage

```
iotwizz > show modules          # List all modules
iotwizz > use uart/baud_rate_finder   # Select a module
iotwizz(uart/baud_rate_finder) > info         # View module info
iotwizz(uart/baud_rate_finder) > set PORT /dev/ttyUSB0  # Set options
iotwizz(uart/baud_rate_finder) > run          # Execute!
```

---

## 📖 Module Quick Reference

### 🔌 UART Baud Rate Finder
Automatically detects the baud rate of a UART serial connection by testing common rates.

```
iotwizz > use uart/baud_rate_finder
iotwizz(uart/baud_rate_finder) > set PORT /dev/ttyUSB0
iotwizz(uart/baud_rate_finder) > set LIST_PORTS true
iotwizz(uart/baud_rate_finder) > run
```

### 🔓 U-Boot Breaker
Intercepts U-Boot boot sequence to gain bootloader shell access.

```
iotwizz > use exploit/uboot_breaker
iotwizz(exploit/uboot_breaker) > set PORT /dev/ttyUSB0
iotwizz(exploit/uboot_breaker) > set BAUD_RATE 115200
iotwizz(exploit/uboot_breaker) > run
# Power cycle the device when prompted!
```

### 🔑 Default Credential Checker
Tests IoT devices for default/known credentials over SSH, Telnet, HTTP, or FTP.

```
iotwizz > use recon/default_creds
iotwizz(recon/default_creds) > set TARGET 192.168.1.1
iotwizz(recon/default_creds) > set SERVICE ssh
iotwizz(recon/default_creds) > run
```

### 📦 Firmware Analyzer
Analyzes firmware images using binwalk — signature scan, entropy, extraction, and string search.

```
iotwizz > use firmware/binwalk_analyzer
iotwizz(firmware/binwalk_analyzer) > set FIRMWARE_FILE ./router_firmware.bin
iotwizz(firmware/binwalk_analyzer) > set EXTRACT true
iotwizz(firmware/binwalk_analyzer) > run
```

### 🤖 AiWizz (Interactive Hacking Assistant)
Talk to an AI expert that can autonomously control the IoTwizz framework, run modules, and analyze output for you.

```
iotwizz > use ai/aiwizz
iotwizz(ai/aiwizz) > set PROVIDER gemini
iotwizz(ai/aiwizz) > set API_KEY your_api_key_here
iotwizz(ai/aiwizz) > run
AiWizz > "I want you to scan 192.168.1.1 for default SSH credentials"
```

---

## 🏗️ Creating Custom Modules

IoTwizz has a plugin architecture. To add a new module:

1. Create a new `.py` file in the appropriate `iotwizz/modules/<category>/` directory
2. Inherit from `BaseModule` (or `StubModule` for placeholders)
3. Define `name`, `description`, `author`, `category`, `options`
4. Implement the `run()` method
5. IoTwizz will auto-discover your module!

```python
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, info

class MyCustomModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "My Custom Tool"
        self.description = "Does something awesome"
        self.author = "Your Name"
        self.category = "recon"
        self.options = {
            "TARGET": {
                "value": "",
                "required": True,
                "description": "Target to scan",
            },
        }

    def run(self):
        target = self.get_option("TARGET")
        info(f"Scanning {target}...")
        # Your exploit/scan logic here
        success("Done!")
```

---

## 📋 Requirements

- Python 3.8+
- `pyserial` — Serial/UART communication
- `rich` — Beautiful terminal output
- `prompt-toolkit` — Interactive console
- `paramiko` — SSH connections
- `requests` — HTTP requests
- `scapy` — Network packet crafting
- `paho-mqtt` — MQTT protocol
- `google-generativeai`, `openai`, `anthropic` — For AiWizz mode

Optional:
- `binwalk` — Firmware analysis (system package)

---

## ⚠️ Legal Disclaimer

**IoTwizz is intended for authorized security testing only.** Only use this tool on devices and networks you own or have explicit written permission to test. Unauthorized access to computer systems is illegal. The authors are not responsible for any misuse.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-module`)
3. Add your module to `iotwizz/modules/<category>/`
4. Test thoroughly
5. Submit a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>⚡ Built by <a href="https://github.com/khushalmistry">Khushal Mistry</a> ⚡</strong><br>
  <em>Happy Hacking! 💀</em>
</p>

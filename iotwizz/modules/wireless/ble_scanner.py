"""
IoTwizz Module: BLE Scanner [STUB]
Scan and enumerate Bluetooth Low Energy (BLE) devices.
"""

from iotwizz.base_module import StubModule


class BleScanner(StubModule):
    """Scan and enumerate BLE devices. [Coming Soon]"""

    def __init__(self):
        super().__init__()
        self.name = "BLE Scanner"
        self.description = "Scan and enumerate Bluetooth Low Energy (BLE) devices [Coming Soon]"
        self.author = "IoTwizz Team"
        self.category = "wireless"

        self.options = {
            "INTERFACE": {
                "value": "hci0",
                "required": False,
                "description": "Bluetooth adapter interface (default: hci0)",
            },
            "SCAN_DURATION": {
                "value": "10",
                "required": False,
                "description": "Scan duration in seconds (default: 10)",
            },
            "TARGET_MAC": {
                "value": "",
                "required": False,
                "description": "Specific MAC to probe (scans all if empty)",
            },
            "ENUM_SERVICES": {
                "value": "true",
                "required": False,
                "description": "Enumerate GATT services on found devices (default: true)",
            },
        }

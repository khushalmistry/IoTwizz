"""
IoTwizz Module: JTAG/SWD Scanner [STUB]
Detect and enumerate JTAG/SWD debug interfaces on IoT devices.
"""

from iotwizz.base_module import StubModule


class JtagSwdScanner(StubModule):
    """Detect JTAG/SWD debug interfaces. [Coming Soon]"""

    def __init__(self):
        super().__init__()
        self.name = "JTAG/SWD Scanner"
        self.description = "Detect and enumerate JTAG/SWD debug interfaces [Coming Soon]"
        self.author = "IoTwizz Team"
        self.category = "hardware"

        self.options = {
            "ADAPTER": {
                "value": "",
                "required": True,
                "description": "Debug adapter type (jlink, stlink, ftdi, buspirate)",
            },
            "INTERFACE": {
                "value": "jtag",
                "required": False,
                "description": "Interface type: jtag or swd (default: jtag)",
            },
            "SPEED": {
                "value": "1000",
                "required": False,
                "description": "Clock speed in KHz (default: 1000)",
            },
        }

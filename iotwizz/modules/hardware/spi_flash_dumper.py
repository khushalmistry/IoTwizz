"""
IoTwizz Module: SPI Flash Dumper [STUB]
Read and dump firmware from SPI flash chips.
"""

from iotwizz.base_module import StubModule


class SpiFlashDumper(StubModule):
    """Dump firmware from SPI flash chips. [Coming Soon]"""

    def __init__(self):
        super().__init__()
        self.name = "SPI Flash Dumper"
        self.description = "Read and dump firmware from SPI flash chips [Coming Soon]"
        self.author = "IoTwizz Team"
        self.category = "hardware"

        self.options = {
            "ADAPTER": {
                "value": "",
                "required": True,
                "description": "Hardware adapter (buspirate, ftdi, ch341a, flashrom)",
            },
            "CHIP": {
                "value": "",
                "required": False,
                "description": "SPI flash chip model (auto-detect if empty)",
            },
            "OUTPUT_FILE": {
                "value": "firmware_dump.bin",
                "required": True,
                "description": "Output file for dumped firmware",
            },
            "VERIFY": {
                "value": "true",
                "required": False,
                "description": "Verify dump by reading twice (default: true)",
            },
        }

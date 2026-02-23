"""
IoTwizz Module: Zigbee/Z-Wave Sniffer [STUB]
Sniff and analyze Zigbee and Z-Wave wireless communications.
"""

from iotwizz.base_module import StubModule


class ZigbeeSniffer(StubModule):
    """Sniff Zigbee/Z-Wave packets. [Coming Soon]"""

    def __init__(self):
        super().__init__()
        self.name = "Zigbee/Z-Wave Sniffer"
        self.description = "Sniff and analyze Zigbee/Z-Wave wireless communications [Coming Soon]"
        self.author = "IoTwizz Team"
        self.category = "wireless"

        self.options = {
            "ADAPTER": {
                "value": "",
                "required": True,
                "description": "Sniffer adapter (cc2531, hackrf, yard-stick-one)",
            },
            "CHANNEL": {
                "value": "11",
                "required": False,
                "description": "Zigbee channel to sniff (11-26, default: 11)",
            },
            "PROTOCOL": {
                "value": "zigbee",
                "required": False,
                "description": "Protocol: zigbee or zwave (default: zigbee)",
            },
            "OUTPUT_PCAP": {
                "value": "",
                "required": False,
                "description": "Save capture to PCAP file",
            },
            "DURATION": {
                "value": "60",
                "required": False,
                "description": "Capture duration in seconds (default: 60)",
            },
        }

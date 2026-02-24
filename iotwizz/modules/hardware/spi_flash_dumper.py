"""
IoTwizz Module: SPI Flash Dumper
Extract firmware directly from flash chips using flashrom.
"""
import subprocess
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info

class SpiFlashDumper(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "SPI Flash Dumper"
        self.description = "Read and dump firmware from physical SPI flash chips using flashrom"
        self.author = "IoTwizz Team"
        self.category = "hardware"
        
        self.options = {
            "PROGRAMMER": {
                "value": "ch341a_spi",
                "required": True,
                "description": "Programmer type (e.g., ch341a_spi, ft2232_spi:type=232H)",
            },
            "OUTPUT_FILE": {
                "value": "firmware_dump.bin",
                "required": True,
                "description": "Output file path to save the dumped firmware",
            }
        }
        
    def run(self):
        programmer = self.get_option("PROGRAMMER")
        output_file = self.get_option("OUTPUT_FILE")
        
        info(f"Initializing flashrom with programmer: {programmer}...")
        
        try:
            # First, try to identify the chip
            probe_cmd = ["flashrom", "-p", programmer]
            info("Probing for flash chip...")
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            output = probe_result.stdout + probe_result.stderr
            
            chip_found = False
            for line in output.split("\n"):
                if "Found" in line and "flash chip" in line:
                    success(line.strip())
                    chip_found = True
                    break
                    
            if not chip_found:
                error("No supported flash chip found or programmer not connected.")
                info("Ensure the clip is properly seated and the chip is supported.")
                return
                
            # If chip found, attempt to read
            info(f"Attempting to read firmware to {output_file} (This may take a while)...")
            read_cmd = ["flashrom", "-p", programmer, "-r", output_file]
            
            read_result = subprocess.run(read_cmd, capture_output=True, text=True) # Let it run as long as needed
            read_output = read_result.stdout + read_result.stderr
            
            if "Reading flash... done" in read_output:
                success(f"Firmware successfully dumped to {output_file}")
            else:
                error("Failed to dump firmware.")
                print(read_output)
                
        except subprocess.TimeoutExpired:
            error("Probing timed out.")
        except FileNotFoundError:
            error("flashrom command not found. Please install flashrom.")

"""
IoTwizz - Base Module Class
All IoTwizz modules inherit from this base class.
"""

from abc import ABC, abstractmethod
import copy


class BaseModule(ABC):
    """Abstract base class for all IoTwizz modules.

    Every module must define:
        - name: Human-readable module name
        - description: What the module does
        - author: Module author
        - category: Module category path (e.g., 'uart', 'exploit', 'recon')
        - options: Dict of configurable options
        - run(): Main execution method
    """

    def __init__(self):
        self.name = "Unnamed Module"
        self.description = "No description"
        self.author = "IoTwizz Team"
        self.category = "misc"
        self.options = {}
        self._is_stub = False

    def get_option(self, name: str):
        """Get the value of an option as string."""
        name_upper = name.upper()
        if name_upper in self.options:
            val = self.options[name_upper].get("value")
            return val if val is not None else ""
        return ""

    def get_option_int(self, name: str, default: int = 0) -> int:
        """Safely get an option as an integer, swallowing ValueErrors."""
        val = self.get_option(name)
        try:
            return int(val)
        except (ValueError, TypeError):
            from iotwizz.utils.colors import warning
            warning(f"Invalid integer for {name}: '{val}'. Using default {default}.")
            return default

    def get_option_float(self, name: str, default: float = 0.0) -> float:
        """Safely get an option as a float, swallowing ValueErrors."""
        val = self.get_option(name)
        try:
            return float(val)
        except (ValueError, TypeError):
            from iotwizz.utils.colors import warning
            warning(f"Invalid float for {name}: '{val}'. Using default {default}.")
            return default

    def set_option(self, name: str, value: str) -> bool:
        """Set the value of an option.

        Args:
            name: Option name (case-insensitive)
            value: Value to set

        Returns:
            True if option was set successfully
        """
        name_upper = name.upper()
        if name_upper in self.options:
            self.options[name_upper]["value"] = value
            return True
        return False

    def validate(self) -> list:
        """Validate that all required options are set.

        Returns:
            List of missing required option names
        """
        missing = []
        for name, opt in self.options.items():
            if opt.get("required", False) and not opt.get("value"):
                missing.append(name)
        return missing

    def get_module_path(self) -> str:
        """Get the full module path (category/name format)."""
        module_name = self.__class__.__module__.split(".")[-1]
        return f"{self.category}/{module_name}"

    def reset_options(self):
        """Reset all options to their default values."""
        for name, opt in self.options.items():
            opt["value"] = opt.get("default", "")

    @abstractmethod
    def run(self):
        """Execute the module. Must be implemented by subclasses."""
        pass

    def __repr__(self):
        return f"<Module: {self.name} ({self.category})>"


class StubModule(BaseModule):
    """Base class for stub/placeholder modules (coming soon)."""

    def __init__(self):
        super().__init__()
        self._is_stub = True

    def run(self):
        from iotwizz.utils.colors import print_coming_soon
        print_coming_soon(self.name)

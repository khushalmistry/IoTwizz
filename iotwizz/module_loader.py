"""
IoTwizz - Dynamic Module Loader
Discovers and loads all modules from the modules directory.
"""

import os
import importlib
import inspect
from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import info, error, warning


class ModuleLoader:
    """Dynamically discovers and loads IoTwizz modules."""

    def __init__(self, modules_dir: str = None):
        if modules_dir is None:
            modules_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "modules"
            )
        self.modules_dir = modules_dir
        self.modules = {}  # path -> module instance
        self._load_all()

    def _load_all(self):
        """Discover and load all modules from the modules directory."""
        for category in os.listdir(self.modules_dir):
            category_path = os.path.join(self.modules_dir, category)
            if not os.path.isdir(category_path) or category.startswith("_"):
                continue

            for filename in os.listdir(category_path):
                if filename.startswith("_") or not filename.endswith(".py"):
                    continue

                module_name = filename[:-3]  # strip .py
                module_path = f"{category}/{module_name}"

                try:
                    # Import the Python module
                    py_module = importlib.import_module(
                        f"iotwizz.modules.{category}.{module_name}"
                    )

                    # Find the BaseModule subclass in the module
                    for attr_name in dir(py_module):
                        attr = getattr(py_module, attr_name)
                        if (
                            inspect.isclass(attr)
                            and issubclass(attr, BaseModule)
                            and attr is not BaseModule
                            and not attr.__name__ == "StubModule"
                        ):
                            instance = attr()
                            self.modules[module_path] = instance
                            break

                except Exception as e:
                    warning(f"Failed to load module {module_path}: {e}")

    def get_module(self, path: str):
        """Get a module instance by its path.

        Args:
            path: Module path (e.g., 'uart/baud_rate_finder')

        Returns:
            Module instance, or None
        """
        return self.modules.get(path)

    def get_all_modules(self) -> dict:
        """Get all loaded modules.

        Returns:
            Dict of {path: module_instance}
        """
        return self.modules

    def search_modules(self, query: str) -> dict:
        """Search modules by name, description, or category.

        Args:
            query: Search term

        Returns:
            Dict of matching {path: module_instance}
        """
        query_lower = query.lower()
        results = {}
        for path, module in self.modules.items():
            if (
                query_lower in path.lower()
                or query_lower in module.name.lower()
                or query_lower in module.description.lower()
                or query_lower in module.category.lower()
            ):
                results[path] = module
        return results

    def get_categories(self) -> list:
        """Get a sorted list of unique module categories."""
        categories = set()
        for module in self.modules.values():
            categories.add(module.category)
        return sorted(categories)

    @property
    def count(self) -> int:
        """Number of loaded modules."""
        return len(self.modules)

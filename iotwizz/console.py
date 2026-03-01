"""
IoTwizz - Interactive Console
Metasploit-style interactive shell for IoT pentesting.
"""

import os
import sys
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import ANSI

from iotwizz import __version__, __author__, __banner__
from iotwizz.module_loader import ModuleLoader
from iotwizz.utils.colors import (
    console,
    success,
    error,
    warning,
    info,
    print_table,
    print_module_info,
    print_options,
    print_separator,
)


class IoTwizzConsole:
    """Interactive console for IoTwizz framework."""

    def __init__(self):
        self.loader = ModuleLoader()
        self.current_module = None
        self.current_module_path = None
        self.session = PromptSession(
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
        )

        # Command handlers
        self.commands = {
            "help": self.cmd_help,
            "?": self.cmd_help,
            "show": self.cmd_show,
            "use": self.cmd_use,
            "info": self.cmd_info,
            "set": self.cmd_set,
            "unset": self.cmd_unset,
            "options": self.cmd_options,
            "run": self.cmd_run,
            "exploit": self.cmd_run,
            "back": self.cmd_back,
            "search": self.cmd_search,
            "banner": self.cmd_banner,
            "clear": self.cmd_clear,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "modules": self.cmd_modules,
        }

    def display_banner(self):
        """Display the IoTwizz ASCII banner."""
        banner = __banner__.format(
            version=__version__,
            author=__author__,
            modules=self.loader.count,
        )
        print(banner)

    def get_prompt(self):
        """Generate the prompt string based on current state."""
        if self.current_module_path:
            prompt_str = f"\033[38;5;196miotwizz\033[0m(\033[38;5;51m{self.current_module_path}\033[0m) > "
        else:
            prompt_str = "\033[38;5;196miotwizz\033[0m > "
        return ANSI(prompt_str)

    def start(self):
        """Start the interactive console."""
        self.display_banner()

        while True:
            try:
                user_input = self.session.prompt(self.get_prompt()).strip()
                if not user_input:
                    continue

                self.process_command(user_input)

            except KeyboardInterrupt:
                console.print()
                warning("Use 'exit' or 'quit' to leave IoTwizz")
            except EOFError:
                self.cmd_exit([])
            except Exception as e:
                error(f"Unexpected error: {e}")

    def process_command(self, user_input: str):
        """Parse and execute a command."""
        try:
            parts = shlex.split(user_input)
        except ValueError:
            parts = user_input.split()

        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            error(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

    # ─── Command Handlers ────────────────────────────────────────────

    def cmd_help(self, args):
        """Show available commands."""
        columns = [
            ("Command", "cyan"),
            ("Description", "white"),
        ]
        rows = [
            ("help / ?", "Show this help menu"),
            ("show modules", "List all available modules"),
            ("show categories", "List module categories"),
            ("use <module>", "Select a module to configure & run"),
            ("info", "Show info about the selected module"),
            ("set <option> <value>", "Set a module option"),
            ("unset <option>", "Clear a module option"),
            ("options", "Show current module options"),
            ("run / exploit", "Execute the selected module"),
            ("back", "Deselect the current module"),
            ("search <term>", "Search modules by name/description"),
            ("modules", "Quick list of all modules"),
            ("banner", "Display the banner"),
            ("clear", "Clear the screen"),
            ("exit / quit", "Exit IoTwizz"),
        ]
        print_table("IoTwizz Commands", columns, rows)

    def cmd_show(self, args):
        """Handle 'show' subcommands."""
        if not args:
            error("Usage: show <modules|categories>")
            return

        subcmd = args[0].lower()
        if subcmd == "modules":
            self._show_modules()
        elif subcmd == "categories":
            self._show_categories()
        elif subcmd == "options":
            self.cmd_options([])
        else:
            error(f"Unknown show option: '{subcmd}'. Try: modules, categories, options")

    def _show_modules(self):
        """List all available modules."""
        modules = self.loader.get_all_modules()
        if not modules:
            warning("No modules loaded")
            return

        columns = [
            ("#", "dim"),
            ("Module", "cyan"),
            ("Name", "white"),
            ("Description", "dim white"),
            ("Status", "green"),
        ]
        rows = []
        for idx, (path, module) in enumerate(sorted(modules.items()), 1):
            status = "🚧 Stub" if module._is_stub else "✅ Ready"
            rows.append((str(idx), path, module.name, module.description, status))

        print_table(f"Available Modules ({len(modules)})", columns, rows, show_lines=True)

    def _show_categories(self):
        """List module categories."""
        categories = self.loader.get_categories()
        columns = [("Category", "cyan"), ("Module Count", "white")]
        rows = []
        for cat in categories:
            count = sum(
                1 for m in self.loader.modules.values() if m.category == cat
            )
            rows.append((cat, str(count)))
        print_table("Module Categories", columns, rows)

    def cmd_use(self, args):
        """Select a module."""
        if not args:
            error("Usage: use <module_path>")
            info("Example: use uart/baud_rate_finder")
            return

        module_path = args[0]
        module = self.loader.get_module(module_path)

        if module is None:
            # Try partial match
            matches = self.loader.search_modules(module_path)
            if len(matches) == 1:
                module_path, module = list(matches.items())[0]
            elif len(matches) > 1:
                warning(f"Ambiguous module name. Did you mean one of these?")
                for path in matches:
                    info(f"  {path}")
                return
            else:
                error(f"Module not found: '{module_path}'")
                info("Use 'show modules' to see available modules")
                return

        self.current_module = module
        self.current_module_path = module_path
        info(f"Using module: {module.name}")

        if module._is_stub:
            warning("This module is a stub (coming soon). It cannot be run yet.")

    def cmd_info(self, args):
        """Show module information."""
        if self.current_module is None:
            error("No module selected. Use 'use <module>' first.")
            return

        print_module_info(self.current_module)

        if self.current_module.options:
            print_options(self.current_module.options)

    def cmd_set(self, args):
        """Set a module option value."""
        if self.current_module is None:
            error("No module selected. Use 'use <module>' first.")
            return

        if len(args) < 2:
            error("Usage: set <option> <value>")
            return

        option_name = args[0].upper()
        value = " ".join(args[1:])

        if self.current_module.set_option(option_name, value):
            success(f"{option_name} => {value}")
        else:
            error(f"Unknown option: '{option_name}'")
            info("Use 'options' to see available options")

    def cmd_unset(self, args):
        """Clear a module option value."""
        if self.current_module is None:
            error("No module selected. Use 'use <module>' first.")
            return

        if not args:
            error("Usage: unset <option>")
            return

        option_name = args[0].upper()
        if self.current_module.set_option(option_name, ""):
            success(f"{option_name} => (cleared)")
        else:
            error(f"Unknown option: '{option_name}'")

    def cmd_options(self, args):
        """Show current module options."""
        if self.current_module is None:
            error("No module selected. Use 'use <module>' first.")
            return

        if not self.current_module.options:
            info("This module has no configurable options.")
            return

        print_options(self.current_module.options)

    def cmd_run(self, args):
        """Execute the selected module."""
        if self.current_module is None:
            error("No module selected. Use 'use <module>' first.")
            return

        # Validate required options
        missing = self.current_module.validate()
        if missing:
            error("Missing required options:")
            for opt in missing:
                error(f"  → {opt}: {self.current_module.options[opt]['description']}")
            info("Use 'set <option> <value>' to configure")
            return

        console.print()
        print_separator()
        info(f"Running: [bold]{self.current_module.name}[/bold]")
        print_separator()
        console.print()

        try:
            self.current_module.run()
        except KeyboardInterrupt:
            console.print()
            warning("Module execution interrupted by user")
        except Exception as e:
            error(f"Module error: {e}")

        console.print()
        print_separator()

    def cmd_back(self, args):
        """Deselect the current module."""
        if self.current_module is None:
            info("No module is currently selected.")
            return

        info(f"Module '{self.current_module_path}' deselected")
        self.current_module = None
        self.current_module_path = None

    def cmd_search(self, args):
        """Search modules by keyword."""
        if not args:
            error("Usage: search <keyword>")
            return

        query = " ".join(args)
        results = self.loader.search_modules(query)

        if not results:
            warning(f"No modules found matching '{query}'")
            return

        columns = [
            ("Module", "cyan"),
            ("Name", "white"),
            ("Description", "dim white"),
        ]
        rows = [(path, m.name, m.description) for path, m in results.items()]
        print_table(f"Search Results for '{query}'", columns, rows)

    def cmd_modules(self, args):
        """Quick list of all modules."""
        self._show_modules()

    def cmd_banner(self, args):
        """Display the banner."""
        self.display_banner()

    def cmd_clear(self, args):
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def cmd_exit(self, args):
        """Exit IoTwizz."""
        console.print()
        console.print("[bold red]  ⚡ IoTwizz out. Happy hacking! ⚡[/bold red]")
        console.print()
        sys.exit(0)

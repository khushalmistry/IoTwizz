"""
IoTwizz - Color & Output Utilities
Rich-powered terminal output helpers.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


def success(message: str):
    """Print a success message."""
    console.print(f"  [bold green][+][/bold green] {message}")


def error(message: str):
    """Print an error message."""
    console.print(f"  [bold red][-][/bold red] {message}")


def warning(message: str):
    """Print a warning message."""
    console.print(f"  [bold yellow][!][/bold yellow] {message}")


def info(message: str):
    """Print an info message."""
    console.print(f"  [bold blue][*][/bold blue] {message}")


def debug(message: str):
    """Print a debug message."""
    console.print(f"  [dim][D][/dim] {message}", style="dim")


def result(message: str):
    """Print a result/finding message."""
    console.print(f"  [bold magenta][>][/bold magenta] {message}")


def print_banner(banner_text: str):
    """Print the IoTwizz banner."""
    console.print(banner_text)


def print_table(title: str, columns: list, rows: list, show_lines: bool = False):
    """Print a formatted table.

    Args:
        title: Table title
        columns: List of (name, style) tuples
        rows: List of row tuples/lists
        show_lines: Show row separator lines
    """
    table = Table(
        title=title,
        box=box.ROUNDED,
        title_style="bold cyan",
        header_style="bold white",
        show_lines=show_lines,
        padding=(0, 1),
    )

    for col_name, col_style in columns:
        table.add_column(col_name, style=col_style)

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print()
    console.print(table)
    console.print()


def print_module_info(module):
    """Print detailed module information in a panel."""
    info_text = Text()
    info_text.append(f"  Name:        ", style="bold white")
    info_text.append(f"{module.name}\n", style="cyan")
    info_text.append(f"  Category:    ", style="bold white")
    info_text.append(f"{module.category}\n", style="yellow")
    info_text.append(f"  Description: ", style="bold white")
    info_text.append(f"{module.description}\n", style="white")
    info_text.append(f"  Author:      ", style="bold white")
    info_text.append(f"{module.author}\n", style="green")

    panel = Panel(
        info_text,
        title="[bold red]Module Info[/bold red]",
        border_style="bright_black",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)


def print_options(options: dict):
    """Print module options in a formatted table."""
    columns = [
        ("Option", "cyan"),
        ("Value", "white"),
        ("Required", "yellow"),
        ("Description", "dim white"),
    ]

    rows = []
    for name, opt in options.items():
        value = opt.get("value", "") or ""
        required = "Yes" if opt.get("required", False) else "No"
        description = opt.get("description", "")
        rows.append((name, value, required, description))

    print_table("Module Options", columns, rows)


def print_separator():
    """Print a separator line."""
    console.print("[dim]" + "─" * 50 + "[/dim]")


def print_coming_soon(module_name: str):
    """Print a 'coming soon' message for stub modules."""
    panel = Panel(
        f"[bold yellow]⚠ Module '[cyan]{module_name}[/cyan]' is under development.\n"
        f"  This module will be available in a future release.[/bold yellow]\n\n"
        f"  [dim]Want to contribute? Add your implementation to the module file![/dim]",
        title="[bold yellow]🚧 Coming Soon 🚧[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)
    console.print()

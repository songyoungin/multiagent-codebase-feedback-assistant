"""Output formatters for analysis results."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_response(response: dict[str, Any]) -> None:
    """Print agent response in a user-friendly format.

    Args:
        response: Agent response dictionary
    """
    # Extract the actual response text from the A2A response structure
    if "response" in response:
        content = response["response"]
    elif "message" in response:
        content = response["message"]
    else:
        content = str(response)

    # Print in a nice panel
    console.print(Panel(content, title="[bold blue]Analysis Results[/bold blue]", border_style="blue"))


def print_table_from_dict(data: dict[str, Any], title: str = "Results") -> None:
    """Print dictionary data as a table.

    Args:
        data: Dictionary to display
        title: Table title
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for key, value in data.items():
        table.add_row(str(key), str(value))

    console.print(table)


def print_status_table(status: dict[str, str]) -> None:
    """Print container status as a table.

    Args:
        status: Dictionary mapping container names to their status
    """
    table = Table(title="Container Status", show_header=True, header_style="bold magenta")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")

    for agent, status_value in status.items():
        # Color code the status
        if status_value == "running":
            status_display = "[green]running[/green]"
        elif status_value == "exited":
            status_display = "[red]exited[/red]"
        else:
            status_display = f"[yellow]{status_value}[/yellow]"

        table.add_row(agent, status_display)

    console.print(table)


def print_error(message: str) -> None:
    """Print error message.

    Args:
        message: Error message to display
    """
    console.print(f"✗ [red]{message}[/red]")


def print_success(message: str) -> None:
    """Print success message.

    Args:
        message: Success message to display
    """
    console.print(f"✓ [green]{message}[/green]")


def print_warning(message: str) -> None:
    """Print warning message.

    Args:
        message: Warning message to display
    """
    console.print(f"⚠ [yellow]{message}[/yellow]")


def print_info(message: str) -> None:
    """Print info message.

    Args:
        message: Info message to display
    """
    console.print(f"ℹ [blue]{message}[/blue]")

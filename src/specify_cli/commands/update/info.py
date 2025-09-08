"""Installation info command implementation."""

import typer
from rich.console import Console

from ...services.update_service import UpdateService

console = Console()


def info_command(
    cache: bool = typer.Option(
        False, "--cache", help="Show detailed cache information"
    ),
    clear_cache: bool = typer.Option(
        False, "--clear-cache", help="Clear the version check cache"
    ),
) -> None:
    """Show installation and update information."""
    update_service = UpdateService()

    if clear_cache:
        update_service.clear_cache()
        console.print("[green]✓[/green] Version cache cleared")
        return

    # Show installation information
    update_service.show_installation_info()

    # Show additional cache details if requested
    if cache:
        cache_info = update_service.version_checker.get_cache_info()
        if cache_info:
            console.print("\n[bold]Detailed Cache Information[/bold]")
            for key, value in cache_info.items():
                if key != "cache_file":  # Already shown in main info
                    console.print(f"{key}: [dim]{value}[/dim]")
        else:
            console.print("\n[dim]No cache data available[/dim]")

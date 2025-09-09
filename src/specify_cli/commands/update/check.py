"""Update check command implementation."""

import typer
from rich.console import Console

from ...services.update_service import UpdateService

console = Console()


def check_update_command(
    force: bool = typer.Option(
        False, "--force", help="Force fresh check, bypass cache"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Only show output if update is available"
    ),
) -> None:
    """Check for available updates."""
    update_service = UpdateService()

    # Use force flag to bypass cache
    update_info = update_service.check_for_updates(use_cache=not force)

    # TODO: Use strong typing such as typed dict or pydantic model
    if update_info["has_update"]:
        current = update_info["current_version"]
        latest = update_info["latest_version"]
        method = update_info["method"]
        can_auto_update = update_info["supports_auto_update"]

        console.print("[yellow]Update available![/yellow]")
        console.print(f"Current version: [blue]{current}[/blue]")
        console.print(f"Latest version: [green]{latest}[/green]")
        console.print(f"Installation method: [cyan]{method}[/cyan]")

        if can_auto_update:
            console.print("\nRun [bold cyan]specifyx update[/bold cyan] to update")
        else:
            from ...services.update_installer import InstallationMethodDetector

            detector = InstallationMethodDetector()
            info = detector.get_installation_info()
            console.print(
                f"\nManual update required: [cyan]{info.get('update_command', 'See documentation')}[/cyan]"
            )

        # Exit with code 1 to indicate update available
        raise typer.Exit(1)
    else:
        if not quiet:
            console.print(
                f"[green]✓[/green] You are using the latest version ([bold cyan]v{update_info['current_version']}[/bold cyan])"
            )
        # Exit with code 0 for no update needed
        raise typer.Exit(0)

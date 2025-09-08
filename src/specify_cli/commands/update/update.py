"""Main update command implementation."""

from typing import Optional

import typer
from rich.console import Console

from ...services.update_service import UpdateService

console = Console()


def update_command(
    target_version: Optional[str] = typer.Option(
        None,
        "--target-version",
        "-t",
        help="Specific version to install (default: latest)",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force update even if already up to date"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be updated without doing it"
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Skip cache and force fresh version check"
    ),
) -> None:
    """Update SpecifyX to the latest version."""
    update_service = UpdateService()

    if dry_run:
        console.print("[yellow]Dry run mode - showing what would be done[/yellow]")
        console.print()

    # Check if we can auto-update (skip during dry run)
    if not dry_run and not update_service.installer.can_auto_update():
        console.print(
            "[yellow]⚠[/yellow] Automatic update not supported for your installation method."
        )
        # Apply no-cache behavior before showing installation info
        if no_cache:
            update_service.clear_cache()
        update_service.show_installation_info()
        console.print("\nPlease update manually using the command shown above.")
        raise typer.Exit(1)

    # Perform update check first (unless forced)
    if not force and not dry_run:
        update_info = update_service.check_for_updates(use_cache=not no_cache)
        if not update_info["has_update"]:
            console.print(
                f"[green]✓[/green] Already using the latest version ([bold cyan]v{update_info['current_version']}[/bold cyan])"
            )
            console.print("\nUse [cyan]--force[/cyan] to reinstall the current version")
            raise typer.Exit(0)

        current = update_info["current_version"]
        latest = update_info["latest_version"]
        target = target_version or latest

        if not dry_run:
            console.print(
                f"Updating from [blue]{current}[/blue] to [green]{target}[/green]"
            )
            console.print()

    # Perform the update
    success = update_service.perform_update(
        target_version=target_version, force=force, dry_run=dry_run
    )

    if dry_run:
        if success:
            console.print(
                "\n[green]✓[/green] Dry run completed - automatic update is supported"
            )
        else:
            console.print("\n[red]✗[/red] Automatic update not available")
            console.print("Manual update will be required")
        raise typer.Exit(0)

    if success:
        console.print("\n[green]✓[/green] Update completed successfully!")
        console.print(
            "You may need to restart your shell or run [cyan]hash -r[/cyan] to use the new version"
        )
    else:
        console.print("\n[red]✗[/red] Update failed")
        console.print("Please try updating manually or check the error messages above")
        raise typer.Exit(1)

"""Main update service orchestrator."""

from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel

from specify_cli.services.update_installer import (
    InstallationMethodDetector,
    UpdateInstaller,
)
from specify_cli.services.version_checker import PyPIVersionChecker


class UpdateService:
    """Main service for handling updates."""

    def __init__(self):
        self.console = Console()
        self.version_checker = PyPIVersionChecker()
        self.installer = UpdateInstaller()
        self.detector = InstallationMethodDetector()

    def check_for_updates(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Check for available updates.

        Returns:
            Dict containing update status information with canonical keys:
            - method: installation method identifier
            - supports_auto_update: whether automatic update is supported
        """
        has_update, current_version, latest_version = (
            self.version_checker.check_for_updates(use_cache)
        )

        return {
            "has_update": has_update,
            "current_version": current_version,
            "latest_version": latest_version,
            "method": self.detector.detect_installation_method(),
            "supports_auto_update": self.installer.can_auto_update(),
        }

    def show_update_notification(
        self, quiet: bool = False, force_check: bool = False
    ) -> bool:
        """
        Show update notification if updates are available.

        Args:
            quiet: Only show notification if update is available
            force_check: Skip cache and force fresh check

        Returns:
            bool: True if update is available
        """
        update_info = self.check_for_updates(use_cache=not force_check)

        if not update_info["has_update"]:
            if not quiet:
                self.console.print("[green]✓[/green] You are using the latest version!")
            return False

        # Create update notification
        current = update_info["current_version"]
        latest = update_info["latest_version"]
        method = update_info["method"]
        can_auto_update = update_info["supports_auto_update"]

        message_lines = [
            "[yellow]Update available![/yellow]",
            f"Current: [blue]{current}[/blue] → Latest: [green]{latest}[/green]",
            "",
        ]

        if can_auto_update:
            message_lines.extend(
                [
                    "Run [bold cyan]specifyx update perform[/bold cyan] to update automatically",
                    f"Installation method: [dim]{method}[/dim]",
                ]
            )
        else:
            installation_info = self.detector.get_installation_info()
            update_cmd = installation_info.get(
                "update_command", "Manual update required"
            )
            message_lines.extend(
                [
                    f"Installation method: [bold]{method}[/bold] (manual update required)",
                    f"Run: [bold cyan]{update_cmd}[/bold cyan]",
                ]
            )

            if "manual_note" in installation_info:
                message_lines.append(f"[dim]{installation_info['manual_note']}[/dim]")

        message = "\n".join(message_lines)

        self.console.print(
            Panel(
                message,
                title="[bold blue]SpecifyX Update Available[/bold blue]",
                border_style="blue",
            )
        )

        return True

    def perform_update(
        self,
        target_version: Optional[str] = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> bool:
        """
        Perform update installation.

        Args:
            target_version: Specific version to install
            force: Force update even if already up to date
            dry_run: Show what would be done without doing it

        Returns:
            bool: True if update was successful (or would be for dry run)
        """
        if dry_run:
            return self._show_dry_run_info(target_version)

        # Check if update is needed (unless forced)
        if not force:
            update_info = self.check_for_updates()
            if not update_info["has_update"]:
                self.console.print("[green]✓[/green] Already using the latest version!")
                return True

        # Perform the update
        return self.installer.perform_update(target_version, force)

    def _show_dry_run_info(self, target_version: Optional[str] = None) -> bool:
        """Show what would happen during an update."""
        dry_run_info = self.installer.dry_run_update(target_version)

        self.console.print(
            Panel(
                f"""[bold]Update Plan (Dry Run)[/bold]

Installation method: [cyan]{dry_run_info["method"]}[/cyan]
Target package: [green]{dry_run_info["package_spec"]}[/green]
Auto-update supported: [{"green" if dry_run_info["supports_auto_update"] else "red"}]{dry_run_info["supports_auto_update"]}[/]
Python executable: [dim]{dry_run_info["python_executable"]}[/dim]

Command that would be executed:
[bold cyan]{dry_run_info["update_command"]}[/bold cyan]""",
                title="[bold yellow]Dry Run[/bold yellow]",
                border_style="yellow",
            )
        )

        return dry_run_info["supports_auto_update"]

    def get_installation_info(self) -> Dict[str, Any]:
        """
        Get detailed installation and update information.

        Returns a combined dict containing canonical keys including:
        - method
        - supports_auto_update
        along with version and environment details.
        """
        update_info = self.check_for_updates()
        installation_info = self.detector.get_installation_info()
        cache_info = self.version_checker.get_cache_info()

        return {
            **update_info,
            **installation_info,
            "cache_info": cache_info,
        }

    def show_installation_info(self) -> None:
        """Display detailed installation and update information."""
        info = self.get_installation_info()

        # Current version status
        version_status = f"[green]{info['current_version']}[/green]"
        if info["has_update"]:
            version_status += f" → [yellow]{info['latest_version']} available[/yellow]"
        else:
            version_status += " [dim](latest)[/dim]"

        # Installation details
        install_details = [
            f"Method: [cyan]{info['method']}[/cyan]",
            f"Auto-update: [{'green' if info['supports_auto_update'] else 'red'}]{info['supports_auto_update']}[/]",
            f"Python: [dim]{info['python_executable']}[/dim]",
        ]

        if "update_command" in info:
            install_details.append(
                f"Update command: [cyan]{info['update_command']}[/cyan]"
            )

        # Cache information
        cache_details = []
        if info["cache_info"]:
            cache = info["cache_info"]
            cache_details = [
                f"Last check: [dim]{cache.get('last_check', 'never')}[/dim]",
                f"Cache age: [dim]{cache.get('cache_age_hours', 0):.1f} hours[/dim]",
                f"Cache file: [dim]{cache.get('cache_file', 'none')}[/dim]",
            ]
        else:
            cache_details = ["[dim]No cache data[/dim]"]

        # Display information
        self.console.print(
            Panel(
                f"""[bold]Version Information[/bold]
Current version: {version_status}

[bold]Installation Details[/bold]
{chr(10).join(install_details)}

[bold]Cache Information[/bold]
{chr(10).join(cache_details)}""",
                title="[bold blue]SpecifyX Installation Info[/bold blue]",
                border_style="blue",
            )
        )

    def clear_cache(self) -> None:
        """Clear the version check cache."""
        self.version_checker.clear_cache()
        self.console.print("[green]✓[/green] Version cache cleared")

    def force_check(self) -> Dict[str, Any]:
        """Force a fresh version check, bypassing cache."""
        return self.check_for_updates(use_cache=False)

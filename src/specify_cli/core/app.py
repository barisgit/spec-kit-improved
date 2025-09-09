"""Core CLI application setup and configuration.

This module contains the Typer app setup, Rich console configuration,
and main entry point for the SpecifyX CLI tool.
"""

import logging
import sys
from importlib.metadata import version

import typer
from rich.align import Align
from rich.console import Console
from rich.text import Text
from typer.core import TyperGroup

from specify_cli.utils.logging_config import setup_logging

# Setup logging for developers
setup_logging(log_level=logging.CRITICAL)

# ASCII Art Banner
BANNER = """
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗    ██╗  ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝    ╚██╗██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝█████╗╚███╔╝ 
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝ ╚════╝██╔██╗ 
███████║██║     ███████╗╚██████╗██║██║        ██║       ██╔╝ ██╗
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝       ╚═╝  ╚═╝
"""

TAGLINE = "Spec-Driven Development Toolkit"

# Rich console instance
console = Console()


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


def show_banner():
    """Display the ASCII art banner with enhanced colorization for front and back characters."""
    banner_lines = BANNER.strip().split("\n")

    # Professional color palette: green to teal gradient for front characters
    front_colors = [
        "bright_green",
        "green",
        "bright_cyan",
        "cyan",
        "bright_blue",
        "blue",
    ]
    # Subtle background color for decorative elements
    back_color = "dim white"

    num_colors = len(front_colors)

    # Print each line with different colors for front and back characters
    for i, line in enumerate(banner_lines):
        # Get front color for this line using gradient
        front_color_index = int((i / len(banner_lines)) * num_colors) % num_colors
        front_color = front_colors[front_color_index]

        # Split the line into front characters (█) and back characters (box drawing)
        # Only the solid block characters █ are front characters
        # All other characters (╗╔╝║═╚ and spaces) are back characters
        colored_line = ""
        for char in line:
            if char == "█":
                # Only the solid block character is the front character
                colored_line += f"[bold {front_color}]{char}[/]"
            else:
                # All other characters are back characters
                colored_line += f"[{back_color}]{char}[/]"

        console.print(Align.center(colored_line))

    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


# Main Typer app instance
app = typer.Typer(
    name="specify",
    help="Setup tool for SpecifyX spec-driven development projects",
    add_completion=True,
    invoke_without_command=True,
    cls=BannerGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def callback(
    ctx: typer.Context,
    show_version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
    no_update_check: bool = typer.Option(
        False, "--no-update-check", help="Skip automatic update check"
    ),
):
    """Show banner when no subcommand is provided."""
    # Handle version flag
    if show_version:
        try:
            pkg_version = version("specifyx")  # TODO: Move package name to constants.py
        except Exception:
            pkg_version = "unknown"

        # Show version with update information
        version_text = f"SpecifyX CLI [bold cyan]v{pkg_version}[/bold cyan]"

        # Check for updates when showing version (unless disabled)
        if not no_update_check:
            try:
                from specify_cli.services.update_service import UpdateService

                update_service = UpdateService()
                update_info = update_service.check_for_updates()

                if update_info["has_update"]:
                    latest = update_info["latest_version"]
                    version_text += f" [yellow]→ {latest} available[/yellow]"
                    console.print(version_text)
                    console.print("[dim]Run 'specifyx update perform' to upgrade[/dim]")
                else:
                    console.print(version_text)
            except Exception:
                # If update check fails, just show version
                console.print(version_text)
        else:
            console.print(version_text)

        raise typer.Exit()

    # Auto-update check for non-help, non-version commands (unless disabled)
    if (
        not no_update_check
        and ctx.invoked_subcommand is not None
        and ctx.invoked_subcommand not in ("update", "help")
        and "--help" not in sys.argv
        and "-h" not in sys.argv
    ):
        try:
            from specify_cli.services.update_service import UpdateService

            update_service = UpdateService()
            # Show update notification quietly (only if update available)
            update_service.show_update_notification(quiet=True)
        except Exception:
            # Update check should never break the main functionality
            pass

    # Show banner only when no subcommand and no help flag
    # (help is handled by BannerGroup)
    if (
        ctx.invoked_subcommand is None
        and "--help" not in sys.argv
        and "-h" not in sys.argv
    ):
        show_banner()
        console.print(
            Align.center("[dim]Run 'specifyx --help' for usage information[/dim]")
        )
        console.print()


def register_commands():
    """Register commands with the main app."""
    from specify_cli.commands import check_command, init_command, run_app, update_app

    # Register commands directly on main app
    app.command("init")(init_command)
    app.command("check")(check_command)

    # Register run command with subcommands - the default command is 'run_command'
    app.add_typer(run_app, name="run")

    # Register update group
    app.add_typer(update_app, name="update")


def main():
    """Main entry point for the SpecifyX CLI."""
    register_commands()
    app()

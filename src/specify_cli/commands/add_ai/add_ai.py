"""Add AI assistant command for existing projects."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from specify_cli.assistants import (
    get_assistant,
    list_assistant_names,
)
from specify_cli.services import (
    AssistantManagementService,
    CommandLineGitService,
    TomlConfigService,
)
from specify_cli.services.project_manager import ProjectManager
from specify_cli.utils.ui_helpers import select_ai_assistant_for_add

console = Console()


def get_assistant_management_service(
    project_manager: ProjectManager,
) -> AssistantManagementService:
    """Factory function to create AssistantManagementService with dependencies."""
    return AssistantManagementService(
        project_manager=project_manager,
        console=console,
    )


def confirm_creation(assistant, files_to_create: list[str], force: bool) -> bool:
    """Ask user to confirm file creation."""
    console.print(
        f"\nThis will create files for [cyan]{assistant.config.display_name}[/cyan]:"
    )

    for file_path in files_to_create:
        console.print(f"  [green]+[/green] {file_path}")

    if force:
        console.print(
            "\n[yellow]Warning: --force will overwrite existing files![/yellow]"
        )

    return typer.confirm("\nProceed?")


def add_ai_command(
    assistant_name: Optional[str] = typer.Argument(
        None,
        help=f"AI assistant to add: {', '.join(list_assistant_names())} (interactive if not specified)",
    ),
    list_status: bool = typer.Option(
        False, "--list", help="Show status of all available assistants"
    ),
    show_injection_points: bool = typer.Option(
        False,
        "--injection-points",
        help="Show all available injection points and their descriptions",
    ),
    show_assistant_values: bool = typer.Option(
        False,
        "--show-values",
        help="Show injection point values for a specific assistant (requires assistant name)",
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite existing AI assistant files"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be created without doing it"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
) -> None:
    """Add an AI assistant to an existing SpecifyX project.

    This command adds AI-specific files (context files, commands, agents)
    to a project that's already been initialized with SpecifyX.

    Multiple AI assistants can coexist since each uses separate directories.

    Use --injection-points to see all available injection points and their descriptions.
    Use --show-values <assistant> to see the actual values an assistant provides.
    Use --list to see which assistants are already configured in the current project.
    """
    project_path = Path.cwd()
    config_service = TomlConfigService()
    git_service = CommandLineGitService()
    project_manager = ProjectManager(
        config_service=config_service, git_service=git_service
    )
    assistant_service = get_assistant_management_service(project_manager)

    # Handle informational options that don't require a SpecifyX project
    if show_injection_points:
        assistant_service.show_injection_points_info()
        return

    if show_assistant_values:
        if assistant_name is None:
            console.print(
                "[red]Error:[/red] --show-values requires an assistant name.\n"
                f"Available assistants: {', '.join(list_assistant_names())}"
            )
            raise typer.Exit(1)

        if assistant_name not in list_assistant_names():
            console.print(
                f"[red]Error:[/red] Unknown assistant '{assistant_name}'. "
                f"Available: {', '.join(list_assistant_names())}"
            )
            raise typer.Exit(1)

        assistant_service.show_assistant_injection_values(assistant_name)
        return

    # Check if this is a SpecifyX project
    if not project_manager.is_project_initialized(project_path):
        console.print(
            "[red]Error:[/red] This directory is not a SpecifyX project.\n"
            "Run [cyan]specify init[/cyan] first to initialize the project."
        )
        raise typer.Exit(1)

    # Handle --list option
    if list_status:
        console.print(
            f"\n[bold]AI Assistant Status for [cyan]{project_path.name}[/cyan][/bold]\n"
        )
        assistant_service.show_assistant_status(project_path)
        return

    # Interactive selection if no assistant specified
    if assistant_name is None:
        try:
            assistant_name = select_ai_assistant_for_add(project_path)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
            raise typer.Exit(0) from None

    # Validate assistant name
    if assistant_name not in list_assistant_names():
        console.print(
            f"[red]Error:[/red] Unknown assistant '{assistant_name}'. "
            f"Available: {', '.join(list_assistant_names())}"
        )
        raise typer.Exit(1)

    assistant = get_assistant(assistant_name)
    if not assistant:
        console.print(f"[red]Error:[/red] Failed to load assistant '{assistant_name}'")
        raise typer.Exit(1)

    # Check current status
    status = assistant_service.check_assistant_status(project_path, assistant_name)

    console.print(
        Panel.fit(
            f"[bold cyan]Adding AI Assistant[/bold cyan]\n"
            f"Assistant: [green]{assistant.config.display_name}[/green]\n"
            f"Project: [cyan]{project_path.name}[/cyan]\n"
            f"Current Status: {assistant_service.get_status_text(status)}",
            border_style="cyan",
        )
    )

    # Handle existing configuration
    if status == "configured" and not force:
        console.print(
            f"[yellow]Assistant '{assistant_name}' is already configured.[/yellow]\n"
            "Use [cyan]--force[/cyan] to overwrite existing files."
        )
        raise typer.Exit(0)

    # Show what will be created
    files_to_create = assistant_service.get_files_to_create(
        assistant_name, project_path
    )

    if dry_run:
        console.print("\n[bold]Files that would be created:[/bold]")
        for file_path in files_to_create:
            console.print(f"  [green]+[/green] {file_path}")
        return

    # Confirmation
    if not yes and not confirm_creation(assistant, files_to_create, force):
        console.print("[yellow]Operation cancelled[/yellow]")
        raise typer.Exit(0)

    # Create the assistant files
    success = assistant_service.create_assistant_files(
        project_path, assistant_name, force
    )

    if success:
        console.print(
            f"\n[green]✓[/green] Successfully added [cyan]{assistant.config.display_name}[/cyan]!"
        )
        console.print(
            f"Context file: [cyan]{assistant.config.context_file.file}[/cyan]"
        )
        console.print(
            f"Commands directory: [cyan]{assistant.config.command_files.directory}[/cyan]"
        )

        # Show next steps
        console.print(
            "\n[bold]Next steps:[/bold]\n"
            f"• Edit [cyan]{assistant.config.context_file.file}[/cyan] to customize your AI context\n"
            f"• Explore commands in [cyan]{assistant.config.command_files.directory}/[/cyan]\n"
            "• Run [cyan]specify check[/cyan] to verify the setup"
        )
    else:
        console.print(f"[red]✗[/red] Failed to add {assistant.config.display_name}")
        raise typer.Exit(1)

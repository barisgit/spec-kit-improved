"""Add AI assistant command for existing projects."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from specify_cli.assistants import (
    get_all_assistants,
    get_assistant,
    list_assistant_names,
)
from specify_cli.assistants.types import (
    INJECTION_POINT_DESCRIPTIONS,
    OPTIONAL_INJECTION_POINTS,
    REQUIRED_INJECTION_POINTS,
)
from specify_cli.models.project import ProjectInitOptions
from specify_cli.services import CommandLineGitService, TomlConfigService
from specify_cli.services.project_manager import ProjectManager
from specify_cli.utils.ui_helpers import select_ai_assistant_for_add

console = Console()


def get_project_manager() -> ProjectManager:
    """Factory function to create ProjectManager with all dependencies."""
    config_service = TomlConfigService()
    git_service = CommandLineGitService()

    return ProjectManager(
        config_service=config_service,
        git_service=git_service,
    )


def check_assistant_status(project_path: Path, assistant_name: str) -> str:
    """Check if an assistant is already configured in the project.

    Returns:
        'configured', 'partial', or 'missing'
    """
    assistant = get_assistant(assistant_name)
    if not assistant:
        return "missing"

    config = assistant.config

    # Check if base directory exists
    base_dir = project_path / config.base_directory
    if not base_dir.exists():
        return "missing"

    # Check if context file exists
    context_file = project_path / config.context_file.file
    if not context_file.exists():
        return "partial"

    # Check if commands directory exists
    commands_dir = project_path / config.command_files.directory
    if not commands_dir.exists():
        return "partial"

    return "configured"


def show_assistant_status(project_path: Path) -> None:
    """Show the status of all available assistants."""
    table = Table(title="AI Assistant Status")
    table.add_column("Assistant", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Base Directory", style="dim")

    assistants = get_all_assistants()

    for assistant in assistants:
        status = check_assistant_status(project_path, assistant.config.name)

        if status == "configured":
            status_text = "[green]✓ Configured[/green]"
        elif status == "partial":
            status_text = "[yellow]⚠️  Partial[/yellow]"
        else:
            status_text = "[red]✗ Not configured[/red]"

        table.add_row(
            assistant.config.name,
            assistant.config.display_name,
            status_text,
            assistant.config.base_directory,
        )

    console.print(table)


def show_injection_points_info() -> None:
    """Show information about injection points and their descriptions."""
    console.print("\n[bold cyan]Injection Points Reference[/bold cyan]")
    console.print(
        "These are the template injection points that AI assistants can provide:\n"
    )

    # Required injection points
    console.print("[bold green]Required Injection Points[/bold green]")
    console.print("Every AI assistant must provide these injection points:")

    for point in REQUIRED_INJECTION_POINTS:
        description = INJECTION_POINT_DESCRIPTIONS.get(
            point, "No description available"
        )
        console.print(f"  • [cyan]{point.value}[/cyan]")
        console.print(f"    {description}\n")

    # Optional injection points
    console.print("[bold yellow]Optional Injection Points[/bold yellow]")
    console.print("AI assistants may optionally provide these injection points:")

    for point in OPTIONAL_INJECTION_POINTS:
        description = INJECTION_POINT_DESCRIPTIONS.get(
            point, "No description available"
        )
        console.print(f"  • [cyan]{point.value}[/cyan]")
        console.print(f"    {description}\n")


def show_assistant_injection_values(assistant_name: str) -> None:
    """Show the injection point values for a specific assistant."""
    assistant = get_assistant(assistant_name)
    if not assistant:
        console.print(f"[red]Error:[/red] Assistant '{assistant_name}' not found")
        return

    injection_values = assistant.get_injection_values()

    console.print(
        f"\n[bold cyan]Injection Point Values for {assistant.config.display_name}[/bold cyan]"
    )
    console.print("These are the actual values this assistant provides:\n")

    # Group by required vs optional
    required_values = {
        k: v for k, v in injection_values.items() if k in REQUIRED_INJECTION_POINTS
    }
    optional_values = {
        k: v for k, v in injection_values.items() if k in OPTIONAL_INJECTION_POINTS
    }

    if required_values:
        console.print("[bold green]Required Values[/bold green]")
        for point, value in required_values.items():
            description = INJECTION_POINT_DESCRIPTIONS.get(
                point, "No description available"
            )
            console.print(f"  • [cyan]{point.value}[/cyan]: [white]{value}[/white]")
            console.print(f"    [dim]{description}[/dim]\n")

    if optional_values:
        console.print("[bold yellow]Optional Values[/bold yellow]")
        for point, value in optional_values.items():
            description = INJECTION_POINT_DESCRIPTIONS.get(
                point, "No description available"
            )
            console.print(f"  • [cyan]{point.value}[/cyan]: [white]{value}[/white]")
            console.print(f"    [dim]{description}[/dim]\n")


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
    project_manager = get_project_manager()

    # Handle informational options that don't require a SpecifyX project
    if show_injection_points:
        show_injection_points_info()
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

        show_assistant_injection_values(assistant_name)
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
        show_assistant_status(project_path)
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
    status = check_assistant_status(project_path, assistant_name)

    console.print(
        Panel.fit(
            f"[bold cyan]Adding AI Assistant[/bold cyan]\n"
            f"Assistant: [green]{assistant.config.display_name}[/green]\n"
            f"Project: [cyan]{project_path.name}[/cyan]\n"
            f"Current Status: {get_status_text(status)}",
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
    files_to_create = get_files_to_create(assistant, project_path)

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
    success = create_assistant_files(project_manager, project_path, assistant_name)

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


def get_status_text(status: str) -> str:
    """Convert status to colored text."""
    if status == "configured":
        return "[green]✓ Configured[/green]"
    elif status == "partial":
        return "[yellow]⚠️  Partially configured[/yellow]"
    else:
        return "[red]✗ Not configured[/red]"


def get_files_to_create(assistant, project_path: Path) -> list[str]:
    """Get list of files that will be created."""
    files = []
    config = assistant.config

    # Context file
    context_file = project_path / config.context_file.file
    files.append(str(context_file.relative_to(project_path)))

    # Commands directory (will contain multiple files)
    commands_dir = config.command_files.directory
    files.append(f"{commands_dir}/")

    # Agents directory (will contain multiple files)
    agents_dir = config.agent_files.directory
    files.append(f"{agents_dir}/")

    return files


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


def create_assistant_files(
    project_manager: ProjectManager, project_path: Path, assistant_name: str
) -> bool:
    """Create AI assistant files using the project manager."""
    try:
        # Create minimal options for AI-only initialization
        options = ProjectInitOptions(
            project_name=project_path.name,
            ai_assistants=[assistant_name],
            use_current_dir=True,  # Initialize in current directory
            force=True,  # Allow overwriting since we already confirmed
        )

        # Use the project manager to create only AI-specific files
        # We'll need to add a method for this
        return create_ai_only_files(project_manager, options, project_path)

    except Exception as e:
        console.print(f"[red]Error creating files:[/red] {e}")
        return False


def create_ai_only_files(
    project_manager: ProjectManager, options: ProjectInitOptions, project_path: Path
) -> bool:
    """Create only AI-specific files using the existing template system."""
    try:
        # Load existing project config to update it
        from specify_cli.services import TomlConfigService

        config_service = TomlConfigService()

        project_config = config_service.load_project_config(project_path)
        if project_config:
            # Add the new assistant to the existing config
            project_config.template_settings.add_assistant(options.ai_assistants[0])

            # Save the updated config
            config_service.save_project_config(project_path, project_config)
        else:
            console.print(
                "[yellow]Warning: Could not load project config, proceeding anyway[/yellow]"
            )

        # Create template context for the new assistant
        from specify_cli.models.config import BranchNamingConfig
        from specify_cli.models.project import TemplateContext

        context = TemplateContext(
            project_name=options.project_name or project_path.name,
            ai_assistant=options.ai_assistants[0],
            project_path=project_path,
            branch_naming_config=project_config.branch_naming
            if project_config
            else BranchNamingConfig(),
        )

        # Use the existing template rendering system
        render_result = project_manager._render_all_templates(context)

        if render_result.success:
            console.print(
                f"[green]✓[/green] Created {options.ai_assistants[0]} files using template system"
            )
            return True
        else:
            console.print("[red]Template rendering failed:[/red]")
            for error in render_result.errors:
                console.print(f"  • {error}")
            return False

    except Exception as e:
        console.print(f"[red]Error creating files:[/red] {e}")
        return False

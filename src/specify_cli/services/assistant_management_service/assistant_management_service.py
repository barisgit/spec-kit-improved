"""Service for managing AI assistant configurations and operations."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from specify_cli.assistants import get_all_assistants, get_assistant
from specify_cli.assistants.constants import (
    OPTIONAL_INJECTION_POINTS,
    REQUIRED_INJECTION_POINTS,
)
from specify_cli.assistants.injection_points import get_injection_point_descriptions
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.project import ProjectInitOptions, TemplateContext
from specify_cli.services.config_service import TomlConfigService
from specify_cli.services.project_manager import ProjectManager


class AssistantManagementService:
    """Service for managing AI assistant configurations and operations."""

    def __init__(
        self,
        project_manager: ProjectManager,
        config_service: Optional[TomlConfigService] = None,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize the assistant management service.

        Args:
            project_manager: Project manager for file operations
            config_service: Config service for project configuration
            console: Rich console for output (creates new if None)
        """
        self.project_manager = project_manager
        self.config_service = config_service or TomlConfigService()
        self.console = console or Console()

    def check_assistant_status(self, project_path: Path, assistant_name: str) -> str:
        """Check if an assistant is already configured in the project.

        Args:
            project_path: Path to the project directory
            assistant_name: Name of the assistant to check

        Returns:
            'configured', 'partial', or 'missing'
        """
        assistant = get_assistant(assistant_name)
        if not assistant:
            return "missing"

        config = assistant.config

        try:
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
        except (PermissionError, OSError):
            # Handle file system errors gracefully
            return "missing"

    def get_status_text(self, status: str) -> str:
        """Convert status to colored text.

        Args:
            status: Status string ('configured', 'partial', or 'missing')

        Returns:
            Colored text representation of the status
        """
        if status == "configured":
            return "[green]✓ Configured[/green]"
        elif status == "partial":
            return "[yellow]⚠️  Partially configured[/yellow]"
        else:
            return "[red]✗ Not configured[/red]"

    def show_assistant_status(self, project_path: Path) -> None:
        """Show the status of all available assistants.

        Args:
            project_path: Path to the project directory
        """
        table = Table(title="AI Assistant Status")
        table.add_column("Assistant", style="cyan")
        table.add_column("Display Name", style="white")
        table.add_column("Status", style="bold")
        table.add_column("Base Directory", style="dim")

        assistants = get_all_assistants()

        for assistant in assistants:
            status = self.check_assistant_status(project_path, assistant.config.name)
            status_text = self.get_status_text(status)

            table.add_row(
                assistant.config.name,
                assistant.config.display_name,
                status_text,
                assistant.config.base_directory,
            )

        self.console.print(table)

    def show_injection_points_info(self) -> None:
        """Show information about injection points and their descriptions."""
        self.console.print("\n[bold cyan]Injection Points Reference[/bold cyan]")
        self.console.print(
            "These are the template injection points that AI assistants can provide:\n"
        )

        # Required injection points
        self.console.print("[bold green]Required Injection Points[/bold green]")
        self.console.print("Every AI assistant must provide these injection points:")

        injection_point_descriptions = get_injection_point_descriptions()
        for point in REQUIRED_INJECTION_POINTS:
            description = injection_point_descriptions.get(
                point.name, "No description available"
            )
            self.console.print(f"  • [cyan]{point.name}[/cyan]")
            self.console.print(f"    {description}\n")

        # Optional injection points
        self.console.print("[bold yellow]Optional Injection Points[/bold yellow]")
        self.console.print(
            "AI assistants may optionally provide these injection points:"
        )

        for point in OPTIONAL_INJECTION_POINTS:
            description = injection_point_descriptions.get(
                point.name, "No description available"
            )
            self.console.print(f"  • [cyan]{point.name}[/cyan]")
            self.console.print(f"    {description}\n")

    def show_assistant_injection_values(self, assistant_name: str) -> None:
        """Show the injection point values for a specific assistant.

        Args:
            assistant_name: Name of the assistant to show values for
        """
        assistant = get_assistant(assistant_name)
        if not assistant:
            self.console.print(
                f"[red]Error:[/red] Assistant '{assistant_name}' not found"
            )
            return

        injection_values = assistant.get_injection_values()

        self.console.print(
            f"\n[bold cyan]Injection Point Values for {assistant.config.display_name}[/bold cyan]"
        )
        self.console.print("These are the actual values this assistant provides:\n")

        # Group by required vs optional
        required_values = {
            k: v for k, v in injection_values.items() if k in REQUIRED_INJECTION_POINTS
        }
        optional_values = {
            k: v for k, v in injection_values.items() if k in OPTIONAL_INJECTION_POINTS
        }

        if required_values:
            self.console.print("[bold green]Required Values[/bold green]")
            injection_point_descriptions = get_injection_point_descriptions()
            for point, value in required_values.items():
                description = injection_point_descriptions.get(
                    point.name, "No description available"
                )
                self.console.print(
                    f"  • [cyan]{point.name}[/cyan]: [white]{value}[/white]"
                )
                self.console.print(f"    [dim]{description}[/dim]\n")

        if optional_values:
            self.console.print("[bold yellow]Optional Values[/bold yellow]")
            for point, value in optional_values.items():
                description = injection_point_descriptions.get(
                    point.name, "No description available"
                )
                self.console.print(
                    f"  • [cyan]{point.name}[/cyan]: [white]{value}[/white]"
                )
                self.console.print(f"    [dim]{description}[/dim]\n")

    def get_files_to_create(self, assistant_name: str, project_path: Path) -> list[str]:
        """Get list of files that will be created for an assistant.

        Args:
            assistant_name: Name of the assistant
            project_path: Path to the project directory

        Returns:
            List of relative file paths that will be created
        """
        assistant = get_assistant(assistant_name)
        if not assistant:
            return []

        files = []
        config = assistant.config

        # Context file
        context_file = project_path / config.context_file.file
        files.append(str(context_file.relative_to(project_path)))

        # Commands directory (will contain multiple files)
        commands_dir = config.command_files.directory
        files.append(f"{commands_dir}/")

        # Agents directory (will contain multiple files) - only if enabled
        if config.agent_files:
            agents_dir = config.agent_files.directory
            files.append(f"{agents_dir}/")

        return files

    def create_assistant_files(
        self, project_path: Path, assistant_name: str, force: bool = False
    ) -> bool:
        """Create AI assistant files using the project manager.

        Args:
            project_path: Path to the project directory
            assistant_name: Name of the assistant to create files for
            force: Whether to overwrite existing files

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create minimal options for AI-only initialization
            options = ProjectInitOptions(
                project_name=project_path.name,
                ai_assistants=[assistant_name],
                use_current_dir=True,  # Initialize in current directory
                force=force,
            )

            # Use the project manager to create only AI-specific files
            return self._create_ai_only_files(options, project_path)

        except Exception as e:
            self.console.print(f"[red]Error creating files:[/red] {e}")
            return False

    def _create_ai_only_files(
        self, options: ProjectInitOptions, project_path: Path
    ) -> bool:
        """Create only AI-specific files using the existing template system.

        Args:
            options: Project initialization options
            project_path: Path to the project directory

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing project config to update it
            project_config = self.config_service.load_project_config(project_path)
            if project_config:
                # Add the new assistant to the existing config
                project_config.template_settings.add_assistant(options.ai_assistants[0])

                # Save the updated config
                self.config_service.save_project_config(project_path, project_config)
            else:
                self.console.print(
                    "[yellow]Warning: Could not load project config, proceeding anyway[/yellow]"
                )

            # Create template context for the new assistant
            context = TemplateContext(
                project_name=options.project_name or project_path.name,
                ai_assistant=options.ai_assistants[0],
                project_path=project_path,
                branch_naming_config=project_config.branch_naming
                if project_config
                else BranchNamingConfig(),
            )

            # Use the existing template rendering system
            render_result = self.project_manager._render_all_templates(context)

            if render_result.success:
                self.console.print(
                    f"[green]✓[/green] Created {options.ai_assistants[0]} files using template system"
                )
                return True
            else:
                self.console.print("[red]Template rendering failed:[/red]")
                for error in render_result.errors:
                    self.console.print(f"  • {error}")
                return False

        except Exception as e:
            self.console.print(f"[red]Error creating files:[/red] {e}")
            return False

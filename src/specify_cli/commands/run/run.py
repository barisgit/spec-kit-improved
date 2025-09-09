"""Run command implementation for executing generated Python scripts."""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from ...services.script_discovery_service import FileSystemScriptDiscoveryService
from ...services.script_execution_service import SubprocessScriptExecutionService

console = Console()

# Define typer options at module level to avoid B008 violation
_PROJECT_PATH_OPTION = typer.Option(
    None, "--project", "-p", help="Project path (defaults to current directory)"
)

# Create the Typer app
run_app = typer.Typer(
    help="Execute generated Python scripts",
    invoke_without_command=True,
)


@run_app.callback()
def run_callback(
    commands: Annotated[Optional[List[str]], typer.Argument()] = None,
    list_scripts: bool = typer.Option(
        False, "--list", "-l", help="List available scripts"
    ),
    which_script: Optional[str] = typer.Option(
        None, "--which", help="Show path to specified script"
    ),
    project_path: Optional[Path] = _PROJECT_PATH_OPTION,
) -> None:
    """Execute a generated Python script with arguments passed through.

    Pass all arguments after script name directly to the script:
        specifyx run setup-plan --help
        specifyx run setup-plan --json --verbose
    """

    # Handle utility flags first
    if list_scripts:
        _list_available_scripts(project_path)
        return

    if which_script:
        _show_script_path(which_script, project_path)
        return

    # Parse script name and arguments from commands list
    if not commands:
        console.print(
            "[red]Error:[/red] Must provide a script name or use --list to see available scripts"
        )
        console.print("Use --help for more information.")
        raise typer.Exit(1)

    script_name = commands[0]
    script_args = commands[1:] if len(commands) > 1 else []

    try:
        # Initialize services
        discovery_service = FileSystemScriptDiscoveryService(project_path or Path.cwd())
        execution_service = SubprocessScriptExecutionService()

        # Find the script
        script_path = discovery_service.find_script(script_name)
        if not script_path:
            available_scripts = discovery_service.list_available_scripts()
            console.print(f"[red]Error:[/red] Script '{script_name}' not found.")
            if available_scripts:
                console.print("Available scripts:")
                for script in available_scripts:
                    console.print(f"  - {script}")
            else:
                console.print("No scripts found in .specify/scripts/ directory.")
            raise typer.Exit(1)

        # Execute the script with all arguments passed through
        result = execution_service.execute_script(script_path, script_args)

        # Output result directly (let script handle its own formatting)
        if result.output:
            typer.echo(result.output, nl=False)
        if result.error:
            typer.echo(result.error, err=True, nl=False)

        # Exit with script's exit code
        if not result.success:
            raise typer.Exit(result.return_code or 1)

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to execute script: {str(e)}")
        raise typer.Exit(1) from e


def _show_script_path(script_name: str, project_path: Optional[Path]) -> None:
    """Show the full path to a script."""
    try:
        discovery_service = FileSystemScriptDiscoveryService(project_path or Path.cwd())
        script_path = discovery_service.find_script(script_name)

        if script_path:
            typer.echo(str(script_path))
        else:
            console.print(f"[red]Error:[/red] Script '{script_name}' not found")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to locate script: {str(e)}")
        raise typer.Exit(1) from e


def _list_available_scripts(project_path: Optional[Path]) -> None:
    """List all available scripts in the project."""
    try:
        discovery_service = FileSystemScriptDiscoveryService(project_path or Path.cwd())
        scripts = discovery_service.list_available_scripts()

        if not scripts:
            typer.echo("No scripts found in .specify/scripts/ directory.")
            return

        typer.echo("Available scripts:")
        for script in scripts:
            script_path = discovery_service.find_script(script)
            if script_path and script_path.exists():
                # Try to get description from script docstring
                try:
                    with open(script_path, "r") as f:
                        first_lines = [f.readline().strip() for _ in range(5)]

                    description = "No description available"
                    for line in first_lines:
                        if line.startswith('"""') and len(line) > 3:
                            # Extract content between triple quotes
                            content = line[3:]
                            if content.endswith('"""'):
                                content = content[:-3]
                            description = content.strip()
                            break
                        elif line.startswith("# ") and "description:" in line.lower():
                            description = line[2:].strip()
                            break

                    typer.echo(f"  {script:<20} - {description}")

                except Exception:
                    typer.echo(f"  {script}")
            else:
                typer.echo(f"  {script} (not found)")

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to list scripts: {str(e)}")
        raise typer.Exit(1) from e

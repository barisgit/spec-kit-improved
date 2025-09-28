"""Refresh templates command for updating project templates from various sources."""

import difflib
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from specify_cli.services import CommandLineGitService, TomlConfigService
from specify_cli.services.download_service import HttpxDownloadService
from specify_cli.services.project_manager import ProjectManager
from specify_cli.services.template_registry import TEMPLATE_REGISTRY
from specify_cli.services.template_service import (
    TemplateChange,
    TemplateChangeType,
    TemplateDiff,
    get_template_service,
)
from specify_cli.utils.ui_helpers import multiselect_agent_types

console = Console()


def get_download_service() -> HttpxDownloadService:
    """Factory function to create download service."""
    return HttpxDownloadService(console=console)


def show_unified_diff(change: "TemplateChange") -> None:
    """Display a unified diff for a specific file change."""
    if change.change_type == TemplateChangeType.ADDED:
        # Show new file content
        content = change.new_content or ""
        console.print(f"\n[green]New file: {change.template_name}[/green]")
        if content.strip():
            try:
                # Try to syntax highlight based on file extension
                syntax = Syntax(
                    content,
                    lexer_name_from_filename(change.template_name),
                    theme="monokai",
                    line_numbers=True,
                )
                console.print(syntax)
            except Exception:
                # Fallback to plain text
                console.print(content)
        else:
            console.print("[dim](empty file)[/dim]")

    elif change.change_type == TemplateChangeType.DELETED:
        # Show deleted file content
        content = change.old_content or ""
        console.print(f"\n[red]Deleted file: {change.template_name}[/red]")
        if content.strip():
            console.print(
                "[dim]"
                + content[:500]
                + ("..." if len(content) > 500 else "")
                + "[/dim]"
            )
        else:
            console.print("[dim](was empty)[/dim]")

    elif change.change_type == TemplateChangeType.MODIFIED:
        # Show unified diff
        old_content = change.old_content or ""
        new_content = change.new_content or ""

        console.print(f"\n[yellow]Modified: {change.template_name}[/yellow]")

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{change.template_name}",
                tofile=f"b/{change.template_name}",
                lineterm="",
            )
        )

        if diff_lines:
            # Display diff with color coding
            for line in diff_lines[2:]:  # Skip the file header lines
                line = line.rstrip()
                if line.startswith("+++") or line.startswith("---"):
                    console.print(f"[bold]{line}[/bold]")
                elif line.startswith("+"):
                    console.print(f"[green]{line}[/green]")
                elif line.startswith("-"):
                    console.print(f"[red]{line}[/red]")
                elif line.startswith("@@"):
                    console.print(f"[cyan]{line}[/cyan]")
                else:
                    console.print(f"[dim]{line}[/dim]")
        else:
            console.print("[dim]No differences found[/dim]")


def lexer_name_from_filename(filename: str) -> str:
    """Get appropriate syntax lexer for a file."""
    if filename.endswith(".py"):
        return "python"
    elif filename.endswith(".md"):
        return "markdown"
    elif filename.endswith(".json"):
        return "json"
    elif filename.endswith(".yaml") or filename.endswith(".yml"):
        return "yaml"
    elif filename.endswith(".toml"):
        return "toml"
    elif filename.endswith(".sh"):
        return "bash"
    else:
        return "text"


def show_template_diff(
    diff: TemplateDiff, verbosity: int = 0, show_skipped: bool = False
) -> None:
    """Display template differences in a user-friendly format."""

    if not diff.has_changes:
        console.print(
            "[green]✓[/green] No template changes found - everything is up to date!"
        )
        return

    # Create summary table
    table = Table(title="Template Changes Summary")
    table.add_column("Change Type", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Files")

    # Group changes by type
    added_files = [
        c
        for c in diff.changes
        if c.change_type == TemplateChangeType.ADDED
        and not (c.should_skip and not show_skipped)
    ]
    modified_files = [
        c
        for c in diff.changes
        if c.change_type == TemplateChangeType.MODIFIED
        and not (c.should_skip and not show_skipped)
    ]
    deleted_files = [
        c
        for c in diff.changes
        if c.change_type == TemplateChangeType.DELETED
        and not (c.should_skip and not show_skipped)
    ]
    skipped_files = [
        c
        for c in diff.changes
        if c.should_skip and c.change_type != TemplateChangeType.UNCHANGED
    ]

    if added_files:
        file_list = ", ".join([f.template_name for f in added_files[:3]])
        if len(added_files) > 3:
            file_list += f" (+{len(added_files) - 3} more)"
        table.add_row("[green]Added[/green]", str(len(added_files)), file_list)

    if modified_files:
        file_list = ", ".join([f.template_name for f in modified_files[:3]])
        if len(modified_files) > 3:
            file_list += f" (+{len(modified_files) - 3} more)"
        table.add_row("[yellow]Modified[/yellow]", str(len(modified_files)), file_list)

    if deleted_files:
        file_list = ", ".join([f.template_name for f in deleted_files[:3]])
        if len(deleted_files) > 3:
            file_list += f" (+{len(deleted_files) - 3} more)"
        table.add_row("[red]Deleted[/red]", str(len(deleted_files)), file_list)

    if skipped_files and show_skipped:
        file_list = ", ".join([f.template_name for f in skipped_files[:3]])
        if len(skipped_files) > 3:
            file_list += f" (+{len(skipped_files) - 3} more)"
        table.add_row(
            "[dim]Skipped[/dim]", str(len(skipped_files)), f"[dim]{file_list}[/dim]"
        )

    console.print(table)

    # Show detailed changes based on verbosity level
    if verbosity >= 1:  # -v: show detailed list
        console.print("\n[bold]Detailed Changes:[/bold]")

        for change in diff.changes:
            if change.change_type == TemplateChangeType.UNCHANGED:
                continue

            if change.should_skip and not show_skipped:
                continue

            color = {
                TemplateChangeType.ADDED: "green",
                TemplateChangeType.MODIFIED: "yellow",
                TemplateChangeType.DELETED: "red",
            }.get(change.change_type, "white")

            status_symbol = {
                TemplateChangeType.ADDED: "+",
                TemplateChangeType.MODIFIED: "~",
                TemplateChangeType.DELETED: "-",
            }.get(change.change_type, "?")

            skip_suffix = " [dim](skipped)[/dim]" if change.should_skip else ""

            # Basic change info
            if change.change_type == TemplateChangeType.MODIFIED:
                console.print(
                    f"  [{color}]{status_symbol}[/{color}] {change.template_name} "
                    f"[dim](+{change.lines_added}/-{change.lines_removed} lines)[/dim]{skip_suffix}"
                )
            else:
                line_count = (
                    change.lines_added
                    if change.change_type == TemplateChangeType.ADDED
                    else change.lines_removed
                )
                console.print(
                    f"  [{color}]{status_symbol}[/{color}] {change.template_name} "
                    f"[dim]({line_count} lines)[/dim]{skip_suffix}"
                )

            # Show full diff if very verbose (-vv and above)
            if verbosity >= 2:
                show_unified_diff(change)

    # Show skip notice
    if skipped_files and not show_skipped:
        console.print(
            f"\n[dim]Note: {len(skipped_files)} files will be skipped (context files, user data). Use --show-skipped to see them.[/dim]"
        )


def confirm_template_update(
    diff: TemplateDiff,
    dry_run: bool = False,
    per_file: bool = False,
    verbosity: int = 0,
) -> tuple[bool, Optional[list[str]]]:
    """Ask user to confirm template updates.

    Returns:
        Tuple of (should_proceed, selected_files).
        If per_file is True, selected_files contains the files to update.
        If per_file is False, selected_files is None and should_proceed applies to all.
    """
    if dry_run:
        console.print("\n[yellow]Dry run mode - no changes will be made[/yellow]")
        return False, None

    if not diff.has_changes:
        return False, None

    # Count actionable changes (non-skipped)
    actionable_changes = [
        c
        for c in diff.changes
        if not c.should_skip and c.change_type != TemplateChangeType.UNCHANGED
    ]

    if not actionable_changes:
        console.print("\n[yellow]All changes are skipped - nothing to update[/yellow]")
        return False, None

    if per_file:
        # Per-file selection
        console.print("\n[bold]Select files to update:[/bold]")
        selected_files = []

        for change in actionable_changes:
            if change.should_skip:
                continue

            color = {
                TemplateChangeType.ADDED: "green",
                TemplateChangeType.MODIFIED: "yellow",
                TemplateChangeType.DELETED: "red",
            }.get(change.change_type, "white")

            action = change.change_type.value.title()

            # Show file info
            if change.change_type == TemplateChangeType.MODIFIED:
                file_info = f"  [{color}]{action}[/{color}] {change.template_name} [dim](+{change.lines_added}/-{change.lines_removed} lines)[/dim]"
            else:
                line_count = (
                    change.lines_added
                    if change.change_type == TemplateChangeType.ADDED
                    else change.lines_removed
                )
                file_info = f"  [{color}]{action}[/{color}] {change.template_name} [dim]({line_count} lines)[/dim]"

            console.print(file_info)

            # Option to show diff in per-file mode
            if per_file and verbosity == 0:
                if typer.confirm("    Show diff?", default=False):
                    show_unified_diff(change)
            elif verbosity >= 2:
                # Always show diff if -vv or higher
                show_unified_diff(change)

            if typer.confirm("    Apply this change?"):
                selected_files.append(change.template_name)

            console.print()  # Add spacing between files

        if selected_files:
            console.print(
                f"\n[cyan]Selected {len(selected_files)} files for update[/cyan]"
            )
            return True, selected_files
        else:
            console.print("\n[yellow]No files selected[/yellow]")
            return False, None
    else:
        # All-or-nothing confirmation
        total_changes = len(actionable_changes)

        console.print(f"\n[bold]This will update {total_changes} files.[/bold]")
        console.print(
            "[yellow]⚠️  Warning: This will overwrite any local changes you made to these files.[/yellow]"
        )

        if typer.confirm("\nProceed with template update?"):
            return True, None
        else:
            console.print("[yellow]Operation cancelled[/yellow]")
            return False, None


def download_templates_from_source(source: str) -> Optional[Path]:
    """Download templates from various sources (GitHub, URL, local path).

    Returns:
        Path to the downloaded/extracted templates directory, or None if failed.
    """
    download_service = get_download_service()

    # Create temporary directory for download
    temp_dir = Path(tempfile.mkdtemp(prefix="specifyx_templates_"))

    try:
        if source.startswith(("http://", "https://")):
            if source.endswith(".zip"):
                # Direct ZIP URL
                console.print(f"[blue]Downloading ZIP from:[/blue] {source}")
                zip_path = temp_dir / "templates.zip"

                if download_service.download_template(source, zip_path):
                    extract_dir = temp_dir / "extracted"
                    if download_service.extract_archive(zip_path, extract_dir):
                        return extract_dir
                    else:
                        console.print("[red]Failed to extract ZIP archive[/red]")
                        return None
                else:
                    console.print("[red]Failed to download ZIP file[/red]")
                    return None
            else:
                # GitHub repository URL
                console.print(f"[blue]Downloading from GitHub:[/blue] {source}")
                extract_dir = temp_dir / "repo"

                if download_service.download_github_repo(source, extract_dir):
                    return extract_dir
                else:
                    console.print("[red]Failed to download GitHub repository[/red]")
                    return None
        else:
            # Local file path
            source_path = Path(source).expanduser().resolve()

            if not source_path.exists():
                console.print(f"[red]Local path does not exist:[/red] {source_path}")
                return None

            if source_path.is_file():
                # ZIP file
                if source_path.suffix.lower() == ".zip":
                    console.print(f"[blue]Extracting local ZIP:[/blue] {source_path}")
                    extract_dir = temp_dir / "extracted"

                    if download_service.extract_archive(source_path, extract_dir):
                        return extract_dir
                    else:
                        console.print("[red]Failed to extract local ZIP file[/red]")
                        return None
                else:
                    console.print(
                        f"[red]Unsupported file type:[/red] {source_path.suffix}"
                    )
                    return None
            else:
                # Directory
                console.print(f"[blue]Using local directory:[/blue] {source_path}")
                copy_dir = temp_dir / "copy"
                shutil.copytree(source_path, copy_dir)
                return copy_dir

    except Exception as e:
        console.print(f"[red]Error downloading templates:[/red] {e}")
        return None


def refresh_templates_command(
    source: Optional[str] = typer.Option(
        None,
        "--source",
        "-s",
        help="Template source: GitHub URL, ZIP URL, local path, or local ZIP file (default: built-in templates)",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity (-v: detailed summary, -vv: show diffs, -vvv: debug info)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be changed without making changes"
    ),
    per_file: bool = typer.Option(
        False, "--per-file", help="Select individual files to update"
    ),
    show_skipped: bool = typer.Option(
        False, "--show-skipped", help="Show files that will be skipped during update"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompts (not compatible with --per-file)",
    ),
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        help="AI agents to include when refreshing (comma-separated): code-reviewer,documentation-reviewer,implementer,spec-reviewer,architecture-reviewer,test-reviewer (interactive multiselect if not specified)",
    ),
) -> None:
    """Refresh project templates from various sources.

    This command compares your current project files with templates from a source
    and shows you what would change. Sources can be:

    • GitHub repository: https://github.com/user/repo
    • ZIP file URL: https://example.com/templates.zip
    • Local directory: /path/to/templates
    • Local ZIP file: /path/to/templates.zip
    • Built-in templates (default)

    Templates are compared against your existing files and you can choose
    which changes to apply. Context files and user data are skipped by default.
    """
    project_path = Path.cwd()
    config_service = TomlConfigService()
    git_service = CommandLineGitService()
    project_manager = ProjectManager(
        config_service=config_service, git_service=git_service
    )
    template_service = get_template_service()

    # Check if this is a SpecifyX project
    if not project_manager.is_project_initialized(project_path):
        console.print(
            "[red]Error:[/red] This directory is not a SpecifyX project.\n"
            "Run [cyan]specify init[/cyan] first to initialize the project."
        )
        raise typer.Exit(1)

    # Validate options
    if per_file and yes:
        console.print("[red]Error:[/red] --per-file and --yes cannot be used together")
        raise typer.Exit(1)

    # Parse and validate agent types
    selected_agents: List[str] = []

    if agents is None:
        if yes:
            # Use default agents when --yes flag is used
            selected_agents = ["code-reviewer", "implementer", "test-reviewer"]
        else:
            try:
                selected_agents = multiselect_agent_types()
            except KeyboardInterrupt:
                console.print("[yellow]Template refresh cancelled[/yellow]")
                raise typer.Exit(0) from None
    else:
        # Parse comma-separated list
        selected_agents = [name.strip() for name in agents.split(",")]

    # Validate agent choices using template registry
    validation_result = TEMPLATE_REGISTRY.validate_selections(
        "agent-prompts", selected_agents
    )

    if not validation_result.is_valid:
        valid_agents = TEMPLATE_REGISTRY.get_template_names("agent-prompts")
        console.print(
            f"[red]Error:[/red] Invalid agent(s): {', '.join(validation_result.invalid_templates)}. Choose from: {', '.join(valid_agents)}"
        )
        raise typer.Exit(1)

    if validation_result.has_warnings:
        for warning in validation_result.warnings:
            console.print(f"[yellow]Warning:[/yellow] {warning}")

    console.print(
        Panel.fit(
            f"[bold cyan]Refreshing Templates[/bold cyan]\n"
            f"Project: [green]{project_path.name}[/green]\n"
            f"Source: [yellow]{source or 'built-in templates'}[/yellow]",
            border_style="cyan",
        )
    )

    # Download templates from source
    template_dir = None
    if source:
        template_dir = download_templates_from_source(source)
        if not template_dir:
            console.print("[red]Failed to download templates from source[/red]")
            raise typer.Exit(1)

    try:
        # Compare templates
        console.print("\n[blue]Analyzing template differences...[/blue]")

        if verbose >= 3:  # -vvv: debug info
            console.print(
                f"[dim]Debug: Template source: {template_dir or 'built-in'}[/dim]"
            )
            console.print(f"[dim]Debug: Project path: {project_path}[/dim]")

        diff = template_service.compare_templates(
            project_path, template_dir, selected_agents
        )

        # Show diff
        show_template_diff(diff, verbosity=verbose, show_skipped=show_skipped)

        # Get confirmation and apply changes
        if diff.has_changes:
            should_proceed, selected_files = confirm_template_update(
                diff, dry_run=dry_run, per_file=per_file, verbosity=verbose
            )

            if should_proceed and not dry_run:
                # Apply the updates
                console.print("\n[blue]Applying template updates...[/blue]")

                # Implement actual file updates
                files_updated = 0
                files_skipped = 0

                for change in diff.changes:
                    # Skip if per_file mode and file not selected
                    if (
                        per_file
                        and selected_files
                        and change.template_name not in selected_files
                    ):
                        files_skipped += 1
                        continue

                    # Skip files marked as should_skip
                    if change.should_skip:
                        files_skipped += 1
                        continue

                    try:
                        if (
                            change.change_type == TemplateChangeType.ADDED
                            or change.change_type == TemplateChangeType.MODIFIED
                        ):
                            # Write new content to file
                            output_path = project_path / change.template_name
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            output_path.write_text(
                                change.new_content or "", encoding="utf-8"
                            )

                            # Make Python scripts executable
                            if output_path.suffix == ".py":
                                output_path.chmod(0o755)

                            files_updated += 1
                            if verbose >= 1:
                                console.print(
                                    f"  [green]✓[/green] {change.change_type.value.title()}: {change.template_name}"
                                )

                        elif change.change_type == TemplateChangeType.DELETED:
                            # Delete file
                            output_path = project_path / change.template_name
                            if output_path.exists():
                                output_path.unlink()
                                files_updated += 1
                                if verbose >= 1:
                                    console.print(
                                        f"  [red]✗[/red] Deleted: {change.template_name}"
                                    )

                    except Exception as e:
                        console.print(
                            f"  [red]Error updating {change.template_name}: {e}[/red]"
                        )
                        continue

                console.print("[green]✓[/green] Template refresh completed!")

                if files_updated > 0:
                    console.print(f"Updated {files_updated} files")
                if files_skipped > 0:
                    console.print(f"Skipped {files_skipped} files")

    finally:
        # Clean up temporary directory
        if template_dir and template_dir.exists():
            shutil.rmtree(template_dir, ignore_errors=True)

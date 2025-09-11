"""Project management commands using services and enhanced UI."""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from specify_cli.models.defaults import AI_DEFAULTS, BRANCH_DEFAULTS
from specify_cli.models.project import ProjectInitOptions
from specify_cli.services import (
    CommandLineGitService,
    TomlConfigService,
)
from specify_cli.services.project_manager import ProjectManager
from specify_cli.utils.ui import StepTracker
from specify_cli.utils.ui_helpers import (
    select_ai_assistant,
    select_branch_naming_pattern,
)


# Initialize services
def get_project_manager():
    """Factory function to create ProjectManager with all dependencies."""
    config_service = TomlConfigService()
    git_service = CommandLineGitService()

    return ProjectManager(
        config_service=config_service,
        git_service=git_service,
    )


def init_command(
    project_name: Optional[str] = typer.Argument(
        None, help="Name for your new project directory (optional if using --here)"
    ),
    ai_assistant: Optional[str] = typer.Option(
        None,
        "--ai",
        help=f"AI assistant to use: {', '.join([assistant.name for assistant in AI_DEFAULTS.ASSISTANTS])} (interactive if not specified)",
    ),
    branch_pattern: Optional[str] = typer.Option(
        None,
        "--branch-pattern",
        help="Branch naming pattern: '001-feature-name' or 'feature/{name}' (interactive if not specified)",
    ),
    here: bool = typer.Option(
        False,
        "--here",
        help="Initialize project in the current directory instead of creating a new one",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output during template rendering"
    ),
    use_remote: bool = typer.Option(
        False,
        "--use-remote",
        help="Force download templates from remote repository instead of using local ones",
    ),
    remote_repo: Optional[str] = typer.Option(
        None,
        "--remote-repo",
        help="GitHub repository for templates in format 'owner/repo' (default: barisgit/spec-kit-improved)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force initialization even if directory is already initialized",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Use defaults for all options not provided and skip interactive prompts",
    ),
):
    """
    Initialize a new SpecifyX project using the modular service architecture.

    This command uses the ProjectManager service to orchestrate:
    - Project structure creation
    - Template rendering with Jinja2
    - Git repository initialization
    - Configuration management with TOML
    """
    from specify_cli.core.app import console, show_banner

    # Show banner
    show_banner()

    # Validate arguments
    if here and project_name:
        console.print(
            "[red]Error:[/red] Cannot specify both project name and --here flag"
        )
        raise typer.Exit(1)

    if not here and not project_name:
        console.print(
            "[red]Error:[/red] Must specify either a project name or use --here flag"
        )
        raise typer.Exit(1)

    # Early check for already initialized directory
    if here and not force:
        project_manager = get_project_manager()
        current_path = Path.cwd()
        if project_manager.is_project_initialized(current_path):
            console.print(
                "[yellow]Directory is already initialized as a SpecifyX project.[/yellow]"
            )
            console.print(f"[dim]Location:[/dim] {current_path}")
            console.print(
                "\nUse [cyan]--force[/cyan] to reinitialize or choose a different directory."
            )
            raise typer.Exit(0)

    # Determine project path (for display only; manager derives it from options)
    if here:
        display_project_name = Path.cwd().name
        project_path = Path.cwd()
    else:
        # project_name is asserted below
        display_project_name = project_name or ""
        project_path = (
            Path.cwd() / display_project_name if display_project_name else Path.cwd()
        )

    # Check if project already exists
    if not here and project_path.exists():
        console.print(f"[red]Error:[/red] Directory '{project_name}' already exists")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "[bold cyan]SpecifyX Project Setup[/bold cyan]\n"
            f"{'Initializing in current directory:' if here else 'Creating new project:'} [green]{project_path.name}[/green]"
            + (f"\n[dim]Path: {project_path}[/dim]" if here else ""),
            border_style="cyan",
        )
    )

    # Interactive AI assistant selection if not specified
    if ai_assistant is None:
        if yes:
            # Use default AI assistant when --yes flag is used
            ai_assistant = AI_DEFAULTS.ASSISTANTS[0].name  # First assistant as default
        else:
            try:
                ai_assistant = select_ai_assistant()
            except KeyboardInterrupt:
                console.print("[yellow]Setup cancelled[/yellow]")
                raise typer.Exit(0) from None

    # Validate AI assistant choice using AI_DEFAULTS
    valid_assistants = [assistant.name for assistant in AI_DEFAULTS.ASSISTANTS]
    if ai_assistant not in valid_assistants:
        console.print(
            f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(valid_assistants)}"
        )
        raise typer.Exit(1)

    # Interactive template source selection if not specified via flags
    if not use_remote and remote_repo is None:
        if yes:
            # Use default template source when --yes flag is used (local templates)
            use_remote = False
            remote_repo = None
        else:
            try:
                from specify_cli.utils.ui_helpers import select_template_source

                interactive_use_remote, interactive_remote_repo = (
                    select_template_source()
                )
                use_remote = interactive_use_remote
                remote_repo = interactive_remote_repo
            except KeyboardInterrupt:
                console.print("[yellow]Setup cancelled[/yellow]")
                raise typer.Exit(0) from None

    # Interactive branch pattern selection if not specified
    branch_naming_config = None
    if branch_pattern is None:
        if yes:
            # Use default branch pattern when --yes flag is used
            branch_pattern = BRANCH_DEFAULTS.DEFAULT_PATTERN_NAME
        else:
            try:
                branch_naming_config = select_branch_naming_pattern()
                # Get the selected pattern name from the config
                # The select_branch_naming_pattern returns a config object,
                # we need to map it back to the pattern name for legacy compatibility
                for pattern in BRANCH_DEFAULTS.PATTERNS:
                    if (
                        branch_naming_config.patterns == pattern.patterns
                        and branch_naming_config.description == pattern.description
                    ):
                        branch_pattern = pattern.name
                        break
                else:
                    # Fallback if no match found
                    branch_pattern = BRANCH_DEFAULTS.DEFAULT_PATTERN_NAME
            except KeyboardInterrupt:
                console.print("[yellow]Setup cancelled[/yellow]")
                raise typer.Exit(0) from None

    # Validate branch pattern using centralized system
    valid_patterns = BRANCH_DEFAULTS.get_all_pattern_names()
    if branch_pattern not in valid_patterns:
        console.print(
            f"[red]Error:[/red] Invalid branch pattern '{branch_pattern}'. Choose from: {', '.join(valid_patterns)}"
        )
        raise typer.Exit(1)

    # Get project manager
    project_manager = get_project_manager()

    # Use StepTracker for enhanced progress display
    with StepTracker.create_default("SpecifyX Project Setup") as tracker:
        try:
            tracker.add_step("validate", "Validate project settings")
            tracker.start_step("validate")

            # Build options for project initialization
            options = ProjectInitOptions(
                project_name=project_name if not here else None,
                ai_assistant=ai_assistant,
                use_current_dir=here,
                skip_git=False,
                branch_pattern=branch_pattern,
                branch_naming_config=branch_naming_config,
                force=force,
            )
            tracker.complete_step(
                "validate", f"AI: {ai_assistant}, Pattern: {branch_pattern}"
            )

            tracker.add_step("initialize", "Initialize project structure")
            tracker.start_step("initialize")

            result = project_manager.initialize_project(options)

            # Check if initialization was successful
            # Consider it successful if templates were rendered, even with minor warnings
            from specify_cli.models.project import ProjectInitStep

            templates_rendered = (
                result
                and hasattr(result, "completed_steps")
                and ProjectInitStep.TEMPLATE_RENDER in result.completed_steps
            )

            if result and templates_rendered and not use_remote:
                tracker.complete_step("initialize", "Project created successfully")

                tracker.add_step("finalize", "Finalize setup")
                tracker.start_step("finalize")
                tracker.complete_step("finalize", "Ready to use!")
            else:
                # Either template rendering failed or user requested remote templates
                reason = (
                    "Using remote templates (--use-remote)"
                    if use_remote
                    else "Local templates failed, using fallback"
                )
                if (
                    result
                    and hasattr(result, "warnings")
                    and result.warnings
                    and not use_remote
                ):
                    console.print(
                        f"[yellow]Template warnings:[/yellow] {len(result.warnings)} issues"
                    )
                    for warning in result.warnings[:3]:  # Show first 3 warnings
                        console.print(f"  • {warning}")

                # Debug: Show why local templates failed
                if not use_remote and result:
                    console.print(
                        f"[dim]Debug - Local template failure reason: {getattr(result, 'error_message', 'Unknown')}[/dim]"
                    )

                tracker.error_step(
                    "initialize", reason
                ) if not use_remote else tracker.complete_step("initialize", reason)
                tracker.add_step("download-remote", "Download templates from GitHub")
                tracker.start_step("download-remote")

                try:
                    import tempfile

                    from specify_cli.services.download_service import (
                        HttpxDownloadService,
                    )
                    from specify_cli.services.template_service import (
                        get_template_service,
                    )

                    # Parse remote repo option
                    repo_owner, repo_name = "barisgit", "spec-kit-improved"
                    if remote_repo:
                        if "/" in remote_repo:
                            repo_owner, repo_name = remote_repo.split("/", 1)
                        else:
                            console.print(
                                f"[yellow]Warning:[/yellow] Invalid remote-repo format '{remote_repo}', using default"
                            )

                    download_service = HttpxDownloadService(
                        default_repo_owner=repo_owner,
                        default_repo_name=repo_name,
                        console=console,
                    )

                    # Download templates to a temporary directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        success, metadata = (
                            download_service.download_github_release_template(
                                ai_assistant, temp_path
                            )
                        )

                        if success and metadata:
                            # Extract the ZIP file
                            zip_path = temp_path / metadata["filename"]
                            extract_path = temp_path / "extracted"

                            if download_service.extract_archive(zip_path, extract_path):
                                tracker.complete_step(
                                    "download-remote",
                                    f"Templates downloaded: {metadata['filename']}",
                                )

                                # Now render templates using the template service
                                tracker.add_step(
                                    "render-remote", "Process remote templates"
                                )
                                tracker.start_step("render-remote")

                                template_service = get_template_service()
                                template_result = template_service.render_templates(
                                    templates_path=extract_path,
                                    destination_path=project_path,
                                    ai_assistant=ai_assistant,
                                    project_name=project_name or project_path.name,
                                    branch_pattern=branch_pattern,
                                )

                                if template_result and template_result.success:
                                    tracker.complete_step(
                                        "render-remote",
                                        "Remote templates processed successfully",
                                    )

                                    tracker.add_step("finalize", "Finalize setup")
                                    tracker.start_step("finalize")
                                    tracker.complete_step("finalize", "Ready to use!")
                                    result = template_result  # Use the template result
                                else:
                                    tracker.error_step(
                                        "render-remote",
                                        "Failed to process remote templates",
                                    )
                                    raise typer.Exit(1)
                            else:
                                tracker.error_step(
                                    "download-remote",
                                    "Failed to extract remote templates",
                                )
                                raise typer.Exit(1)
                        else:
                            tracker.error_step(
                                "download-remote", "Remote download failed"
                            )
                            raise typer.Exit(1)

                except Exception as download_error:
                    error_msg = str(download_error)

                    # Provide user-friendly error messages for common issues
                    if "404 Not Found" in error_msg:
                        if remote_repo and remote_repo != "barisgit/spec-kit-improved":
                            user_friendly_error = f"Repository '{remote_repo}' not found or has no releases"
                            suggestion = "Please check the repository name and ensure it has published releases"
                        else:
                            user_friendly_error = "Default repository not accessible"
                            suggestion = "Please check your internet connection"
                    elif "403 Forbidden" in error_msg:
                        user_friendly_error = "Access denied to repository"
                        suggestion = "Repository may be private or rate limit exceeded"
                    elif (
                        "timeout" in error_msg.lower()
                        or "connection" in error_msg.lower()
                    ):
                        user_friendly_error = "Network connection failed"
                        suggestion = (
                            "Please check your internet connection and try again"
                        )
                    else:
                        user_friendly_error = f"Download failed: {error_msg}"
                        suggestion = "Please try again or use embedded templates"

                    tracker.error_step("download-remote", user_friendly_error)

                    if not use_remote:
                        # This was a fallback attempt, show both errors
                        console.print("[red]Template initialization failed![/red]")
                        console.print(
                            f"[yellow]Local templates:[/yellow] {getattr(result, 'errors', ['Unknown error'])[0] if result and hasattr(result, 'errors') and result.errors else 'Failed to render'}"
                        )
                        console.print(
                            f"[yellow]Remote fallback:[/yellow] {user_friendly_error}"
                        )
                        console.print(f"\n[blue]Suggestion:[/blue] {suggestion}")
                    else:
                        # User explicitly chose remote, offer fallback to embedded
                        console.print("[red]Remote template download failed![/red]")
                        console.print(f"[yellow]Error:[/yellow] {user_friendly_error}")
                        console.print(f"[blue]Suggestion:[/blue] {suggestion}")

                        # Ask if user wants to fallback to embedded templates
                        console.print(
                            "\n[bold]Would you like to use embedded templates instead?[/bold]"
                        )
                        console.print(
                            "[dim]This will use the templates packaged with SpecifyX (offline, faster)[/dim]"
                        )

                        try:
                            fallback_choice = (
                                input("\nUse embedded templates? [Y/n]: ")
                                .strip()
                                .lower()
                            )
                            if fallback_choice in ["", "y", "yes"]:
                                console.print(
                                    "[green]Switching to embedded templates...[/green]"
                                )

                                # Try with embedded templates
                                tracker.add_step(
                                    "fallback-embedded", "Using embedded templates"
                                )
                                tracker.start_step("fallback-embedded")

                                # Reset the use_remote flag and try again with project manager
                                fallback_result = project_manager.initialize_project(
                                    options
                                )

                                if fallback_result and fallback_result.success:
                                    tracker.complete_step(
                                        "fallback-embedded",
                                        "Embedded templates successful",
                                    )

                                    tracker.add_step("finalize", "Finalize setup")
                                    tracker.start_step("finalize")
                                    tracker.complete_step("finalize", "Ready to use!")

                                    console.print(
                                        "\n[green]✓ Project initialized successfully using embedded templates![/green]"
                                    )
                                    return
                                else:
                                    tracker.error_step(
                                        "fallback-embedded",
                                        "Embedded templates also failed",
                                    )
                                    console.print(
                                        "[red]Both remote and embedded templates failed![/red]"
                                    )
                            else:
                                console.print(
                                    "[yellow]Setup cancelled. You can try again later.[/yellow]"
                                )
                        except KeyboardInterrupt:
                            console.print("\n[yellow]Setup cancelled.[/yellow]")

                    raise typer.Exit(1) from download_error

        except Exception as e:
            if "tracker" in locals():
                tracker.error_step("initialize", f"Error: {e}")
            console.print(f"[red]Error during project initialization:[/red] {e}")
            raise typer.Exit(1) from e

    # Show next steps (outside the context manager so tracker is displayed)
    if result:
        console.print("\n[bold green]✓ Project initialized successfully![/bold green]")

        # Show warnings if any occurred during initialization
        if hasattr(result, "warnings") and result.warnings:
            console.print("\n[yellow]⚠ Warnings during initialization:[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")

        # Show next steps with enhanced formatting
        steps_lines = []
        if not here:
            steps_lines.append(f"1. [bold green]cd {project_name}[/bold green]")
            step_num = 2
        else:
            steps_lines.append("1. You're already in the project directory!")
            step_num = 2

        # Add AI-specific guidance
        if ai_assistant == "claude":
            steps_lines.append(
                f"{step_num}. Open in VS Code and use / commands with Claude Code"
            )
            steps_lines.append("   • Type / in any file to see available commands")
            steps_lines.append("   • Use /specify to create specifications")
        elif ai_assistant == "gemini":
            steps_lines.append(f"{step_num}. Use Gemini CLI for development")
            steps_lines.append("   • Run gemini /specify for specifications")
        elif ai_assistant == "copilot":
            steps_lines.append(f"{step_num}. Use GitHub Copilot in your IDE")
            steps_lines.append("   • Use /specify, /plan, /tasks commands")

        steps_lines.append(
            f"{step_num + 1}. Update [bold magenta]CONSTITUTION.md[/bold magenta] with your project's principles"
        )

        steps_panel = Panel(
            "\n".join(steps_lines),
            title="Next steps",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print(steps_panel)

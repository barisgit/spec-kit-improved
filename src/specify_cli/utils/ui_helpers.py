"""UI helper functions for interactive project initialization."""

from pathlib import Path
from typing import Dict, Optional, Tuple

from specify_cli.assistants import get_all_assistants
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.defaults import BRANCH_DEFAULTS

from .ui.interactive_ui import InteractiveUI

# Branch naming pattern selection using configurable defaults


def select_branch_naming_pattern() -> BranchNamingConfig:
    """
    Interactive selection of branch naming patterns.

    Presents the 4 default branch naming options from the data model specification
    and returns the selected BranchNamingConfig object.

    Returns:
        BranchNamingConfig: The selected branch naming configuration

    Raises:
        KeyboardInterrupt: If user cancels selection
    """
    ui = InteractiveUI()

    # Get branch naming options from configuration system
    pattern_options = BRANCH_DEFAULTS.get_pattern_options_for_ui()

    # Create choices dict with key -> display mapping for UI
    choices: Dict[str, str] = {}
    for key, config in pattern_options.items():
        patterns_text = ", ".join(config["patterns"])
        display_text = f"{config['display']}\n[dim]Patterns: {patterns_text}[/dim]"
        choices[key] = display_text

    # Create header text for panel content only
    header_text = (
        "Choose how your project will name branches for features, hotfixes, and releases.\n\n"
        "[dim]Note: You can customize patterns later in .specify/config.toml[/dim]"
    )

    try:
        selected_key = ui.select(
            "Select your preferred branch naming pattern:",
            choices=choices,
            default=BRANCH_DEFAULTS.DEFAULT_PATTERN_NAME,
            header=header_text,
        )

        # Get the selected configuration
        selected_config = pattern_options[selected_key]

        # Return BranchNamingConfig object with selected options
        return BranchNamingConfig(
            description=selected_config["description"],
            patterns=selected_config["patterns"],
            validation_rules=selected_config["validation_rules"],
        )

    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise


def select_ai_assistant() -> str:
    """
    Interactive selection of AI assistant.

    Returns:
        str: The selected AI assistant name

    Raises:
        KeyboardInterrupt: If user cancels selection
    """
    ui = InteractiveUI()

    # Use the new assistant registry
    assistants = get_all_assistants()

    # Create choices dict from registry
    ai_choices = {
        assistant.config.name: f"{assistant.config.display_name} ({assistant.config.description})"
        for assistant in assistants
    }

    # Get default (first assistant name)
    default_assistant = assistants[0].config.name if assistants else "claude"

    # Create header text for panel content only
    header_text = (
        "Select your preferred AI assistant for code generation and project guidance.\n\n"
        "[dim]This will configure templates and commands for your chosen assistant.[/dim]"
    )

    try:
        return ui.select(
            "Choose your AI assistant:",
            choices=ai_choices,
            default=default_assistant,
            header=header_text,
        )
    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise


def select_ai_assistant_for_add(project_path: Path) -> str:
    """
    Interactive selection of AI assistant for add-ai command.
    Shows status indicators for already configured assistants.

    Args:
        project_path: Path to the project directory

    Returns:
        str: The selected AI assistant name

    Raises:
        KeyboardInterrupt: If user cancels selection
    """
    from specify_cli.services.assistant_management_service.assistant_management_service import (
        AssistantManagementService,
    )
    from specify_cli.services.project_manager import ProjectManager

    ui = InteractiveUI()

    # Create assistant management service for status checking
    project_manager = ProjectManager()
    assistant_service = AssistantManagementService(project_manager)

    # Use the new assistant registry
    assistants = get_all_assistants()

    # Create choices dict with status indicators
    ai_choices = {}
    available_assistants = []

    for assistant in assistants:
        status = assistant_service.check_assistant_status(
            project_path, assistant.config.name
        )

        if status == "configured":
            # Dim already configured assistants
            display_text = (
                f"[dim]{assistant.config.display_name} (already configured)[/dim]"
            )
            # Still add to choices but make it less appealing
            ai_choices[assistant.config.name] = display_text
        else:
            # Show available assistants normally
            status_text = (
                "⚠️  partially configured" if status == "partial" else "not configured"
            )
            display_text = f"{assistant.config.display_name} ({status_text})"
            ai_choices[assistant.config.name] = display_text
            available_assistants.append(assistant.config.name)

    # Default to first available (non-configured) assistant
    default_assistant = (
        available_assistants[0] if available_assistants else assistants[0].config.name
    )

    # Create header text
    header_text = (
        "Select an AI assistant to add to your project.\n\n"
        "[dim]Already configured assistants are shown dimmed.[/dim]"
    )

    try:
        return ui.select(
            "Choose AI assistant to add:",
            choices=ai_choices,
            default=default_assistant,
            header=header_text,
        )
    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise


def multiselect_ai_assistants() -> list[str]:
    """
    Interactive multi-selection of AI assistants for init command.

    Returns:
        list[str]: List of selected AI assistant names

    Raises:
        KeyboardInterrupt: If user cancels selection
    """
    ui = InteractiveUI()

    # Use the new assistant registry
    assistants = get_all_assistants()

    # Create choices dict from registry
    ai_choices = {
        assistant.config.name: f"{assistant.config.display_name} ({assistant.config.description})"
        for assistant in assistants
    }

    # Default to first assistant selected
    default_selection = [assistants[0].config.name] if assistants else []

    # Create header text
    header_text = (
        "Select one or more AI assistants for your project.\n\n"
        "[dim]You can always add more assistants later with 'specify add-ai'.[/dim]"
    )

    try:
        return ui.multiselect(
            "Choose AI assistants:",
            choices=ai_choices,
            default=default_selection,
            min_selections=1,  # Require at least one assistant
            header=header_text,
        )
    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise


def multiselect_agent_types() -> list[str]:
    """
    Interactive multi-selection of agent types for project initialization.

    Returns:
        list[str]: List of selected agent type names (without .md.j2 extension)

    Raises:
        KeyboardInterrupt: If user cancels selection
    """
    ui = InteractiveUI()

    # Available agent types with descriptions
    agent_choices = {
        "code-reviewer": "Code Reviewer\n[dim]Reviews code quality, type safety, and professional standards[/dim]",
        "documentation-reviewer": "Documentation Reviewer\n[dim]Reviews documentation quality, completeness, and accuracy[/dim]",
        "implementer": "Implementer\n[dim]Handles systematic feature implementation using TDD principles[/dim]",
        "spec-reviewer": "Spec Reviewer\n[dim]Reviews specifications for completeness and feasibility[/dim]",
        "architecture-reviewer": "Architecture Reviewer\n[dim]Reviews system architecture and design patterns[/dim]",
        "test-reviewer": "Test Reviewer\n[dim]Reviews test coverage, quality, and testing strategies[/dim]",
    }

    # Default to commonly used agents
    default_selection = ["code-reviewer", "implementer", "test-reviewer"]

    # Create header text
    header_text = (
        "Select which AI agents to include in your project. Agents provide specialized assistance for different development tasks.\n\n"
        "[dim]You can generate additional agents later using the scaffold-agent script.[/dim]"
    )

    try:
        return ui.multiselect(
            "Choose AI agents:",
            choices=agent_choices,
            default=default_selection,
            min_selections=0,  # Allow no agents if user prefers
            header=header_text,
        )
    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise


def select_template_source() -> Tuple[bool, Optional[str]]:
    """
    Interactive selection of template source (embedded vs remote).

    Returns:
        Tuple[bool, Optional[str]]: (use_remote, remote_repo)
            - use_remote: True if remote templates should be used
            - remote_repo: Repository string in "owner/repo" format or None for default

    Raises:
        KeyboardInterrupt: If user cancels selection
    """
    from rich.console import Console

    console = Console()
    ui = InteractiveUI()

    # Template source choices
    source_choices = {
        "embedded": "Embedded Templates\n[dim]Use templates packaged with SpecifyX (faster, offline)[/dim]",
        "remote": "Remote Templates\n[dim]Download latest templates from GitHub repository[/dim]",
    }

    # Create header text for panel content only
    header_text = (
        "Choose whether to use embedded templates (faster) or download from remote repository (latest).\n\n"
        "[dim]Remote templates may have newer features and fixes.[/dim]"
    )

    try:
        # First choice: embedded vs remote
        source_choice = ui.select(
            "Choose template source:",
            choices=source_choices,
            default="embedded",
            header=header_text,
        )

        use_remote = source_choice == "remote"
        remote_repo = None

        if use_remote:
            # Second choice: default repo vs custom repo
            repo_choices = {
                "default": "Default Repository\n[dim]barisgit/spec-kit-improved (recommended)[/dim]",
                "custom": "Custom Repository\n[dim]Specify your own GitHub repository[/dim]",
            }

            repo_choice = ui.select(
                "Choose repository:", choices=repo_choices, default="default"
            )

            if repo_choice == "custom":
                console.print("\n[bold]Custom Repository[/bold]")
                console.print("Enter GitHub repository in 'owner/repo' format:")
                console.print("[dim]Example: myusername/my-templates[/dim]")

                while True:
                    try:
                        custom_repo = input("\nRepository (owner/repo): ").strip()
                        if not custom_repo:
                            console.print(
                                "[yellow]Repository cannot be empty. Try again or press Ctrl+C to cancel.[/yellow]"
                            )
                            continue
                        elif "/" not in custom_repo:
                            console.print(
                                "[yellow]Invalid format. Please use 'owner/repo' format.[/yellow]"
                            )
                            continue
                        else:
                            remote_repo = custom_repo
                            console.print(
                                f"Using custom repository: [green]{custom_repo}[/green]"
                            )
                            break
                    except KeyboardInterrupt:
                        console.print(
                            "\n[yellow]Cancelled. Using default repository.[/yellow]"
                        )
                        break

        return use_remote, remote_repo

    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise

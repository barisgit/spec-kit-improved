"""UI helper functions for interactive project initialization."""

from typing import Dict, Optional, Tuple

from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.defaults import AI_DEFAULTS, BRANCH_DEFAULTS

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
        str: The selected AI assistant ("claude", "gemini", or "copilot")

    Raises:
        KeyboardInterrupt: If user cancels selection
    """
    ui = InteractiveUI()

    # Use configurable AI assistant choices from AI_DEFAULTS
    ai_choices = {
        assistant.name: f"{assistant.display_name} ({assistant.description})"
        for assistant in AI_DEFAULTS.ASSISTANTS
    }

    # Create header text for panel content only
    header_text = (
        "Select your preferred AI assistant for code generation and project guidance.\n\n"
        "[dim]This will configure templates and commands for your chosen assistant.[/dim]"
    )

    try:
        return ui.select(
            "Choose your AI assistant:",
            choices=ai_choices,
            default="claude",
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

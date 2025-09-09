"""UI helper functions for interactive project initialization."""

from typing import Dict

from ..models.config import BranchNamingConfig
from .ui.interactive_ui import InteractiveUI

# FIXME: This whole file should be more dynamic with base UI select with content and choices as inputs


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
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    ui = InteractiveUI()

    # Show explanatory information
    # TODO: Improve ui to add this into same panel as the choices
    info_text = (
        "[bold cyan]Branch Naming Configuration[/bold cyan]\n\n"
        "Choose how your project will name branches for features, hotfixes, and releases.\n\n"
        "[dim]Note: You can customize patterns later in .specify/config.toml[/dim]"
    )

    console.print(Panel(info_text, border_style="cyan", padding=(1, 2)))
    console.print()  # Add spacing

    # Define the 4 branch naming options with short names and clear descriptions
    # TODO: Use strong typing
    pattern_options = {
        "traditional-spec": {
            "description": "Traditional numbered branches with hotfixes",
            "display": "Traditional numbered branches with hotfixes",
            "patterns": [
                "{spec-id}-{feature-name}",
                "hotfix/{bug-id}",
                "main",
                "development",
            ],
            "validation_rules": [
                "max_length_50",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_slash_only",
            ],
        },
        "branch-type": {
            "description": "Modern namespaced branches with type prefixes",
            "display": "Modern namespaced branches with type prefixes",
            "patterns": [
                "feature/{feature-name}",
                "hotfix/{bug-id}",
                "bugfix/{bug-id}",
                "main",
                "development",
            ],
            "validation_rules": [
                "max_length_50",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_slash_only",
            ],
        },
        "numbered-type": {
            "description": "Numbered branches with organized type prefixes",
            "display": "Numbered branches with organized type prefixes",
            "patterns": [
                "feature/{spec-id}-{feature-name}",
                "hotfix/{bug-id}",
                "release/{version}",
                "main",
                "development",
            ],
            "validation_rules": [
                "max_length_50",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_slash_only",
            ],
        },
        "team-based": {
            "description": "Team-based organization with workflow support",
            "display": "Team-based organization with workflow support",
            "patterns": [
                "{team}/{feature-name}",
                "hotfix/{bug-id}",
                "release/{version}",
                "main",
                "development",
            ],
            "validation_rules": [
                "max_length_60",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_slash_only",
            ],
        },
    }

    # Create choices dict with key -> display mapping for UI
    choices: Dict[str, str] = {}
    for key, config in pattern_options.items():
        patterns_text = ", ".join(config["patterns"])
        display_text = f"{config['display']}\n[dim]Patterns: {patterns_text}[/dim]"
        choices[key] = display_text

    try:
        selected_key = ui.select(
            "Select your preferred branch naming pattern:",
            choices=choices,
            default="traditional-spec",  # Default to traditional format
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

    ai_choices = {
        # FIXME: HARDCODED - AI assistant choices hardcoded
        # TODO: Make configurable via configuration system
        "claude": "Claude Code (Terminal-based AI assistant with / commands)",
        "gemini": "Gemini CLI (Terminal-based AI assistant)",
        "copilot": "GitHub Copilot (VS Code/IDE integration)",
    }

    try:
        return ui.select(
            "Choose your AI assistant:", choices=ai_choices, default="claude"
        )
    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise

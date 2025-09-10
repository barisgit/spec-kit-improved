"""UI helper functions for interactive project initialization."""

from typing import Dict

from ..models.config import BranchNamingConfig
from ..models.defaults import AI_DEFAULTS, BRANCH_DEFAULTS
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

    # Get branch naming options from configuration system
    pattern_options = BRANCH_DEFAULTS.get_pattern_options_for_ui()

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
            default=BRANCH_DEFAULTS.DEFAULT_PATTERN_NAME,  # Use configurable default
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

    try:
        return ui.select(
            "Choose your AI assistant:", choices=ai_choices, default="claude"
        )
    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise

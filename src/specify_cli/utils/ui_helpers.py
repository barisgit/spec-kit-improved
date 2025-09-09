"""UI helper functions for interactive project initialization."""

from typing import Dict

from ..models.config import BranchNamingConfig
from .ui.interactive_ui import InteractiveUI


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
    
    # Define the 4 branch naming options from data model specification
    pattern_options = {
        "001-feature-name": {
            "description": "Traditional numbered branches with hotfixes and main branches",
            "display": "Traditional numbered format (001-auth-system)",
            "patterns": ["{number-3}-{feature-name}", "hotfix/{bug-id}", "main", "development"],
            "validation_rules": ["max_length_50", "lowercase_only", "no_spaces", "alphanumeric_dash_only"]
        },
        "feature/{name}": {
            "description": "Modern feature branches with hotfixes and main branches", 
            "display": "Modern branch format (feature/auth-system)",
            "patterns": ["feature/{feature-name}", "hotfix/{bug-id}", "bugfix/{bug-id}", "main", "development"],
            "validation_rules": ["max_length_50", "lowercase_only", "no_spaces", "alphanumeric_dash_only"]
        },
        "feature/{number-3}-{name}": {
            "description": "Numbered feature branches with organized prefixes",
            "display": "Numbered feature branch format (feature/001-auth-system)", 
            "patterns": ["feature/{number-3}-{feature-name}", "hotfix/{bug-id}", "release/{version}", "main", "development"],
            "validation_rules": ["max_length_50", "lowercase_only", "no_spaces", "alphanumeric_dash_only"]
        },
        "{team}/{name}": {
            "description": "Team-based branches with workflow support",
            "display": "Team-based branches (frontend/auth-system)",
            "patterns": ["{team}/{feature-name}", "hotfix/{bug-id}", "release/{version}", "main", "development"], 
            "validation_rules": ["max_length_60", "lowercase_only", "no_spaces", "alphanumeric_dash_slash_only"]
        }
    }
    
    # Create choices dict with key -> display mapping for UI
    choices: Dict[str, str] = {}
    for key, config in pattern_options.items():
        choices[key] = config["display"]
    
    try:
        selected_key = ui.select(
            "Choose your branch naming pattern:",
            choices=choices,
            default="001-feature-name"  # Default to traditional format
        )
        
        # Get the selected configuration
        selected_config = pattern_options[selected_key]
        
        # Return BranchNamingConfig object with selected options
        return BranchNamingConfig(
            description=selected_config["description"],
            patterns=selected_config["patterns"],
            validation_rules=selected_config["validation_rules"]
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
        "claude": "Claude Code (Terminal-based AI assistant with / commands)",
        "gemini": "Gemini CLI (Terminal-based AI assistant)", 
        "copilot": "GitHub Copilot (VS Code/IDE integration)",
    }
    
    try:
        return ui.select(
            "Choose your AI assistant:",
            choices=ai_choices,
            default="claude"
        )
    except KeyboardInterrupt:
        # Re-raise to allow caller to handle cancellation
        raise
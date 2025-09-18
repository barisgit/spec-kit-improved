"""
Type-safe contracts for AI assistant configuration system.

This module defines the core typed interfaces for organizing AI assistant
logic in SpecifyX without complex plugin architecture.
"""

from dataclasses import dataclass
from typing import Dict, List, Protocol


@dataclass(frozen=True)
class AssistantConfig:
    """
    Type-safe configuration for AI assistant definitions.

    This replaces the current scattered configuration approach with
    a clean, validated structure that all assistants must implement.
    """

    name: str  # Unique identifier (e.g., "claude")
    display_name: str  # Human-readable name (e.g., "Claude Code")
    description: str  # Brief description for UI
    base_directory: str  # Target directory (e.g., ".claude")
    context_file: str  # Main context file path
    commands_directory: str  # Commands directory path
    memory_directory: str  # Memory/constitution directory path

    def __post_init__(self):
        """Validate configuration on construction."""
        if not self.name or not self.name.islower():
            raise ValueError(f"Assistant name must be non-empty lowercase: {self.name}")
        if not self.base_directory.startswith("."):
            raise ValueError(
                f"Base directory must start with '.': {self.base_directory}"
            )
        if not self.display_name:
            raise ValueError("Display name cannot be empty")
        if not self.context_file or not self.commands_directory:
            raise ValueError("Context file and commands directory are required")


class InjectionProvider(Protocol):
    """
    Protocol for providing template injection points.

    Each assistant module implements this to provide clean,
    assistant-agnostic injection points for templates.
    """

    def get_injections(self) -> Dict[str, str]:
        """
        Return injection point values for template rendering.

        Returns:
            Dict mapping injection point names to their values.
            All values must be strings safe for Jinja2 templates.

        Example:
            {
                "assistant_command_prefix": "claude ",
                "assistant_setup_instructions": "Run 'claude auth'",
                "assistant_context_file_path": ".claude/CLAUDE.md"
            }
        """
        ...


class AssistantValidator(Protocol):
    """
    Protocol for validating assistant configurations.

    Provides type-safe validation for assistant configs and
    injection providers with clear error messages.
    """

    def validate_config(self, config: AssistantConfig) -> List[str]:
        """
        Validate assistant configuration structure.

        Args:
            config: Assistant configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        ...

    def validate_injections(self, provider: InjectionProvider) -> List[str]:
        """
        Validate injection provider implementation.

        Args:
            provider: Injection provider to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        ...


class DocumentationGenerator(Protocol):
    """
    Protocol for auto-generating assistant documentation.

    Generates documentation from typed assistant definitions
    to keep docs current with code changes.
    """

    def generate_assistant_list(self, assistants: List[AssistantConfig]) -> str:
        """
        Generate markdown list of available assistants.

        Args:
            assistants: List of assistant configurations

        Returns:
            Markdown formatted assistant list
        """
        ...

    def generate_injection_point_docs(self) -> str:
        """
        Generate documentation for available injection points.

        Returns:
            Markdown documentation of injection points and usage
        """
        ...


# Type aliases for cleaner code
AssistantName = str
InjectionPoints = Dict[str, str]
ValidationErrors = List[str]


# Injection point constants for type safety
class InjectionPointNames:
    """
    Constants for injection point names to ensure consistency.
    """

    COMMAND_PREFIX = "assistant_command_prefix"
    SETUP_INSTRUCTIONS = "assistant_setup_instructions"
    MEMORY_CONFIGURATION = "assistant_memory_configuration"
    CONTEXT_FILE_PATH = "assistant_context_file_path"
    REVIEW_COMMAND = "assistant_review_command"
    DOCUMENTATION_URL = "assistant_documentation_url"


# Required injection points that all assistants must provide
REQUIRED_INJECTION_POINTS = {
    InjectionPointNames.SETUP_INSTRUCTIONS,
    InjectionPointNames.CONTEXT_FILE_PATH,
}


# Optional injection points for enhanced functionality
OPTIONAL_INJECTION_POINTS = {
    InjectionPointNames.MEMORY_CONFIGURATION,
    InjectionPointNames.REVIEW_COMMAND,
    InjectionPointNames.DOCUMENTATION_URL,
}

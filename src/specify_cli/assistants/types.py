"""
Type-safe data structures for AI assistant organization system.

This module provides fully typed, validated data structures for assistant
configurations with zero hardcoding and complete type safety using Pydantic.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Set

from pydantic import BaseModel, Field, field_validator, model_validator


class FileFormat(str, Enum):
    """File formats for assistant files."""

    MARKDOWN = "md"
    MDC = "mdc"  # Cursor rule files


class TemplateConfig(BaseModel):
    """Configuration for template file generation."""

    directory: str = Field(..., min_length=1, description="Directory path for files")
    file_format: FileFormat = Field(..., description="File format for generated files")

    class Config:
        frozen = True
        extra = "forbid"
        validate_assignment = True
        str_strip_whitespace = True


class ContextFileConfig(BaseModel):
    """Configuration for context file."""

    file: str = Field(..., min_length=1, description="Context file path")
    file_format: FileFormat = Field(..., description="File format for context file")

    class Config:
        frozen = True
        extra = "forbid"
        validate_assignment = True
        str_strip_whitespace = True


class InjectionPoint(str, Enum):
    """
    Type-safe enumeration of all possible template injection points.

    Each injection point represents a specific place where assistant-specific
    content can be injected into templates or configurations.
    """

    COMMAND_PREFIX = "assistant_command_prefix"
    """Command prefix for the AI assistant (e.g., 'claude ', 'cursor '). Used in CLI command examples and documentation."""

    SETUP_INSTRUCTIONS = "assistant_setup_instructions"
    """Step-by-step setup instructions for getting the AI assistant ready for use in the project."""

    CONTEXT_FILE_PATH = "assistant_context_file_path"
    """Path to the main context file where the AI assistant stores project-specific configuration and instructions."""

    CONTEXT_FILE_DESCRIPTION = "assistant_context_file_description"
    """Brief description of the context file format and purpose for the AI assistant."""

    MEMORY_CONFIGURATION = "assistant_memory_configuration"
    """Description of how the AI assistant manages project memory, context, and persistent information."""

    REVIEW_COMMAND = "assistant_review_command"
    """Specific command used to trigger code review functionality with the AI assistant."""

    DOCUMENTATION_URL = "assistant_documentation_url"
    """Official documentation URL for the AI assistant, providing comprehensive usage guides and API references."""

    WORKFLOW_INTEGRATION = "assistant_workflow_integration"
    """Description of how the AI assistant integrates with development workflows, CI/CD, and automation tools."""

    CUSTOM_COMMANDS = "assistant_custom_commands"
    """List of custom or specialized commands available with this AI assistant beyond basic functionality."""

    CONTEXT_FRONTMATTER = "assistant_context_frontmatter"
    """YAML frontmatter or metadata block that should be included at the top of the assistant's context files."""

    IMPORT_SYNTAX = "assistant_import_syntax"
    """Syntax used by the AI assistant to import or reference external files within its context system."""

    BEST_PRACTICES = "assistant_best_practices"
    """Recommended best practices and usage patterns for getting optimal results from the AI assistant."""

    TROUBLESHOOTING = "assistant_troubleshooting"
    """Common troubleshooting steps and solutions for issues that may arise when using the AI assistant."""

    LIMITATIONS = "assistant_limitations"
    """Known limitations, constraints, or considerations when using the AI assistant in development workflows."""

    FILE_EXTENSIONS = "assistant_file_extensions"
    """File extensions and formats that the AI assistant works best with or has specialized support for."""


class AssistantConfig(BaseModel):
    """
    Type-safe, immutable configuration for AI assistant definitions.

    Uses Pydantic for runtime validation, JSON schema generation, and
    built-in serialization capabilities. All validation occurs at construction
    time with detailed error messages.
    """

    name: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_-]*$",
        min_length=1,
        max_length=50,
        description="Unique assistant identifier (lowercase, alphanumeric with hyphens/underscores)",
    )

    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name for UI display",
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Brief description of the assistant for help text",
    )

    base_directory: str = Field(
        ...,
        pattern=r"^\.[a-z][a-z0-9_-]*$",
        description="Base directory for assistant files (must be hidden, start with '.')",
    )

    # Template configurations for different file types
    context_file: ContextFileConfig = Field(
        ..., description="Context file configuration"
    )

    command_files: TemplateConfig = Field(
        ..., description="Command files configuration (slash commands to bash scripts)"
    )

    agent_files: TemplateConfig = Field(
        ..., description="Agent-specific files configuration"
    )

    @field_validator("display_name")
    @classmethod
    def validate_display_name_not_whitespace(cls, v: str) -> str:
        """Ensure display name is not just whitespace."""
        if not v.strip():
            raise ValueError("Display name cannot be empty or only whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description_not_whitespace(cls, v: str) -> str:
        """Ensure description is not just whitespace."""
        if not v.strip():
            raise ValueError("Description cannot be empty or only whitespace")
        return v.strip()

    @model_validator(mode="after")
    def validate_paths_under_base(self) -> "AssistantConfig":
        """Validate that all paths are under the base directory."""
        base_path = Path(self.base_directory)

        # Validate context file - allow it to be in project root or under base directory
        context_path = Path(self.context_file.file)

        # Context file can be in project root (like CLAUDE.md) or under base directory
        is_in_base_dir = True
        is_in_project_root = (
            context_path.name == context_path.as_posix()
        )  # Simple filename like "CLAUDE.md"

        if not is_in_project_root:
            try:
                context_path.relative_to(base_path)
            except ValueError:
                is_in_base_dir = False

        if not is_in_project_root and not is_in_base_dir:
            raise ValueError(
                f"Context file '{self.context_file.file}' must be in project root or under base directory '{self.base_directory}'"
            )

        # Validate commands directory
        commands_path = Path(self.command_files.directory)
        try:
            commands_path.relative_to(base_path)
        except ValueError as e:
            raise ValueError(
                f"Commands directory '{self.command_files.directory}' must be under base directory '{self.base_directory}'"
            ) from e

        # Validate agent files directory
        agent_path = Path(self.agent_files.directory)
        try:
            agent_path.relative_to(base_path)
        except ValueError as e:
            raise ValueError(
                f"Agent files directory '{self.agent_files.directory}' must be under base directory '{self.base_directory}'"
            ) from e

        return self

    def get_all_paths(self) -> Set[str]:
        """
        Get all file/directory paths defined in this configuration.

        Returns:
            Set of all paths for type-safe iteration
        """
        return {
            self.base_directory,
            self.context_file.file,
            self.command_files.directory,
            self.agent_files.directory,
        }

    def is_path_managed(self, path: str) -> bool:
        """
        Check if a given path is managed by this assistant.

        Args:
            path: Path to check

        Returns:
            True if path is managed by this assistant
        """
        if not isinstance(path, str):
            return False

        normalized_path = str(Path(path).as_posix())
        return any(
            normalized_path.startswith(managed_path)
            for managed_path in self.get_all_paths()
        )

    class Config:
        """Pydantic configuration for AssistantConfig."""

        # Immutability - prevent modification after creation
        frozen = True

        # No extra fields allowed - strict validation
        extra = "forbid"

        # Enhanced validation settings
        validate_assignment = True  # Validate on assignment, not just initialization
        str_strip_whitespace = True  # Automatically strip whitespace from strings
        validate_default = True  # Validate default values
        use_enum_values = True  # Use enum values in validation errors


# Required injection points that every assistant must provide
REQUIRED_INJECTION_POINTS: Set[InjectionPoint] = {
    InjectionPoint.COMMAND_PREFIX,
    InjectionPoint.SETUP_INSTRUCTIONS,
    InjectionPoint.CONTEXT_FILE_PATH,
}

# Optional injection points that assistants may provide
OPTIONAL_INJECTION_POINTS: Set[InjectionPoint] = {
    InjectionPoint.CONTEXT_FILE_DESCRIPTION,
    InjectionPoint.MEMORY_CONFIGURATION,
    InjectionPoint.REVIEW_COMMAND,
    InjectionPoint.DOCUMENTATION_URL,
    InjectionPoint.WORKFLOW_INTEGRATION,
    InjectionPoint.CUSTOM_COMMANDS,
    InjectionPoint.CONTEXT_FRONTMATTER,
    InjectionPoint.IMPORT_SYNTAX,
    InjectionPoint.BEST_PRACTICES,
    InjectionPoint.TROUBLESHOOTING,
    InjectionPoint.LIMITATIONS,
    InjectionPoint.FILE_EXTENSIONS,
}

# All valid injection points (for validation)
ALL_INJECTION_POINTS: Set[InjectionPoint] = (
    REQUIRED_INJECTION_POINTS | OPTIONAL_INJECTION_POINTS
)

# Injection point descriptions for UI display and help text
INJECTION_POINT_DESCRIPTIONS: Dict[InjectionPoint, str] = {
    InjectionPoint.COMMAND_PREFIX: "Command prefix for the AI assistant (e.g., 'claude ', 'cursor '). Used in CLI command examples and documentation.",
    InjectionPoint.SETUP_INSTRUCTIONS: "Step-by-step setup instructions for getting the AI assistant ready for use in the project.",
    InjectionPoint.CONTEXT_FILE_PATH: "Path to the main context file where the AI assistant stores project-specific configuration and instructions.",
    InjectionPoint.CONTEXT_FILE_DESCRIPTION: "Brief description of the context file format and purpose for the AI assistant.",
    InjectionPoint.MEMORY_CONFIGURATION: "Description of how the AI assistant manages project memory, context, and persistent information.",
    InjectionPoint.REVIEW_COMMAND: "Specific command used to trigger code review functionality with the AI assistant.",
    InjectionPoint.DOCUMENTATION_URL: "Official documentation URL for the AI assistant, providing comprehensive usage guides and API references.",
    InjectionPoint.WORKFLOW_INTEGRATION: "Description of how the AI assistant integrates with development workflows, CI/CD, and automation tools.",
    InjectionPoint.CUSTOM_COMMANDS: "List of custom or specialized commands available with this AI assistant beyond basic functionality.",
    InjectionPoint.CONTEXT_FRONTMATTER: "YAML frontmatter or metadata block that should be included at the top of the assistant's context files.",
    InjectionPoint.IMPORT_SYNTAX: "Syntax used by the AI assistant to import or reference external files within its context system.",
    InjectionPoint.BEST_PRACTICES: "Recommended best practices and usage patterns for getting optimal results from the AI assistant.",
    InjectionPoint.TROUBLESHOOTING: "Common troubleshooting steps and solutions for issues that may arise when using the AI assistant.",
    InjectionPoint.LIMITATIONS: "Known limitations, constraints, or considerations when using the AI assistant in development workflows.",
    InjectionPoint.FILE_EXTENSIONS: "File extensions and formats that the AI assistant works best with or has specialized support for.",
}

# Type aliases for better type safety and readability
InjectionValues = Dict[InjectionPoint, str]
AssistantName = str  # Should be lowercase, alphanumeric with hyphens/underscores
AssistantPath = str  # File system path string
AssistantPaths = Dict[AssistantName, AssistantPath]

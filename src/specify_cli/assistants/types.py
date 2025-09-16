"""
Type-safe data structures for AI assistant organization system.

This module provides fully typed, validated data structures for assistant
configurations with zero hardcoding and complete type safety using Pydantic.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Set

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


class ContextFileConfig(BaseModel):
    """Configuration for context file."""

    file: str = Field(..., min_length=1, description="Context file path")
    file_format: FileFormat = Field(..., description="File format for context file")

    class Config:
        frozen = True
        extra = "forbid"


class InjectionPoint(str, Enum):
    """
    Type-safe enumeration of all possible template injection points.

    Each injection point represents a specific place where assistant-specific
    content can be injected into templates or configurations.
    """

    COMMAND_PREFIX = "assistant_command_prefix"
    SETUP_INSTRUCTIONS = "assistant_setup_instructions"
    CONTEXT_FILE_PATH = "assistant_context_file_path"
    MEMORY_CONFIGURATION = "assistant_memory_configuration"
    REVIEW_COMMAND = "assistant_review_command"
    DOCUMENTATION_URL = "assistant_documentation_url"
    WORKFLOW_INTEGRATION = "assistant_workflow_integration"
    CUSTOM_COMMANDS = "assistant_custom_commands"


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

        # Validate context file
        context_path = Path(self.context_file.file)
        try:
            context_path.relative_to(base_path)
        except ValueError as e:
            raise ValueError(
                f"Context file '{self.context_file.file}' must be under base directory '{self.base_directory}'"
            ) from e

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

        # Schema generation example for documentation
        json_schema_extra = {
            "example": {
                "name": "claude",
                "display_name": "Claude Code",
                "description": "Anthropic's Claude Code AI assistant",
                "base_directory": ".claude",
                "context_file": {"file": ".claude/CLAUDE.md", "file_format": "md"},
                "command_files": {"directory": ".claude/commands", "file_format": "md"},
                "agent_files": {"directory": ".claude/agents", "file_format": "md"},
            }
        }


# Required injection points that every assistant must provide
REQUIRED_INJECTION_POINTS: Set[InjectionPoint] = {
    InjectionPoint.COMMAND_PREFIX,
    InjectionPoint.SETUP_INSTRUCTIONS,
    InjectionPoint.CONTEXT_FILE_PATH,
}

# Optional injection points that assistants may provide
OPTIONAL_INJECTION_POINTS: Set[InjectionPoint] = {
    InjectionPoint.MEMORY_CONFIGURATION,
    InjectionPoint.REVIEW_COMMAND,
    InjectionPoint.DOCUMENTATION_URL,
    InjectionPoint.WORKFLOW_INTEGRATION,
    InjectionPoint.CUSTOM_COMMANDS,
}

# All valid injection points (for validation)
ALL_INJECTION_POINTS: Set[InjectionPoint] = (
    REQUIRED_INJECTION_POINTS | OPTIONAL_INJECTION_POINTS
)

# Type aliases for better type safety and readability
InjectionValues = Dict[InjectionPoint, str]
AssistantName = str  # Should be lowercase, alphanumeric with hyphens/underscores
AssistantPath = str  # File system path string
AssistantPaths = Dict[AssistantName, AssistantPath]

"""
Type-safe data structures for AI assistant organization system.

This module provides fully typed, validated data structures for assistant
configurations with zero hardcoding and complete type safety using Pydantic.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .injection_points import InjectionPointMeta


class FileFormat(str, Enum):
    """File formats for assistant files."""

    MARKDOWN = "md"
    MDC = "mdc"  # Cursor rule files


class TemplateConfig(BaseModel):
    """Configuration for template file generation."""

    directory: str = Field(..., min_length=1, description="Directory path for files")
    file_format: FileFormat = Field(..., description="File format for generated files")

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class ContextFileConfig(BaseModel):
    """Configuration for context file."""

    file: str = Field(..., min_length=1, description="Context file path")
    file_format: FileFormat = Field(..., description="File format for context file")

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


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

    agent_files: Optional[TemplateConfig] = Field(
        None, description="Agent-specific files configuration (None to disable agents)"
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

        # Validate agent files directory (if configured)
        if self.agent_files:
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
            Set of all paths for immutable iteration
        """
        paths = {
            self.base_directory,
            self.context_file.file,
            self.command_files.directory,
        }
        if self.agent_files:
            paths.add(self.agent_files.directory)
        return paths

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

    model_config = ConfigDict(
        # Immutability - prevent modification after creation
        frozen=True,
        # No extra fields allowed - strict validation
        extra="forbid",
        # Enhanced validation settings
        validate_assignment=True,  # Validate on assignment, not just initialization
        str_strip_whitespace=True,  # Automatically strip whitespace from strings
        validate_default=True,  # Validate default values
        use_enum_values=True,  # Use enum values in validation errors
    )


# Type aliases for better type safety and readability
InjectionValues = Dict[InjectionPointMeta, str]
AssistantName = str  # Should be lowercase, alphanumeric with hyphens/underscores
AssistantPath = str  # File system path string
AssistantPaths = Dict[AssistantName, AssistantPath]

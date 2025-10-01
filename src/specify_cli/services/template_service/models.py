"""
Template Service Models - Data classes and types for template operations.

This module contains all the data structures, enums, and model classes
used throughout the template service subsystem.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

from specify_cli.models.template import GranularTemplate


@dataclass(frozen=True)
class TemplateFolderMapping:
    """Type-safe template folder configuration"""

    source: str  # Source folder in templates/
    target_pattern: str  # Target pattern, supports {ai_assistant}, {project_name}
    render: bool  # Whether to render .j2 files or copy as-is
    executable_extensions: List[str]  # File extensions to make executable


@dataclass
class RenderResult:
    """Type-safe render operation result"""

    rendered_files: List[Path] = field(default_factory=list)
    copied_files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_files(self) -> int:
        return len(self.rendered_files) + len(self.copied_files)


class TemplateChangeType(Enum):
    """Types of template changes."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class TemplateChange:
    """Represents a change to a template."""

    template_name: str
    change_type: TemplateChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    category: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    should_skip: bool = False  # Whether this file should be skipped during updates

    def calculate_line_changes(self) -> None:
        """Calculate lines added and removed."""
        if self.old_content is None or self.new_content is None:
            return

        old_lines = self.old_content.splitlines()
        new_lines = self.new_content.splitlines()

        # Simple line-based diff calculation
        self.lines_added = max(0, len(new_lines) - len(old_lines))
        self.lines_removed = max(0, len(old_lines) - len(new_lines))


@dataclass
class TemplateDiff:
    """Result of comparing template sets."""

    changes: List[TemplateChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(
            change.change_type != TemplateChangeType.UNCHANGED
            for change in self.changes
        )

    @property
    def added_count(self) -> int:
        return len(
            [c for c in self.changes if c.change_type == TemplateChangeType.ADDED]
        )

    @property
    def modified_count(self) -> int:
        return len(
            [c for c in self.changes if c.change_type == TemplateChangeType.MODIFIED]
        )

    @property
    def deleted_count(self) -> int:
        return len(
            [c for c in self.changes if c.change_type == TemplateChangeType.DELETED]
        )

    def get_changes_by_type(
        self, change_type: TemplateChangeType
    ) -> List[TemplateChange]:
        """Get changes of a specific type.

        Args:
            change_type: Type of changes to filter

        Returns:
            List of changes of the specified type
        """
        return [change for change in self.changes if change.change_type == change_type]


@dataclass
class TemplateRenderResult:
    """Result of rendering a single template"""

    template: GranularTemplate
    content: str
    success: bool = True
    error_message: Optional[str] = None

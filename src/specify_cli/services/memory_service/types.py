"""
Type-safe data structures for memory file management.

This module provides Pydantic models for memory file discovery, categorization,
and import formatting with complete type safety and validation.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from specify_cli.assistants.types import AssistantName


class MemoryCategory(str, Enum):
    """Categories for organizing memory files."""

    CONSTITUTION = "constitution"
    PRINCIPLES = "principles"
    GUIDELINES = "guidelines"
    STANDARDS = "standards"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class MemoryFilePattern(BaseModel):
    """Pattern for matching memory files with categorization."""

    filename_pattern: str = Field(
        ..., description="Glob pattern or exact filename to match"
    )
    category: MemoryCategory = Field(
        ..., description="Category for organizing the file"
    )
    priority: int = 100  # Priority for ordering (lower = higher priority)

    @field_validator("filename_pattern")
    @classmethod
    def validate_pattern_not_empty(cls, v: str) -> str:
        """Ensure pattern is not empty."""
        if not v.strip():
            raise ValueError("Filename pattern cannot be empty")
        return v.strip()


class MemoryImportConfig(BaseModel):
    """Configuration for memory file imports."""

    enabled: bool = Field(
        default=True, description="Whether memory imports are enabled"
    )

    extensions: List[str] = Field(
        default=[".md", ".txt"], description="File extensions to include in discovery"
    )

    patterns: List[MemoryFilePattern] = Field(
        default=[
            MemoryFilePattern(
                filename_pattern="constitution.md",
                category=MemoryCategory.CONSTITUTION,
                priority=1,
            ),
            MemoryFilePattern(
                filename_pattern="principles.md",
                category=MemoryCategory.PRINCIPLES,
                priority=2,
            ),
            MemoryFilePattern(
                filename_pattern="guidelines.md",
                category=MemoryCategory.GUIDELINES,
                priority=3,
            ),
            MemoryFilePattern(
                filename_pattern="standards.md",
                category=MemoryCategory.STANDARDS,
                priority=4,
            ),
        ],
        description="Patterns for categorizing and prioritizing memory files",
    )

    max_files: int = 10  # Maximum number of files to import

    @field_validator("extensions")
    @classmethod
    def validate_extensions_format(cls, v: List[str]) -> List[str]:
        """Ensure all extensions start with a dot."""
        result = []
        for ext in v:
            if not ext.startswith("."):
                ext = f".{ext}"
            result.append(ext.lower())
        return result


class DiscoveredMemoryFile(BaseModel):
    """Represents a discovered memory file with metadata."""

    path: Path = Field(..., description="Full path to the memory file")
    filename: str = Field(..., description="Just the filename")
    category: MemoryCategory = Field(..., description="Categorized type of memory file")
    priority: int = Field(..., description="Priority for ordering")
    exists: bool = Field(..., description="Whether the file actually exists")

    model_config = ConfigDict(frozen=True)


class FormattedMemoryImport(BaseModel):
    """Represents a formatted import string for an assistant."""

    import_string: str = Field(
        ..., description="Assistant-specific formatted import string"
    )
    source_file: DiscoveredMemoryFile = Field(
        ..., description="Source memory file information"
    )
    assistant_name: AssistantName = Field(
        ..., description="Assistant this import was formatted for"
    )

    model_config = ConfigDict(frozen=True)


class MemoryImportSection(BaseModel):
    """Complete memory import section for templates."""

    imports: List[FormattedMemoryImport] = Field(
        default=[], description="All formatted imports"
    )
    assistant_name: AssistantName = Field(
        ..., description="Assistant this section was generated for"
    )
    has_constitution: bool = Field(
        default=False, description="Whether constitution files are included"
    )
    has_other_files: bool = Field(
        default=False, description="Whether non-constitution files are included"
    )

    def render(self) -> str:
        """Render the complete import section as string."""
        if not self.imports:
            return ""

        sections = []

        # Group by category
        constitution_imports = [
            imp
            for imp in self.imports
            if imp.source_file.category == MemoryCategory.CONSTITUTION
        ]
        other_imports = [
            imp
            for imp in self.imports
            if imp.source_file.category != MemoryCategory.CONSTITUTION
        ]

        # Add constitution imports first
        if constitution_imports:
            sections.extend([imp.import_string for imp in constitution_imports])

        # Add other imports with header if needed
        if other_imports:
            if constitution_imports:
                sections.append("")
                sections.append("### Additional Memory")
            sections.extend([imp.import_string for imp in other_imports])

        return "\n".join(sections)

    model_config = ConfigDict(frozen=True)


# Type aliases for better readability
MemoryFileMap = Dict[MemoryCategory, List[DiscoveredMemoryFile]]
AssistantImportMap = Dict[AssistantName, MemoryImportSection]

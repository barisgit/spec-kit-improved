"""Data models for Template Registry Service."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class TemplateMetadata:
    """Metadata extracted from template frontmatter or docstrings."""

    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    required: bool = False
    is_utility: bool = False
    variables: Dict[str, str] = field(default_factory=dict)
    author: Optional[str] = None
    version: Optional[str] = None


@dataclass(frozen=True)
class TemplateInfo:
    """Information about a single template."""

    name: str
    category: str
    source_path: Path
    is_runtime_template: bool  # .j2 files that stay as templates
    metadata: TemplateMetadata = field(default_factory=TemplateMetadata)

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return self.name.replace("-", " ").replace("_", " ").title()

    @property
    def filename(self) -> str:
        """Get the filename with extension."""
        return self.source_path.name


@dataclass(frozen=True)
class CategoryInfo:
    """Configuration for a template category."""

    name: str
    source: str  # Source directory in template package
    target_pattern: str  # Target pattern with variables
    render_templates: bool  # Whether to render .j2 files
    is_ai_specific: bool  # Uses AI-specific directories
    description: str = ""
    required_templates: Set[str] = field(default_factory=set)  # Always included

    def resolve_target(
        self, ai_assistant: str, project_name: str = ""
    ) -> Optional[str]:
        """Resolve target path with variable substitution. Returns None if category is disabled for assistant."""
        from specify_cli.assistants import get_assistant

        # Get assistant config for dynamic path resolution
        assistant = get_assistant(ai_assistant)

        # Use actual configuration from assistant, not hardcoded patterns
        if assistant and assistant.config.agent_files:
            ai_agents = assistant.config.agent_files.directory
        elif assistant:
            # Assistant exists but has no agent_files configured (disabled)
            # Return None early for agent categories when agents are disabled
            if self.name in ["agent-prompts", "agent-templates"]:
                return None
            ai_agents = ""  # Empty string for format, won't be used
        else:
            # Fallback for unknown assistants - should not create agents if assistant unknown
            # Return None for agent categories when assistant is unknown
            if self.name in ["agent-prompts", "agent-templates"]:
                return None
            ai_agents = ""  # Empty string for format, won't be used

        variables = {
            "ai_dir": assistant.config.base_directory
            if assistant
            else f".{ai_assistant}",
            "ai_commands": assistant.config.command_files.directory
            if assistant
            else f".{ai_assistant}/commands",
            "ai_agents": ai_agents,
            "project_name": project_name,
            "category": self.name,
        }

        return self.target_pattern.format(**variables)


@dataclass(frozen=True)
class ValidationResult:
    """Result of template validation."""

    valid_templates: List[str]
    invalid_templates: List[str]
    warnings: List[str]
    is_valid: bool

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

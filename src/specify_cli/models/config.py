"""
Configuration data models for spec-kit

These models define the structure for project and global configurations,
supporting TOML serialization and validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .defaults import BRANCH_DEFAULTS


def _get_default_ai_assistant() -> str:
    """Get default AI assistant from PATH_DEFAULTS"""
    from .defaults.path_defaults import PATH_DEFAULTS

    return PATH_DEFAULTS.PROJECT_DEFAULTS.default_ai_assistant


def _get_default_config_directory() -> str:
    """Get default config directory from PATH_DEFAULTS"""
    from .defaults.path_defaults import PATH_DEFAULTS

    return PATH_DEFAULTS.PROJECT_DEFAULTS.config_directory


@dataclass
class BranchNamingConfig:
    """Configuration for branch naming patterns"""

    # Use configurable defaults from BRANCH_DEFAULTS
    description: str = field(
        default_factory=lambda: BRANCH_DEFAULTS.get_default_pattern().description
    )
    patterns: List[str] = field(
        default_factory=lambda: BRANCH_DEFAULTS.DEFAULT_PATTERNS.copy()
    )
    validation_rules: List[str] = field(
        default_factory=lambda: BRANCH_DEFAULTS.DEFAULT_VALIDATION_RULES.copy()
    )
    default_pattern: Optional[str] = field(
        default_factory=lambda: BRANCH_DEFAULTS.DEFAULT_PATTERNS[0]
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        return {
            "description": self.description,
            "patterns": self.patterns.copy(),
            "validation_rules": self.validation_rules.copy(),
            "default_pattern": self.default_pattern,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BranchNamingConfig":
        """Create instance from dictionary (TOML deserialization)"""
        return cls(
            description=data.get(
                "description", BRANCH_DEFAULTS.get_default_pattern().description
            ),
            patterns=data.get("patterns", BRANCH_DEFAULTS.DEFAULT_PATTERNS.copy()),
            validation_rules=data.get(
                "validation_rules", BRANCH_DEFAULTS.DEFAULT_VALIDATION_RULES.copy()
            ),
            default_pattern=data.get(
                "default_pattern", BRANCH_DEFAULTS.DEFAULT_PATTERNS[0]
            ),
        )


@dataclass
class TemplateConfig:
    """Configuration for template engine settings"""

    ai_assistant: str = field(default_factory=lambda: _get_default_ai_assistant())
    config_directory: str = field(
        default_factory=lambda: _get_default_config_directory()
    )
    custom_templates_dir: Optional[Path] = None
    template_cache_enabled: bool = True
    template_variables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        result: Dict[str, Any] = {
            "ai_assistant": self.ai_assistant,
            "config_directory": self.config_directory,
            "template_cache_enabled": self.template_cache_enabled,
        }

        if self.custom_templates_dir:
            result["custom_templates_dir"] = str(self.custom_templates_dir)

        if self.template_variables:
            # Preserve nested dict typing by storing as Any
            result["template_variables"] = dict(self.template_variables)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateConfig":
        """Create instance from dictionary (TOML deserialization)"""
        custom_templates_dir = None
        if "custom_templates_dir" in data and data["custom_templates_dir"]:
            custom_templates_dir = Path(data["custom_templates_dir"])

        return cls(
            ai_assistant=data.get("ai_assistant", "claude"),
            config_directory=data.get("config_directory", ".specify"),
            custom_templates_dir=custom_templates_dir,
            template_cache_enabled=data.get("template_cache_enabled", True),
            template_variables=data.get("template_variables", {}),
        )


@dataclass
class ProjectConfig:
    """Main project configuration"""

    name: str
    branch_naming: BranchNamingConfig = field(default_factory=BranchNamingConfig)
    template_settings: TemplateConfig = field(default_factory=TemplateConfig)
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        result = {
            "project": {
                "name": self.name,
                "branch_naming": self.branch_naming.to_dict(),
                "template_settings": self.template_settings.to_dict(),
            }
        }

        if self.created_at:
            result["project"]["created_at"] = self.created_at.isoformat()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """Create instance from dictionary (TOML deserialization)"""
        project_data = data.get("project", {})

        branch_naming = BranchNamingConfig()
        if "branch_naming" in project_data:
            branch_naming = BranchNamingConfig.from_dict(project_data["branch_naming"])

        template_settings = TemplateConfig()
        if "template_settings" in project_data:
            template_settings = TemplateConfig.from_dict(
                project_data["template_settings"]
            )

        created_at = None
        if "created_at" in project_data:
            created_at_str = project_data["created_at"]
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(created_at_str)
            elif isinstance(created_at_str, datetime):
                created_at = created_at_str

        return cls(
            name=project_data.get("name", ""),
            branch_naming=branch_naming,
            template_settings=template_settings,
            created_at=created_at,
        )

    @classmethod
    def create_default(cls, name: str = "default-project") -> "ProjectConfig":
        """Create a default configuration"""
        return cls(
            name=name,
            branch_naming=BranchNamingConfig(),
            template_settings=TemplateConfig(),
        )

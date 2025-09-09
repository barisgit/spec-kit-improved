"""
Configuration data models for spec-kit

These models define the structure for project and global configurations,
supporting TOML serialization and validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BranchNamingConfig:
    """Configuration for branch naming patterns"""

    # FIXME: HARDCODED - Branch naming patterns and validation rules hardcoded
    # TODO: Make configurable via configuration system
    description: str = "Modern feature branches with hotfixes and main branches"
    patterns: List[str] = field(
        default_factory=lambda: [
            "feature/{feature-name}",
            "hotfix/{bug-id}",
            "bugfix/{bug-id}",
            "main",
            "development",
        ]
    )
    validation_rules: List[str] = field(
        default_factory=lambda: [
            "max_length_50",
            "lowercase_only",
            "no_spaces",
            "alphanumeric_dash_slash_only",
        ]
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        return {
            "description": self.description,
            "patterns": self.patterns.copy(),
            "validation_rules": self.validation_rules.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BranchNamingConfig":
        """Create instance from dictionary (TOML deserialization)"""
        return cls(
            description=data.get(
                "description", "Modern feature branches with hotfixes and main branches"
            ),
            patterns=data.get(
                "patterns",
                [
                    "feature/{feature-name}",
                    "hotfix/{bug-id}",
                    "bugfix/{bug-id}",
                    "main",
                    "development",
                ],
            ),
            validation_rules=data.get(
                "validation_rules",
                [
                    "max_length_50",
                    "lowercase_only",
                    "no_spaces",
                    "alphanumeric_dash_slash_only",
                ],
            ),
        )


@dataclass
class TemplateConfig:
    """Configuration for template engine settings"""

    # FIXME: HARDCODED - AI assistant and config directory defaults hardcoded
    # TODO: Make configurable via configuration system
    ai_assistant: str = "claude"
    config_directory: str = ".specify"
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        return {
            "project": {
                "name": self.name,
                "branch_naming": self.branch_naming.to_dict(),
                "template_settings": self.template_settings.to_dict(),
            }
        }

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

        return cls(
            name=project_data.get("name", ""),
            branch_naming=branch_naming,
            template_settings=template_settings,
        )

    @classmethod
    def create_default(cls, name: str = "default-project") -> "ProjectConfig":
        """Create a default configuration"""
        return cls(
            name=name,
            branch_naming=BranchNamingConfig(),
            template_settings=TemplateConfig(),
        )

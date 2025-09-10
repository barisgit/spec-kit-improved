"""
Project-related data models for spec-kit

These models define project context and template variables for the Jinja2 engine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import BranchNamingConfig
from .defaults import PATH_DEFAULTS


@dataclass
class TemplateVariables:
    """Type-safe container for template variables that avoids dict method conflicts.

    This replaces TemplateDict with a more type-safe approach that prevents
    template variables from conflicting with dictionary methods in Jinja2.
    """

    variables: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to template variables."""
        if name in self.variables:
            return self.variables[name]
        raise AttributeError(f"Template variable '{name}' not found")

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to template variables."""
        return self.variables[key]

    def __contains__(self, key: str) -> bool:
        """Check if a template variable exists."""
        return key in self.variables

    def get(self, key: str, default: Any = None) -> Any:
        """Get a template variable with a default value."""
        return self.variables.get(key, default)

    def items(self):
        """Get all template variables as key-value pairs."""
        return self.variables.items()

    def keys(self):
        """Get all template variable keys."""
        return self.variables.keys()

    def values(self):
        """Get all template variable values."""
        return self.variables.values()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to regular dictionary for Jinja2 compatibility."""
        return self.variables.copy()


@dataclass
class TemplateContext:
    """Context data for template rendering with Jinja2"""

    # Project information
    project_name: str
    project_description: str = ""
    project_path: Optional[Path] = None

    # Branch information
    branch_name: str = ""
    feature_name: str = ""
    task_name: str = ""

    # User/environment information
    author_name: str = ""
    author_email: str = ""
    creation_date: str = field(
        default_factory=lambda: datetime.now().strftime(
            PATH_DEFAULTS.PROJECT_DEFAULTS.date_format
        )
    )
    creation_year: str = field(default_factory=lambda: str(datetime.now().year))

    # Template-specific variables
    template_variables: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # AI assistant configuration (enhanced)
    ai_assistant: str = field(
        default_factory=lambda: PATH_DEFAULTS.PROJECT_DEFAULTS.default_ai_assistant
    )
    ai_context: Dict[str, str] = field(default_factory=dict)

    # Branch naming configuration (new)
    branch_naming_config: BranchNamingConfig = field(default_factory=BranchNamingConfig)

    # Configuration settings (new)
    config_directory: str = field(
        default_factory=lambda: PATH_DEFAULTS.PROJECT_DEFAULTS.config_directory
    )

    # Platform information
    platform_name: str = ""

    # Git information
    git_remote_url: str = ""
    git_branch: str = ""

    # Specification information
    spec_number: str = ""
    spec_title: str = ""
    spec_type: str = field(
        default_factory=lambda: PATH_DEFAULTS.PROJECT_DEFAULTS.spec_type
    )  # feature, bugfix, hotfix, epic

    # Backwards compatibility fields for tests
    branch_type: str = ""
    additional_vars: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Handle backwards compatibility and setup computed fields"""
        # Set branch_type based on spec_type for backwards compatibility
        if not self.branch_type and self.spec_type:
            self.branch_type = self.spec_type

        # Note: AI assistant validation is permissive to allow unknown assistants
        # Templates handle fallback behavior through conditional logic

        # Validate paths are absolute if project_path is set
        if self.project_path and not self.project_path.is_absolute():
            raise ValueError("project_path must be absolute")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Jinja2 template rendering"""
        result = {
            # Basic project info
            "project_name": self.project_name,
            "project_description": self.project_description,
            "project_path": str(self.project_path) if self.project_path else "",
            # Branch and feature info
            "branch_name": self.branch_name,
            "feature_name": self.feature_name,
            "task_name": self.task_name,
            # Author and timing
            "author_name": self.author_name,
            "author_email": self.author_email,
            "creation_date": self.creation_date,
            "creation_year": self.creation_year,
            # AI assistant configuration
            "ai_assistant": self.ai_assistant,
            "ai_context": self.ai_context.copy(),
            # Branch naming configuration
            "branch_naming_config": self.branch_naming_config.to_dict(),
            # Configuration settings
            "config_directory": self.config_directory,
            # Git information
            "git_remote_url": self.git_remote_url,
            "git_branch": self.git_branch,
            # Specification
            "spec_number": self.spec_number,
            "spec_title": self.spec_title,
            "spec_type": self.spec_type,
            # Backwards compatibility
            "branch_type": self.branch_type,
            "additional_vars": TemplateVariables(
                self.additional_vars
            ),  # Use TemplateVariables to avoid method conflicts
            # Template variables (merged with custom fields and additional_vars)
            **self.template_variables,
            **self.custom_fields,
            # Don't flatten additional_vars to avoid conflicts with dict methods like .items()
        }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateContext":
        """Create TemplateContext from dictionary"""
        # Extract known fields
        known_fields = {
            "project_name",
            "project_description",
            "project_path",
            "branch_name",
            "feature_name",
            "task_name",
            "author_name",
            "author_email",
            "creation_date",
            "creation_year",
            "ai_assistant",
            "ai_context",
            "branch_naming_config",
            "config_directory",
            "git_remote_url",
            "git_branch",
            "spec_number",
            "spec_title",
            "spec_type",
        }

        # Separate known fields from custom variables
        context_data = {}
        custom_fields = {}

        for key, value in data.items():
            if key in known_fields:
                context_data[key] = value
            else:
                custom_fields[key] = value

        # Handle project_path conversion
        if "project_path" in context_data and context_data["project_path"]:
            context_data["project_path"] = Path(context_data["project_path"])

        # Handle branch_naming_config conversion
        if "branch_naming_config" in context_data and isinstance(
            context_data["branch_naming_config"], dict
        ):
            context_data["branch_naming_config"] = BranchNamingConfig.from_dict(
                context_data["branch_naming_config"]
            )

        # Set custom fields
        context_data["custom_fields"] = custom_fields

        return cls(**context_data)

    def merge_variables(self, variables: Dict[str, Any]) -> "TemplateContext":
        """Create new context with merged template variables"""
        new_context = TemplateContext(
            project_name=self.project_name,
            project_description=self.project_description,
            project_path=self.project_path,
            branch_name=self.branch_name,
            feature_name=self.feature_name,
            task_name=self.task_name,
            author_name=self.author_name,
            author_email=self.author_email,
            creation_date=self.creation_date,
            creation_year=self.creation_year,
            ai_assistant=self.ai_assistant,
            ai_context=self.ai_context.copy(),
            branch_naming_config=self.branch_naming_config,
            config_directory=self.config_directory,
            git_remote_url=self.git_remote_url,
            git_branch=self.git_branch,
            spec_number=self.spec_number,
            spec_title=self.spec_title,
            spec_type=self.spec_type,
            template_variables={**self.template_variables, **variables},
            custom_fields=self.custom_fields.copy(),
        )
        return new_context

    @classmethod
    def create_default(cls, project_name: str) -> "TemplateContext":
        """Create a default template context for a project"""
        return cls(
            project_name=project_name,
            project_description=f"Project: {project_name}",
            author_name="Developer",
            ai_assistant=PATH_DEFAULTS.PROJECT_DEFAULTS.default_ai_assistant,
            branch_naming_config=BranchNamingConfig(),
            config_directory=PATH_DEFAULTS.PROJECT_DEFAULTS.config_directory,
        )


@dataclass
class TemplateFile:
    """Represents a rendered template file"""

    template_path: Path
    output_path: str
    content: str
    is_executable: bool = False

    def __post_init__(self):
        """Ensure template_path is Path object"""
        if isinstance(self.template_path, str):
            self.template_path = Path(self.template_path)


class ProjectInitStep(Enum):
    """Steps in project initialization process"""

    VALIDATION = "validation"
    DIRECTORY_CREATION = "directory_creation"
    GIT_INIT = "git_init"
    DOWNLOAD = "download"
    TEMPLATE_RENDER = "template_render"
    CONFIG_SAVE = "config_save"
    BRANCH_CREATION = "branch_creation"
    STRUCTURE_SETUP = "structure_setup"
    FINALIZATION = "finalization"


@dataclass
class ProjectInitOptions:
    """Options for project initialization"""

    project_name: Optional[str] = None
    ai_assistant: str = field(
        default_factory=lambda: PATH_DEFAULTS.PROJECT_DEFAULTS.default_ai_assistant
    )
    use_current_dir: bool = False
    skip_git: bool = False
    ignore_agent_tools: bool = False
    custom_config: Optional[Dict[str, Any]] = None
    branch_pattern: Optional[str] = None
    branch_naming_config: Optional[BranchNamingConfig] = None
    force: bool = False


@dataclass
class ProjectInitResult:
    """Result of project initialization"""

    success: bool
    project_path: Path
    completed_steps: List[ProjectInitStep] = field(default_factory=list)
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None

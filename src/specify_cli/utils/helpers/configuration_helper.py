"""
Configuration Helper - focused on project configuration loading and management.

This helper handles:
- Project configuration loading
- Branch naming configuration
- Feature validation rules
- Configuration defaults
"""

from pathlib import Path
from typing import Any, Dict, Optional

from specify_cli.models.config import BranchNamingConfig
from specify_cli.services import TomlConfigService


class ConfigurationHelper:
    """Helper for project configuration operations."""

    def __init__(self):
        """Initialize with config service."""
        self._config_service = TomlConfigService()

    def load_project_config(
        self, project_path: Optional[Path] = None
    ) -> Optional[Dict]:
        """
        Load project configuration from .specify/config.toml.

        Args:
            project_path: Path to project directory (defaults to current directory)

        Returns:
            Optional[Dict]: Project configuration as dict, or None if not found
        """
        try:
            if project_path is None:
                project_path = Path.cwd()
            project_config = self._config_service.load_project_config(project_path)
            if project_config:
                return project_config.to_dict()
            return None
        except Exception:
            return None

    def get_branch_naming_config(self) -> Dict:
        """
        Get branch naming configuration with fallbacks.

        Returns:
            Dict: Branch naming configuration with defaults applied
        """
        config = self.load_project_config()

        if config and "project" in config and "branch_naming" in config["project"]:
            # Use the branch_naming config from the dict
            branch_config_dict = config["project"]["branch_naming"]
            return {
                "description": branch_config_dict.get("description", ""),
                "patterns": branch_config_dict.get("patterns", []),
                "validation_rules": branch_config_dict.get("validation_rules", []),
                "default_pattern": branch_config_dict.get("default_pattern", ""),
            }

        # Return defaults if no valid config found
        default_config = BranchNamingConfig()
        return {
            "description": default_config.description,
            "patterns": default_config.patterns,
            "validation_rules": default_config.validation_rules,
            "default_pattern": default_config.default_pattern,
        }

    def get_project_name(self) -> str:
        """
        Get project name from configuration or directory.

        Returns:
            str: Project name, defaults to current directory name
        """
        config = self.load_project_config()

        if config and "project" in config and "name" in config["project"]:
            return config["project"]["name"]

        # Fallback to directory name
        return Path.cwd().name

    def validate_feature_description(
        self, description: str, min_length: int = 3, max_length: int = 100
    ) -> tuple[bool, Optional[str]]:
        """
        Validate feature description against project rules.

        Args:
            description: Feature description to validate
            min_length: Minimum length requirement
            max_length: Maximum length requirement

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not description or not description.strip():
            return False, "Feature description cannot be empty"

        description = description.strip()

        if len(description) < min_length:
            return (
                False,
                f"Feature description must be at least {min_length} characters",
            )

        if len(description) > max_length:
            return False, f"Feature description cannot exceed {max_length} characters"

        # Check for invalid characters
        invalid_chars = ["#", "@", "$", "%", "^", "&", "*", "(", ")", "+", "="]
        for char in invalid_chars:
            if char in description:
                return False, f"Feature description cannot contain '{char}'"

        # Check that description contains at least some letters
        if not any(c.isalpha() for c in description):
            return False, "Feature description must contain at least one letter"

        return True, None

    def get_current_date(self) -> str:
        """
        Get current date in project's preferred format.

        Returns:
            str: Current date formatted according to project config
        """
        from datetime import datetime

        config = self.load_project_config()

        # Check if project has a preferred date format
        if config and "project" in config and "date_format" in config["project"]:
            date_format = config["project"]["date_format"]
        else:
            date_format = "%Y-%m-%d"  # Default format

        return datetime.now().strftime(date_format)

    def get_ai_assistant_config(self) -> str:
        """
        Get configured AI assistant.

        Returns:
            str: AI assistant name, defaults to 'claude'
        """
        config = self.load_project_config()

        if config and "ai_assistant" in config:
            return config["ai_assistant"]

        return "claude"  # Default

    def get_template_config(self) -> Dict[str, Any]:
        """
        Get template configuration settings.

        Returns:
            Dict[str, Any]: Template configuration
        """
        config = self.load_project_config()

        if config and "templates" in config:
            return config["templates"]

        return {
            "auto_render": True,
            "preserve_user_files": True,
            "backup_on_overwrite": False,
        }

    def get_feature_numbering_config(self) -> Dict[str, Any]:
        """
        Get feature numbering configuration.

        Returns:
            Dict[str, Any]: Feature numbering settings
        """
        config = self.load_project_config()

        if config and "feature_numbering" in config:
            return config["feature_numbering"]

        return {
            "start_number": 1,
            "pad_zeros": 3,  # e.g., 001, 002, 003
            "increment": 1,
        }

    def is_auto_render_enabled(self) -> bool:
        """
        Check if auto-rendering is enabled.

        Returns:
            bool: True if templates should be auto-rendered
        """
        template_config = self.get_template_config()
        return template_config.get("auto_render", True)

    def should_preserve_user_files(self) -> bool:
        """
        Check if user files should be preserved during updates.

        Returns:
            bool: True if user files should be preserved
        """
        template_config = self.get_template_config()
        return template_config.get("preserve_user_files", True)

    def should_backup_on_overwrite(self) -> bool:
        """
        Check if backups should be created when overwriting files.

        Returns:
            bool: True if backups should be created
        """
        template_config = self.get_template_config()
        return template_config.get("backup_on_overwrite", False)

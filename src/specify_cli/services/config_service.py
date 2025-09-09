"""
Configuration service for managing project and global settings

Provides TOML-based configuration management with backup/restore capabilities.
"""

import re
import shutil
import tomllib
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

# For type hints
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import tomli_w

from ..models.config import ProjectConfig

if TYPE_CHECKING:
    from ..models.config import BranchNamingConfig


class ConfigService(ABC):
    """Abstract interface for configuration management"""

    @abstractmethod
    def load_project_config(self, project_path: Path) -> Optional[ProjectConfig]:
        """Load project configuration from .specify/config.toml"""
        pass

    @abstractmethod
    def save_project_config(self, project_path: Path, config: ProjectConfig) -> bool:
        """Save project configuration to .specify/config.toml"""
        pass

    @abstractmethod
    def load_global_config(self) -> Optional[ProjectConfig]:
        """Load global configuration from ~/.specify/config.toml"""
        pass

    @abstractmethod
    def save_global_config(self, config: ProjectConfig) -> bool:
        """Save global configuration to ~/.specify/config.toml"""
        pass

    @abstractmethod
    def get_merged_config(self, project_path: Path) -> ProjectConfig:
        """Get merged configuration (global defaults + project overrides)"""
        pass

    @abstractmethod
    def validate_branch_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """Validate branch naming pattern"""
        pass

    @abstractmethod
    def expand_branch_name(self, pattern: str, context: Dict[str, str]) -> str:
        """Expand branch name pattern with context variables"""
        pass

    @abstractmethod
    def validate_branch_name_against_rules(
        self, branch_name: str, validation_rules: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """Validate a generated branch name against validation rules"""
        pass

    @abstractmethod
    def validate_branch_naming_config(
        self, config: "BranchNamingConfig"
    ) -> Tuple[bool, Optional[str]]:
        """Validate a complete BranchNamingConfig object"""
        pass

    @abstractmethod
    def generate_branch_name(
        self, pattern: str, context: Dict[str, str], validation_rules: List[str]
    ) -> Tuple[str, bool, Optional[str]]:
        """Generate and validate a branch name from pattern and context"""
        pass

    @abstractmethod
    def expand_special_placeholders(self, pattern: str) -> str:
        """Expand special placeholders like {number-3}, {date}, {datetime}"""
        pass

    @abstractmethod
    def backup_config(self, project_path: Path) -> Path:
        """Create backup of project configuration"""
        pass

    @abstractmethod
    def restore_config(self, project_path: Path, backup_path: Path) -> bool:
        """Restore configuration from backup"""
        pass


class TomlConfigService(ConfigService):
    """TOML-based configuration service implementation"""

    def __init__(self):
        self._global_config_dir = Path.home() / ".specify"
        self._global_config_file = self._global_config_dir / "config.toml"

    def load_project_config(self, project_path: Path) -> Optional[ProjectConfig]:
        """Load project configuration from .specify/config.toml"""
        config_file = project_path / ".specify" / "config.toml"

        if not config_file.exists():
            return None

        try:
            with open(config_file, "rb") as f:
                data = tomllib.load(f)
            return ProjectConfig.from_dict(data)
        except (OSError, tomllib.TOMLDecodeError, KeyError):
            # Log error in real implementation
            return None

    def save_project_config(self, project_path: Path, config: ProjectConfig) -> bool:
        """Save project configuration to .specify/config.toml"""
        try:
            config_dir = project_path / ".specify"
            config_dir.mkdir(exist_ok=True)

            config_file = config_dir / "config.toml"
            data = config.to_dict()

            with open(config_file, "wb") as f:
                tomli_w.dump(data, f)
            return True
        except (OSError, PermissionError):
            # Log error in real implementation
            return False

    def load_global_config(self) -> Optional[ProjectConfig]:
        """Load global configuration from ~/.specify/config.toml"""
        if not self._global_config_file.exists():
            return None

        try:
            with open(self._global_config_file, "rb") as f:
                data = tomllib.load(f)
            return ProjectConfig.from_dict(data)
        except (OSError, tomllib.TOMLDecodeError, KeyError):
            # Log error in real implementation
            return None

    def save_global_config(self, config: ProjectConfig) -> bool:
        """Save global configuration to ~/.specify/config.toml"""
        try:
            self._global_config_dir.mkdir(exist_ok=True)
            data = config.to_dict()

            with open(self._global_config_file, "wb") as f:
                tomli_w.dump(data, f)
            return True
        except (OSError, PermissionError):
            # Log error in real implementation
            return False

    def get_merged_config(self, project_path: Path) -> ProjectConfig:
        """Get merged configuration (global defaults + project overrides)"""
        # Start with defaults
        merged = ProjectConfig.create_default("merged-config")

        # Apply global config if it exists
        global_config = self.load_global_config()
        if global_config:
            # Merge global settings
            merged.branch_naming = global_config.branch_naming
            merged.template_settings = global_config.template_settings

        # Apply project config if it exists
        project_config = self.load_project_config(project_path)
        if project_config:
            # Project config overrides global/defaults
            merged.name = project_config.name
            merged.branch_naming = project_config.branch_naming
            merged.template_settings = project_config.template_settings
        else:
            # No project config, use project directory name
            merged.name = project_path.name

        return merged

    def validate_branch_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """Validate branch naming pattern"""
        if not pattern:
            return False, "Pattern cannot be empty"

        if not pattern.strip():
            return False, "Pattern cannot be empty or whitespace only"

        if pattern == "{}":
            return False, "Pattern cannot be just empty braces"

        # Check for unclosed braces
        open_count = pattern.count("{")
        close_count = pattern.count("}")
        if open_count != close_count:
            return False, "Mismatched braces in pattern"
        
        # Check for properly nested braces (no } before matching {)
        brace_depth = 0
        for char in pattern:
            if char == "{":
                brace_depth += 1
            elif char == "}":
                if brace_depth == 0:
                    return False, "Closing brace without matching opening brace"
                brace_depth -= 1

        # Check for invalid characters in the pattern itself
        if " " in pattern:
            return False, "Pattern cannot contain spaces"

        if pattern.isupper():
            return False, "Pattern cannot be all uppercase"

        if "." in pattern:
            return False, "Pattern cannot contain dots"

        if pattern.startswith("/") or pattern.endswith("/"):
            return False, "Pattern cannot start or end with slash"

        if "//" in pattern:
            return False, "Pattern cannot contain double slashes"

        if ":" in pattern:
            return False, "Pattern cannot contain colons"

        if "\\" in pattern:
            return False, "Pattern cannot contain backslashes"

        # Check for invalid characters in variable names
        var_pattern = re.compile(r"\{([^}]+)\}")
        matches = var_pattern.findall(pattern)

        for var_name in matches:
            if not var_name:
                return False, "Empty variable name in braces"
            # Allow alphanumeric, hyphens, and underscores in variable names
            if not re.match(r"^[a-zA-Z0-9_-]+$", var_name):
                return False, f"Invalid characters in variable name: {var_name}"

        return True, None

    def expand_branch_name(self, pattern: str, context: Dict[str, str]) -> str:
        """Expand branch name pattern with context variables"""
        result = pattern

        # First, expand special placeholders like {number-3}, {date}, etc.
        result = self.expand_special_placeholders(result)

        # Find all variables in the pattern
        var_pattern = re.compile(r"\{([^}]+)\}")
        matches = var_pattern.findall(result)

        for var_name in matches:
            placeholder = f"{{{var_name}}}"
            value = context.get(var_name, placeholder)  # Keep placeholder if not found
            result = result.replace(placeholder, value)

        return result

    def validate_branch_name_against_rules(
        self, branch_name: str, validation_rules: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """Validate a generated branch name against validation rules"""
        for rule in validation_rules:
            # Max length rules
            if rule.startswith("max_length_"):
                try:
                    max_length = int(rule.split("_")[-1])
                    if len(branch_name) > max_length:
                        return False, f"Branch name exceeds maximum length of {max_length}"
                except ValueError:
                    return False, f"Invalid max_length rule: {rule}"

            # Lowercase only rule
            elif rule == "lowercase_only":
                if not branch_name.islower():
                    return False, "Branch name must be lowercase only"

            # No spaces rule
            elif rule == "no_spaces":
                if " " in branch_name:
                    return False, "Branch name cannot contain spaces"

            # Alphanumeric dash only rule
            elif rule == "alphanumeric_dash_only":
                if not re.match(r"^[a-z0-9-]+$", branch_name):
                    return False, "Branch name can only contain lowercase letters, numbers, and dashes"

            # Alphanumeric dash slash only rule
            elif rule == "alphanumeric_dash_slash_only":
                if not re.match(r"^[a-z0-9-/]+$", branch_name):
                    return False, "Branch name can only contain lowercase letters, numbers, dashes, and slashes"

            # No leading/trailing dashes
            elif rule == "no_leading_trailing_dashes":
                if branch_name.startswith("-") or branch_name.endswith("-"):
                    return False, "Branch name cannot start or end with a dash"

            # No double dashes
            elif rule == "no_double_dashes":
                if "--" in branch_name:
                    return False, "Branch name cannot contain double dashes"

            # No dots
            elif rule == "no_dots":
                if "." in branch_name:
                    return False, "Branch name cannot contain dots"

            # Valid git branch name
            elif rule == "valid_git_branch":
                # Git branch name restrictions
                invalid_chars = [" ", "~", "^", ":", "?", "*", "[", "\\"]
                for char in invalid_chars:
                    if char in branch_name:
                        return False, f"Branch name cannot contain '{char}' (invalid for git)"

                if branch_name.startswith(".") or branch_name.endswith("."):
                    return False, "Branch name cannot start or end with a dot"

                if branch_name.endswith("/"):
                    return False, "Branch name cannot end with a slash"

                if branch_name.startswith("/"):
                    return False, "Branch name cannot start with a slash"

                if "//" in branch_name:
                    return False, "Branch name cannot contain double slashes"

            # Unknown rule - warn but don't fail
            elif rule and rule not in ["", "none"]:
                # In production, you might want to log this instead
                pass

        return True, None

    def validate_branch_naming_config(
        self, config: "BranchNamingConfig"
    ) -> Tuple[bool, Optional[str]]:
        """Validate a complete BranchNamingConfig object"""
        from ..models.config import BranchNamingConfig

        if not isinstance(config, BranchNamingConfig):
            return False, "Config must be a BranchNamingConfig instance"

        if not config.patterns:
            return False, "At least one branch pattern is required"

        # Validate each pattern
        for pattern in config.patterns:
            is_valid, error_msg = self.validate_branch_pattern(pattern)
            if not is_valid:
                return False, f"Invalid pattern '{pattern}': {error_msg}"

        # Validate validation rules are known
        known_rules = {
            "max_length_50", "max_length_60", "max_length_80", "max_length_100",
            "lowercase_only", "no_spaces", "alphanumeric_dash_only",
            "alphanumeric_dash_slash_only", "no_leading_trailing_dashes",
            "no_double_dashes", "no_dots", "valid_git_branch"
        }

        for rule in config.validation_rules:
            if not rule.startswith("max_length_") and rule not in known_rules:
                return False, f"Unknown validation rule: {rule}"

        return True, None

    def generate_branch_name(
        self, pattern: str, context: Dict[str, str], validation_rules: List[str]
    ) -> Tuple[str, bool, Optional[str]]:
        """Generate and validate a branch name from pattern and context"""
        # First validate the pattern
        pattern_valid, pattern_error = self.validate_branch_pattern(pattern)
        if not pattern_valid:
            return "", False, f"Invalid pattern: {pattern_error}"

        # Expand the pattern with context
        branch_name = self.expand_branch_name(pattern, context)

        # Check if all placeholders were filled
        if "{" in branch_name and "}" in branch_name:
            # Find unfilled placeholders
            unfilled = re.findall(r"\{([^}]+)\}", branch_name)
            return branch_name, False, f"Unfilled placeholders: {', '.join(unfilled)}"

        # Validate against rules
        rules_valid, rules_error = self.validate_branch_name_against_rules(
            branch_name, validation_rules
        )
        if not rules_valid:
            return branch_name, False, rules_error

        return branch_name, True, None

    def expand_special_placeholders(self, pattern: str) -> str:
        """Expand special placeholders like {number-3}, {date}, {datetime}"""
        result = pattern

        # Handle numbered placeholders like {number-3} -> 001
        number_pattern = re.compile(r"\{number(?:-(\d+))?\}")
        
        def replace_number(match):
            width = int(match.group(1)) if match.group(1) else 3
            # Generate next number (for now, default to 001)
            # In a real implementation, this would query git or a counter
            return "1".zfill(width)
        
        result = number_pattern.sub(replace_number, result)

        # Handle date placeholder
        if "{date}" in result:
            date_str = datetime.now().strftime("%Y-%m-%d")
            result = result.replace("{date}", date_str)

        # Handle datetime placeholder
        if "{datetime}" in result:
            datetime_str = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            result = result.replace("{datetime}", datetime_str)

        # Handle timestamp placeholder
        if "{timestamp}" in result:
            timestamp_str = str(int(datetime.now().timestamp()))
            result = result.replace("{timestamp}", timestamp_str)

        # Handle boolean placeholder (defaults to true/false)
        if "{boolean}" in result:
            result = result.replace("{boolean}", "true")

        return result

    def backup_config(self, project_path: Path) -> Path:
        """Create backup of project configuration"""
        config_file = project_path / ".specify" / "config.toml"

        # Create backup directory (and parent directories)
        backup_dir = project_path / ".specify" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"config_backup_{timestamp}.toml"

        if not config_file.exists():
            # Create empty backup file to satisfy contract
            backup_path.touch()
            return backup_path

        shutil.copy2(config_file, backup_path)
        return backup_path

    def restore_config(self, project_path: Path, backup_path: Path) -> bool:
        """Restore configuration from backup"""
        if not backup_path.exists():
            return False

        try:
            config_dir = project_path / ".specify"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.toml"

            shutil.copy2(backup_path, config_file)
            return True
        except (OSError, PermissionError):
            # Log error in real implementation
            return False

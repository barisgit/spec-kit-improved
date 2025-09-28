"""
Branch Naming Helper - focused on branch naming pattern application.

This helper handles:
- Branch pattern application
- Branch name creation and validation
- Pattern completion and suggestions
- Spec ID validation
"""

import re
from typing import Dict, List, Optional, Tuple

from .configuration_helper import ConfigurationHelper


class BranchNamingHelper:
    """Helper for branch naming operations."""

    def __init__(self):
        """Initialize with configuration helper."""
        self._config_helper = ConfigurationHelper()

    def apply_branch_pattern(self, pattern: str, **kwargs) -> str:
        """
        Apply variables to branch naming pattern.

        Args:
            pattern: Branch naming pattern with placeholders
            **kwargs: Variables to substitute in pattern

        Returns:
            str: Pattern with variables applied
        """
        try:
            return pattern.format(**kwargs)
        except KeyError as e:
            # If variable is missing, leave placeholder as-is for now
            missing_var = str(e).strip("'\"")
            return pattern.replace("{" + missing_var + "}", f"[{missing_var}]")

    def create_branch_name(self, description: str, feature_num: str) -> str:
        """
        Create branch name following project patterns.

        Args:
            description: Feature description
            feature_num: Feature number

        Returns:
            str: Generated branch name
        """
        config = self._config_helper.get_branch_naming_config()
        pattern = config.get("pattern", "{feature_num}-feature-{description}")

        # Clean description for use in branch name
        clean_description = self._clean_description_for_branch(description)

        return self.apply_branch_pattern(
            pattern,
            feature_num=feature_num,
            description=clean_description,
            project_name=self._config_helper.get_project_name(),
        )

    def validate_branch_name_against_patterns(
        self, branch_name: str, patterns: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate branch name against configured patterns.

        Args:
            branch_name: Branch name to validate
            patterns: Optional list of patterns to validate against

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not patterns:
            config = self._config_helper.get_branch_naming_config()
            # Convert pattern to regex for validation
            pattern = config.get("pattern", "{feature_num}-feature-{description}")
            patterns = [self._pattern_to_regex(pattern)]

        for pattern in patterns:
            if re.match(pattern, branch_name):
                return True, None

        return (
            False,
            f"Branch name '{branch_name}' does not match any configured patterns",
        )

    def validate_spec_id_format(self, spec_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate spec ID format.

        Args:
            spec_id: Spec ID to validate

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Basic spec ID validation - should be numeric or alphanumeric
        if not spec_id:
            return False, "Spec ID cannot be empty"

        # Allow various formats: 001, 1, feature-001, etc.
        if re.match(r"^[0-9]+$", spec_id):
            return True, None  # Pure numeric

        if re.match(r"^[a-zA-Z0-9-_]+$", spec_id):
            return True, None  # Alphanumeric with separators

        return (
            False,
            "Spec ID must contain only letters, numbers, hyphens, and underscores",
        )

    def complete_branch_name(
        self,
        partial_name: str,
        available_branches: Optional[List[str]] = None,
        max_suggestions: int = 5,
    ) -> List[str]:
        """
        Provide completion suggestions for partial branch names.

        Args:
            partial_name: Partial branch name to complete
            available_branches: List of available branches to suggest from
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List[str]: List of completion suggestions
        """
        if not available_branches:
            available_branches = []

        suggestions = []

        # Get pattern-based suggestions
        pattern_suggestions = self._complete_against_pattern(partial_name)
        suggestions.extend(pattern_suggestions)

        # Filter existing branches that match
        for branch in available_branches:
            if branch.startswith(partial_name) and branch not in suggestions:
                suggestions.append(branch)

        return suggestions[:max_suggestions]

    def _complete_against_pattern(
        self, partial_name: str, max_suggestions: int = 3
    ) -> List[str]:
        """
        Generate completion suggestions based on naming patterns.

        Args:
            partial_name: Partial name to complete
            max_suggestions: Maximum suggestions to generate

        Returns:
            List[str]: Pattern-based suggestions
        """
        config = self._config_helper.get_branch_naming_config()
        config.get("pattern", "{feature_num}-feature-{description}")

        suggestions = []

        # If partial name looks like it starts with a number, suggest feature patterns
        if re.match(r"^\d+", partial_name):
            # Extract number part
            match = re.match(r"^(\d+)", partial_name)
            if match:
                num = match.group(1)
                base_suggestions = [
                    f"{num}-feature-",
                    f"{num}-bugfix-",
                    f"{num}-enhancement-",
                ]
                suggestions.extend(
                    [s for s in base_suggestions if s.startswith(partial_name)]
                )

        # If it looks like a feature description, suggest with common prefixes
        elif partial_name and not partial_name.startswith(
            ("feature/", "feat/", "fix/", "hotfix/")
        ):
            feature_helper = self._get_feature_helper()
            next_num = feature_helper.get_next_feature_number()
            suggestions.extend(
                [
                    f"{next_num}-feature-{partial_name}",
                    f"feature/{partial_name}",
                    f"feat/{partial_name}",
                ]
            )

        return suggestions[:max_suggestions]

    def branch_to_directory_name(
        self, branch_name: str, naming_config: Optional[Dict] = None
    ) -> str:
        """
        Convert branch name to directory name following project conventions.

        Args:
            branch_name: Branch name to convert
            naming_config: Optional naming configuration

        Returns:
            str: Directory name
        """
        if not naming_config:
            naming_config = self._config_helper.get_branch_naming_config()

        # Get the suffix part that would be used for directory naming
        return self._branch_to_directory_suffix(branch_name)

    def _branch_to_directory_suffix(self, branch_name: str) -> str:
        """
        Extract directory suffix from branch name.

        Args:
            branch_name: Branch name to process

        Returns:
            str: Directory suffix
        """
        # Remove common prefixes
        prefixes_to_remove = ["feature/", "feat/", "bugfix/", "fix/", "hotfix/"]

        for prefix in prefixes_to_remove:
            if branch_name.startswith(prefix):
                return branch_name[len(prefix) :]

        # Handle numbered patterns like "001-feature-name"
        match = re.match(r"^(\d+)[-_](feature|feat|bugfix|fix)[-_](.+)$", branch_name)
        if match:
            number, _, description = match.groups()
            return f"{number}-{description}"

        # Default: return as-is
        return branch_name

    def _clean_description_for_branch(self, description: str) -> str:
        """
        Clean description for use in branch names.

        Args:
            description: Raw description

        Returns:
            str: Cleaned description suitable for branch names
        """
        # Convert to lowercase
        clean = description.lower()

        # Replace spaces and special characters with hyphens
        clean = re.sub(r"[^a-z0-9-]", "-", clean)

        # Remove multiple consecutive hyphens
        clean = re.sub(r"-+", "-", clean)

        # Remove leading/trailing hyphens
        clean = clean.strip("-")

        return clean

    def _pattern_to_regex(self, pattern: str) -> str:
        """
        Convert branch naming pattern to regex for validation.

        Args:
            pattern: Branch naming pattern

        Returns:
            str: Regex pattern for validation
        """
        # Escape special regex characters
        regex_pattern = re.escape(pattern)

        # Replace escaped placeholders with regex groups
        replacements = {
            r"\{feature_num\}": r"\\d+",
            r"\{description\}": r"[a-z0-9-]+",
            r"\{project_name\}": r"[a-zA-Z0-9-_]+",
        }

        for placeholder, regex_group in replacements.items():
            regex_pattern = regex_pattern.replace(placeholder, regex_group)

        return f"^{regex_pattern}$"

    def _get_feature_helper(self):
        """Get feature discovery helper (avoid circular import)."""
        from .feature_discovery_helper import FeatureDiscoveryHelper

        return FeatureDiscoveryHelper()

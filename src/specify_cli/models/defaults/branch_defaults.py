"""
Branch naming defaults for SpecifyX

This module provides centralized, immutable branch naming configurations that are
packaged with SpecifyX. These are developer defaults, not user configuration.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Final, List


@dataclass(frozen=True)
class BranchNamingPattern:
    """Single branch naming pattern configuration"""

    name: str
    description: str
    patterns: List[str]
    validation_rules: List[str]

    def __post_init__(self):
        """Validate branch naming pattern configuration"""
        if not self.name or not self.patterns:
            raise ValueError("Name and patterns must be non-empty")


@dataclass(frozen=True)
class BranchNamingDefaults:
    """Developer defaults for branch naming configurations - packaged with SpecifyX"""

    # Supported branch naming patterns
    PATTERNS: Final[List[BranchNamingPattern]] = field(
        default_factory=lambda: [
            BranchNamingPattern(
                name="traditional-spec",
                description="Traditional numbered branches with hotfixes",
                patterns=[
                    "{spec-id}-{feature-name}",
                    "hotfix/{bug-id}",
                    "main",
                    "development",
                ],
                validation_rules=[
                    "max_length_50",
                    "lowercase_only",
                    "no_spaces",
                    "alphanumeric_dash_slash_only",
                    "valid_git_branch",
                ],
            ),
            BranchNamingPattern(
                name="branch-type",
                description="Modern namespaced branches with type prefixes",
                patterns=[
                    "feature/{feature-name}",
                    "hotfix/{bug-id}",
                    "bugfix/{bug-id}",
                    "main",
                    "development",
                ],
                validation_rules=[
                    "max_length_50",
                    "lowercase_only",
                    "no_spaces",
                    "alphanumeric_dash_slash_only",
                    "valid_git_branch",
                ],
            ),
            BranchNamingPattern(
                name="numbered-type",
                description="Numbered branches with organized type prefixes",
                patterns=[
                    "feature/{spec-id}-{feature-name}",
                    "hotfix/{bug-id}",
                    "release/{version}",
                    "main",
                    "development",
                ],
                validation_rules=[
                    "max_length_50",
                    "lowercase_only",
                    "no_spaces",
                    "alphanumeric_dash_slash_only",
                    "valid_git_branch",
                ],
            ),
            BranchNamingPattern(
                name="team-based",
                description="Team-based organization with workflow support",
                patterns=[
                    "{team}/{feature-name}",
                    "hotfix/{bug-id}",
                    "release/{version}",
                    "main",
                    "development",
                ],
                validation_rules=[
                    "max_length_50",
                    "lowercase_only",
                    "no_spaces",
                    "alphanumeric_dash_slash_only",
                    "valid_git_branch",
                ],
            ),
            BranchNamingPattern(
                name="no-branch",
                description="Single-branch workflow - develop all features on current branch or manually created branch",
                patterns=[
                    "current",  # Special pattern indicating no branch creation
                ],
                validation_rules=[
                    # No validation rules needed for no-branch workflow
                ],
            ),
        ]
    )

    # Default branch naming pattern when none specified
    DEFAULT_PATTERN_NAME: Final[str] = "branch-type"

    # Default validation rules for branch names
    DEFAULT_VALIDATION_RULES: Final[List[str]] = field(
        default_factory=lambda: [
            "max_length_50",
            "lowercase_only",
            "no_spaces",
            "alphanumeric_dash_slash_only",
        ]
    )

    # Default branch patterns
    DEFAULT_PATTERNS: Final[List[str]] = field(
        default_factory=lambda: [
            "feature/{feature-name}",
            "hotfix/{bug-id}",
            "bugfix/{bug-id}",
            "main",
            "development",
        ]
    )

    def get_pattern_by_name(self, name: str) -> BranchNamingPattern:
        """Get branch naming pattern by name"""
        for pattern in self.PATTERNS:
            if pattern.name.lower() == name.lower():
                return pattern

        # Return default pattern if not found
        return self.get_default_pattern()

    def get_default_pattern(self) -> BranchNamingPattern:
        """Get default branch naming pattern"""
        return self.get_pattern_by_name(self.DEFAULT_PATTERN_NAME)

    def get_all_pattern_names(self) -> List[str]:
        """Get list of all supported pattern names"""
        return [pattern.name for pattern in self.PATTERNS]

    def get_pattern_choices(self) -> List[str]:
        """Get list of pattern names for CLI choices"""
        return [pattern.name for pattern in self.PATTERNS]

    def get_display_names(self) -> Dict[str, str]:
        """Get mapping of pattern name to display description"""
        return {pattern.name: pattern.description for pattern in self.PATTERNS}

    def is_supported_pattern(self, name: str) -> bool:
        """Check if branch naming pattern is officially supported"""
        return any(pattern.name.lower() == name.lower() for pattern in self.PATTERNS)

    def validate_pattern_name(self, name: str) -> str:
        """Validate and normalize pattern name"""
        if not name:
            return self.DEFAULT_PATTERN_NAME

        # Check if supported
        if self.is_supported_pattern(name):
            return name.lower()

        # Allow unknown patterns with warning
        return name.lower()

    def get_pattern_options_for_ui(self) -> Dict[str, Dict[str, Any]]:
        """Get pattern options formatted for UI selection"""
        options = {}
        for pattern in self.PATTERNS:
            options[pattern.name] = {
                "description": pattern.description,
                "display": pattern.description,
                "patterns": pattern.patterns.copy(),
                "validation_rules": pattern.validation_rules.copy(),
            }
        return options


# Module-level singleton for easy access
BRANCH_DEFAULTS = BranchNamingDefaults()

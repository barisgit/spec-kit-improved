"""
Type-safe script utilities module for SpecifyX generated scripts.

This module provides a ScriptHelpers class with common utilities used by generated Python scripts
to reduce code duplication and improve maintainability. It extracts common patterns for:
- Git repository operations
- SpecifyX project configuration loading
- Branch naming pattern application
- Feature directory discovery
- Sequential feature numbering
- Standalone template rendering with Jinja2
- Click CLI decorators and utilities

Key Features:
- render_template_standalone(): Render individual .j2 templates without full project initialization
- ScriptHelpers class with type-safe utilities for common script operations
- Platform-aware template rendering with context variables
- File permission handling for executable scripts

All methods are fully type-hinted and include comprehensive error handling.
"""

import json
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Typer and Rich imports for CLI utilities
import typer
from rich.console import Console

from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.project import TemplateContext
from specify_cli.services import CommandLineGitService, TomlConfigService
from specify_cli.services.template_service import JinjaTemplateService

# Create a console instance for script output
console = Console()


class ScriptHelpers:
    """
    Utilities class for SpecifyX generated Python scripts.

    Provides common utilities with better IDE support and autocomplete.
    All methods are type-safe and include comprehensive error handling.

    Example usage:
        from specify_cli.utils.script_helpers import ScriptHelpers

        helpers = ScriptHelpers()
        repo_root = helpers.get_repo_root()
        branch = helpers.get_current_branch()
        config = helpers.load_project_config()
    """

    def __init__(self):
        """Initialize ScriptHelpers with SpecifyX services."""
        self._git_service = CommandLineGitService()
        self._config_service = TomlConfigService()
        self._template_service = JinjaTemplateService()

    def get_repo_root(self) -> Path:
        """
        Get repository root directory using git command.

        When scripts run from .specify/scripts/, we need to find the project root
        that contains the .specify directory, not the script execution directory.

        Returns:
            Path: Repository root directory. Falls back to current directory
                  if not in a git repository.
        """
        try:
            # Start from current working directory and walk up to find git repo
            current_dir = Path.cwd()

            # If we're in a .specify/scripts directory, go to project root
            if current_dir.name == "scripts" and current_dir.parent.name == ".specify":
                project_root = current_dir.parent.parent
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=project_root,
                )
                return Path(result.stdout.strip())

            # Otherwise, find git root normally
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            return Path.cwd()

    def get_current_branch(self) -> Optional[str]:
        """
        Get current git branch name using SpecifyX services.

        Returns:
            str: Current branch name, or None if branch cannot be determined
        """
        try:
            branch = self._git_service.get_current_branch(self.get_repo_root())
            # Fix: ensure we don't return string 'None' instead of None
            if branch == "None" or branch == "null" or not branch:
                return None
            return branch
        except Exception:
            # Fallback to direct git command from repository root
            try:
                repo_root = self.get_repo_root()
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=repo_root,  # Run from repository root, not current directory
                )
                branch = result.stdout.strip()
                # Fix: ensure we don't return string 'None' instead of None
                if branch == "None" or branch == "null" or not branch:
                    return None
                return branch
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None

    def load_project_config(self) -> Optional[Dict]:
        """
        Load SpecifyX project configuration from current directory.

        Returns:
            Dict: Project configuration dictionary, or None if not available
        """
        try:
            config = self._config_service.load_project_config(Path.cwd())

            # Handle both ProjectConfig objects and raw dictionaries
            if hasattr(config, "to_dict"):
                return config.to_dict()
            elif isinstance(config, dict):
                return config
            else:
                return None
        except Exception:
            return None

    def apply_branch_pattern(self, pattern: str, **kwargs) -> str:
        """
        Apply branch naming pattern with variable substitution.

        Supports both Jinja2-style ({{ variable }}) and simple ({variable}) patterns.
        Common variables: feature_num, feature_name, bug_id, version, team

        Args:
            pattern: Branch naming pattern with variables
            **kwargs: Variable values for substitution

        Returns:
            str: Branch name with variables substituted

        Example:
            helpers.apply_branch_pattern("feature/{feature_name}", feature_name="auth-system")
            # Returns: "feature/auth-system"
        """
        result = pattern

        # Handle both styles of variable substitution
        for key, value in kwargs.items():
            # Jinja2 style: {{ variable }}
            result = result.replace(f"{{{{ {key} }}}}", str(value))
            # Simple style: {variable}
            result = result.replace(f"{{{key}}}", str(value))

        return result

    def create_branch_name(self, description: str, feature_num: str) -> str:
        """
        Create clean branch name from feature description.

        Args:
            description: Feature description text
            feature_num: Feature number (e.g., "001", "042")

        Returns:
            str: Clean branch name suitable for git

        Example:
            helpers.create_branch_name("User Authentication System", "001")
            # Returns: "001-user-auth-system"
        """
        # Convert to lowercase and replace non-alphanumeric with hyphens
        clean = re.sub(r"[^a-z0-9]", "-", description.lower())
        # Remove multiple consecutive hyphens
        clean = re.sub(r"-+", "-", clean)
        # Remove leading/trailing hyphens
        clean = clean.strip("-")

        # Extract 2-3 meaningful words for feature name
        words = [w for w in clean.split("-") if w and len(w) > 2][:3]
        feature_name = "-".join(words) if words else "feature"

        return f"{feature_num}-{feature_name}"

    def validate_branch_name_against_patterns(
        self, branch_name: str, patterns: List[str]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate if a branch name matches any of the given patterns.

        Args:
            branch_name: The branch name to validate
            patterns: List of patterns to check against

        Returns:
            Tuple of (is_valid, error_message, matched_pattern)
            - is_valid: True if branch name matches at least one pattern
            - error_message: Detailed error if no patterns match
            - matched_pattern: The pattern that matched (if any)
        """
        if not branch_name:
            return False, "Branch name cannot be empty", None

        if not patterns:
            return False, "No patterns configured for validation", None

        # Try each pattern in order
        errors = []
        for pattern in patterns:
            is_valid, error = self._config_service.validate_branch_name_matches_pattern(
                branch_name, pattern
            )
            if is_valid:
                return True, None, pattern
            else:
                errors.append(f"Pattern '{pattern}': {error}")

        # None matched - create comprehensive error message
        error_msg = (
            f"Branch name '{branch_name}' doesn't match any configured pattern:\n"
        )
        for error in errors:
            error_msg += f"  - {error}\n"
        error_msg += f"\nAvailable patterns: {', '.join(patterns)}"

        return False, error_msg.strip(), None

    def validate_spec_id_format(self, spec_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate spec ID format (must be 3-digit number like '001', '042').

        Args:
            spec_id: The spec ID to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not spec_id:
            return False, "Spec ID cannot be empty"

        if not re.match(r"^\d{3}$", spec_id):
            return (
                False,
                f"Spec ID must be a 3-digit number (e.g., '001', '042'), got: '{spec_id}'",
            )

        return True, None

    def check_spec_id_exists(
        self, spec_id: str, specs_dir: Optional[Path] = None
    ) -> Tuple[bool, Optional[Path]]:
        """
        Check if a spec ID already exists in the specs directory.

        Args:
            spec_id: The spec ID to check (e.g., '001')
            specs_dir: Directory containing spec folders. Defaults to ./specs/

        Returns:
            Tuple of (exists, path_if_exists)
        """
        if specs_dir is None:
            specs_dir = self.get_repo_root() / "specs"

        if not specs_dir.exists():
            return False, None

        # Look for directories that start with spec_id
        for dir_path in specs_dir.glob(f"{spec_id}-*"):
            if dir_path.is_dir():
                return True, dir_path

        return False, None

    def check_branch_exists(self, branch_name: str) -> bool:
        """
        Check if a git branch already exists or was already used for feature creation.

        Since git branches don't exist until there's a commit, we check:
        1. If there are commits, use git to check branches
        2. If no commits, check if current branch matches (branch was created but no commits)

        Args:
            branch_name: Name of the branch to check

        Returns:
            True if branch exists or was already used, False otherwise
        """
        try:
            repo_root = self.get_repo_root()

            # Check if we have any commits in the repo
            has_commits = (
                subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                ).returncode
                == 0
            )

            if has_commits:
                # With commits, we can use standard git branch checking
                result = subprocess.run(
                    ["git", "branch", "--list", branch_name],
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                )
                return branch_name in result.stdout
            else:
                # No commits yet - check current branch name
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                )
                current_branch = result.stdout.strip()
                return current_branch == branch_name

        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def complete_branch_name(
        self, partial_branch: str, patterns: List[str], spec_id: Optional[str] = None
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Intelligently complete a partial branch name using configured patterns.

        Examples:
        - "feature/xxx-auth-system" + pattern "feature/{spec-id}-{feature-name}" → "feature/001-auth-system"
        - "xxx-auth-system" + pattern "{spec-id}-{feature-name}" → "001-auth-system"
        - "feature/020-auth-system" → "feature/020-auth-system" (already complete)

        Args:
            partial_branch: User-provided branch name (may contain 'xxx' placeholders)
            patterns: List of valid patterns to match against
            spec_id: Optional specific spec ID to use instead of auto-generating

        Returns:
            Tuple of (completed_branch_name, success, error_message)
        """
        if not partial_branch:
            return partial_branch, False, "Branch name cannot be empty"

        if not patterns:
            return partial_branch, False, "No patterns available for completion"

        # If branch name doesn't contain 'xxx', check if it already matches a pattern
        if "xxx" not in partial_branch.lower():
            is_valid, error, matched_pattern = (
                self.validate_branch_name_against_patterns(partial_branch, patterns)
            )
            if is_valid:
                return partial_branch, True, None  # Already complete and valid

        # Try to complete against each pattern
        for pattern in patterns:
            completed_branch = self._complete_against_pattern(
                partial_branch, pattern, spec_id
            )
            if completed_branch:
                # Validate the completed branch
                is_valid, error, _ = self.validate_branch_name_against_patterns(
                    completed_branch, [pattern]
                )
                if is_valid:
                    return completed_branch, True, None

        # No pattern could complete the branch name
        available_patterns = ", ".join(patterns[:3])
        return (
            partial_branch,
            False,
            f"Cannot complete '{partial_branch}' using available patterns: {available_patterns}",
        )

    def _complete_against_pattern(
        self, partial_branch: str, pattern: str, spec_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Try to complete a partial branch name against a specific pattern.

        Args:
            partial_branch: Partial branch name with 'xxx' placeholders
            pattern: Pattern to complete against
            spec_id: Optional specific spec ID to use

        Returns:
            Completed branch name if successful, None otherwise
        """
        # Handle static patterns (no variables)
        if "{" not in pattern:
            return partial_branch if partial_branch == pattern else None

        # For patterns with variables, try to match structure and complete
        partial_lower = partial_branch.lower()

        # Replace 'xxx' with spec-id in partial branch
        if "xxx" in partial_lower:
            if spec_id is None:
                # Auto-generate spec ID
                spec_id = self.get_next_feature_number()

            # Replace xxx with the spec ID
            completed_branch = re.sub(
                r"xxx", spec_id, partial_branch, flags=re.IGNORECASE
            )

            # Check if completed branch structure matches pattern structure
            pattern_parts = pattern.split("/")
            completed_parts = completed_branch.split("/")

            if len(pattern_parts) == len(completed_parts):
                # Basic structure matches, return completed branch
                return completed_branch

        return None

    def get_next_feature_number(self, specs_dir: Optional[Path] = None) -> str:
        """
        Get next sequential feature number with zero padding.

        Args:
            specs_dir: Directory containing spec folders. Defaults to ./specs/

        Returns:
            str: Next feature number with zero padding (e.g., "001", "042")
        """
        if specs_dir is None:
            specs_dir = self.get_repo_root() / "specs"

        highest = 0

        if specs_dir.exists():
            for dir_path in specs_dir.iterdir():
                if dir_path.is_dir():
                    match = re.match(r"^(\d+)", dir_path.name)
                    if match:
                        number = int(match.group(1))
                        highest = max(highest, number)

        return f"{highest + 1:03d}"

    def branch_to_directory_name(
        self, branch_name: str, feature_num: Optional[str] = None
    ) -> str:
        """
        Convert branch name to smart sequential directory name.

        Rules:
        - Always starts with sequential number (001-, 002-, etc.)
        - feature/feature-name -> 001-feature-name (removes redundant 'feature')
        - 001-some-branch -> 001-some-branch (keeps as-is if already numbered)
        - 001/some-branch -> 001-some-branch (replaces slash with dash)
        - any/thing -> 001-thing (removes prefix, adds number)

        Args:
            branch_name: Git branch name that may contain slashes or numbers
            feature_num: Sequential number to use (auto-generated if None)

        Returns:
            str: Smart directory name with format: 001-feature-name
        """
        # Get next feature number if not provided
        if feature_num is None:
            specs_dir = self.get_repo_root() / "specs"
            feature_num = self.get_next_feature_number(specs_dir)

        # Handle already numbered branches (001-something or 001/something)
        if re.match(r"^\d{3}[-/]", branch_name):
            # Extract the user's number and the part after it
            match = re.match(r"^(\d{3})[-/](.+)", branch_name)
            if match:
                user_number = match.group(1)
                part_after_number = match.group(2)
                return f"{user_number}-{part_after_number.replace('/', '-')}"

        # Handle prefix/name patterns (feature/name, hotfix/name, etc.)
        if "/" in branch_name:
            prefix, name = branch_name.split("/", 1)

            # Special case: feature/001-feature-name -> 001-feature-name (preserve existing number)
            if re.match(r"^\d{3}-", name):
                return name.replace("/", "-")

            # Preserve prefix for context: feature/auth-system -> 001-feature-auth-system
            # Remove redundancy: feature/feature-auth -> 001-feature-auth (not 001-feature-feature-auth)
            if name.startswith(prefix) or name.startswith(f"{prefix}-"):
                # feature/feature-auth -> 001-feature-auth
                clean_name = name
            else:
                # feature/auth-system -> 001-feature-auth-system
                clean_name = f"{prefix}-{name}"
            return f"{feature_num}-{clean_name.replace('/', '-')}"

        # Handle simple branch names (no slash, no number)
        return f"{feature_num}-{branch_name.replace('/', '-')}"

    def find_feature_directory(
        self, branch_name: Optional[str] = None
    ) -> Optional[Path]:
        """
        Find feature directory based on branch name or current branch.
        Uses smart matching to find directories created from branch names.

        Args:
            branch_name: Branch name to search for. Uses current branch if None.

        Returns:
            Path: Feature directory path, or None if not found
        """
        if branch_name is None:
            branch_name = self.get_current_branch()

        if not branch_name:
            return None

        specs_dir = self.get_repo_root() / "specs"
        if not specs_dir.exists():
            return None

        # Strategy 1: Find existing directory that matches this branch
        # Look for directories that could have been created from this branch name
        for dir_path in specs_dir.iterdir():
            if not dir_path.is_dir():
                continue

            dir_name = dir_path.name

            # Check if this directory could correspond to our branch
            if self._directory_matches_branch(dir_name, branch_name):
                return dir_path

        # Strategy 2: No existing directory found, return None
        # The caller can decide to create a new directory if needed
        return None

    def _directory_matches_branch(self, dir_name: str, branch_name: str) -> bool:
        """
        Check if a directory name could have been created from a branch name.

        Args:
            dir_name: Directory name (e.g., "001-want-setup-typer")
            branch_name: Branch name (e.g., "feature/want-setup-typer")

        Returns:
            bool: True if they match
        """
        # Exact match
        if dir_name == branch_name:
            return True

        # Check if directory follows numbered format (001-something)
        if re.match(r"^\d{3}-", dir_name):
            # Extract the part after the number
            dir_suffix = re.sub(r"^\d{3}-", "", dir_name)

            # Compare with various branch formats
            if branch_name == dir_suffix:
                return True

            # feature/want-setup-typer -> want-setup-typer
            if "/" in branch_name:
                branch_suffix = branch_name.split("/", 1)[1]
                if dir_suffix == branch_suffix.replace("/", "-"):
                    return True

            # feature/feature-name -> feature-name (handles redundant prefix)
            if "/" in branch_name:
                prefix, name = branch_name.split("/", 1)
                if dir_suffix == name.replace("/", "-"):
                    return True

            # Convert branch to what directory should be and compare
            expected_dir_suffix = self._branch_to_directory_suffix(branch_name)
            if dir_suffix == expected_dir_suffix:
                return True

        return False

    def _branch_to_directory_suffix(self, branch_name: str) -> str:
        """
        Convert branch name to the suffix part of directory name (without number).

        Args:
            branch_name: Branch name like "feature/want-setup-typer"

        Returns:
            str: Directory suffix like "feature-want-setup-typer" (preserves prefix)
        """
        # Handle prefix/name patterns - now preserving prefix
        if "/" in branch_name:
            prefix, name = branch_name.split("/", 1)

            # Special case: feature/001-something -> 001-something (extract after number)
            if re.match(r"^\d{3}-", name):
                return re.sub(r"^\d{3}-", "", name)

            # Preserve prefix: feature/auth -> feature-auth
            if name.startswith(prefix) or name.startswith(f"{prefix}-"):
                return name.replace("/", "-")
            else:
                return f"{prefix}-{name}".replace("/", "-")

        # Handle simple names
        return branch_name.replace("/", "-")

    def get_branch_naming_config(self) -> Dict:
        """
        Get branch naming configuration from project config with sensible defaults.

        Returns:
            Dict: Branch naming configuration with patterns and validation rules
        """
        project_config = self.load_project_config()

        if project_config and "project" in project_config:
            project_section = project_config["project"]
            if "branch_naming" in project_section:
                return project_section["branch_naming"]

        # Warn about missing project config
        console.print(
            "⚠️  Warning: No project configuration found. Using fallback branch naming patterns.",
            style="yellow",
        )
        console.print(
            "   Run 'specifyx init' to create proper configuration.", style="dim"
        )

        # Return default configuration if project config not available
        try:
            default_config = BranchNamingConfig()
            return default_config.to_dict()
        except Exception:
            # Fallback configuration - issue stronger warning
            console.print(
                "⚠️  Warning: Using emergency fallback configuration. Branch validation may not work correctly.",
                style="red",
            )
            return {
                "patterns": [
                    "{spec-id}-{feature-name}",
                    "hotfix/{bug-id}",
                    "bugfix/{bug-id}",
                    "main",
                    "development",
                ],
                "validation_rules": [
                    "max_length_50",
                    "lowercase_only",
                    "no_spaces",
                    "alphanumeric_dash_slash_only",
                ],
                "description": "Default branch naming configuration",
            }

    def validate_feature_description(
        self, description: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate feature description with SpecifyX validation and fallbacks.

        Args:
            description: Feature description to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Basic validation first
        if not description or not description.strip():
            return False, "Feature description cannot be empty"

        if len(description.strip()) < 3:
            return False, "Feature description must be at least 3 characters"

        if len(description.strip()) > 100:
            return False, "Feature description must be less than 100 characters"

        if not re.search(r"[a-zA-Z]", description):
            return False, "Feature description must contain at least one letter"

        return True, None

    def check_git_repository(self) -> bool:
        """
        Check if current directory is inside a git repository.

        Returns:
            bool: True if in a git repository, False otherwise
        """
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True, check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_feature_branch(self, branch_name: Optional[str] = None) -> bool:
        """
        Check if branch follows feature branch patterns.

        Args:
            branch_name: Branch name to check. Uses current branch if None.

        Returns:
            bool: True if branch follows feature patterns
        """
        if branch_name is None:
            branch_name = self.get_current_branch()

        if not branch_name:
            return False

        # Common feature branch patterns
        feature_patterns = [
            r"^\d{3}-",  # 001-feature-name
            r"^feature/",  # feature/name
            r"^feat/",  # feat/name
        ]

        return any(re.match(pattern, branch_name) for pattern in feature_patterns)

    def is_no_branch_workflow(self) -> bool:
        """
        Check if project is configured for no-branch workflow.

        Returns:
            bool: True if project uses no-branch workflow
        """
        branch_config = self.get_branch_naming_config()
        patterns = branch_config.get("patterns", [])
        return "current" in patterns

    def find_feature_directory_for_workflow(
        self, current_branch: Optional[str] = None
    ) -> Optional[Path]:
        """
        Find feature directory supporting both traditional and no-branch workflows.

        Args:
            current_branch: Branch name to search for. Uses current branch if None.

        Returns:
            Path: Feature directory path, or None if not found
        """
        if current_branch is None:
            current_branch = self.get_current_branch()

        if not current_branch:
            return None

        # Check if using no-branch workflow
        is_no_branch = self.is_no_branch_workflow()

        # For no-branch workflow or non-feature branches, find the most recent spec
        if is_no_branch or not self.is_feature_branch(current_branch):
            # First try to find by branch name (in case it matches somehow)
            feature_dir = self.find_feature_directory(current_branch)

            # If no match, look for most recent spec directory
            if not feature_dir:
                specs_dir = self.get_repo_root() / "specs"
                if specs_dir.exists():
                    spec_dirs = [
                        d
                        for d in specs_dir.iterdir()
                        if d.is_dir() and (d / "spec.md").exists()
                    ]
                    if spec_dirs:
                        # Sort by directory name (assuming numeric prefixes like 001-, 002-)
                        spec_dirs.sort(key=lambda x: x.name)
                        feature_dir = spec_dirs[-1]  # Get the most recent one

            return feature_dir
        else:
            # Traditional feature branch workflow
            return self.find_feature_directory(current_branch)

    def get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d")

    def get_project_name(self) -> str:
        """Get project name from config or directory name."""
        project_config = self.load_project_config()
        if project_config and project_config.get("name"):
            return project_config["name"]

        # Fallback to current directory name
        return self.get_repo_root().name

    def list_available_specs(self) -> List[Dict[str, str]]:
        """
        List all available spec directories with their IDs and names.

        Returns:
            List[Dict]: List of specs with 'id', 'name', and 'path' keys
        """
        specs_dir = self.get_repo_root() / "specs"
        if not specs_dir.exists():
            return []

        specs = []
        for spec_dir in specs_dir.iterdir():
            if spec_dir.is_dir() and (spec_dir / "spec.md").exists():
                spec_name = spec_dir.name
                # Extract spec ID (first 3 digits) if present
                spec_id_match = re.match(r"^(\d{3})-", spec_name)
                spec_id = spec_id_match.group(1) if spec_id_match else spec_name

                specs.append(
                    {"id": spec_id, "name": spec_name, "path": str(spec_dir.absolute())}
                )

        # Sort by spec ID/name
        specs.sort(key=lambda x: x["id"])
        return specs

    def find_spec_by_id(self, spec_id: str) -> Optional[Path]:
        """
        Find spec directory by ID.

        Args:
            spec_id: Spec ID to find (e.g., "001", "004")

        Returns:
            Path: Spec directory path, or None if not found
        """
        specs_dir = self.get_repo_root() / "specs"
        if not specs_dir.exists():
            return None

        # Normalize spec ID (ensure 3 digits)
        normalized_id = spec_id.zfill(3)

        for spec_dir in specs_dir.iterdir():
            if (
                spec_dir.is_dir()
                and (spec_dir / "spec.md").exists()
                and spec_dir.name.startswith(f"{normalized_id}-")
            ):
                return spec_dir

        return None

    def get_author_name(self) -> str:
        """Get author name from config or git config."""
        project_config = self.load_project_config()
        if project_config and project_config.get("template_settings", {}).get(
            "author_name"
        ):
            return project_config["template_settings"]["author_name"]

        # Fallback to git config
        try:
            result = subprocess.run(
                ["git", "config", "--get", "user.name"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "Unknown"

    def render_template_standalone(
        self,
        template_path: Path,
        context_dict: Dict[str, Any],
        output_path: Path,
        make_executable: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Render a standalone template file without going through full project initialization.

        This utility function allows individual template rendering for generated Python scripts
        and other standalone use cases. It handles both .j2 template files and regular files.

        Args:
            template_path: Path to the template file (can be .j2 or regular file)
            context_dict: Dictionary with template variables for rendering
            output_path: Path where the rendered content should be written
            make_executable: Whether to make the output file executable (default: False)

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)

        Example:
            helpers = ScriptHelpers()
            context = {
                'project_name': 'my-project',
                'author_name': 'John Doe',
                'feature_name': 'auth-system'
            }
            success, error = helpers.render_template_standalone(
                template_path=Path('template.j2'),
                context_dict=context,
                output_path=Path('output.py'),
                make_executable=True
            )
        """
        try:
            # Validate inputs
            if not template_path.exists():
                return False, f"Template file not found: {template_path}"

            if not template_path.is_file():
                return False, f"Template path is not a file: {template_path}"

            if not context_dict:
                context_dict = {}

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if template is a .j2 file that needs rendering
            if template_path.suffix == ".j2":
                # Use JinjaTemplateService for rendering
                JinjaTemplateService()

                try:
                    # Read template content
                    template_content = template_path.read_text(encoding="utf-8")

                    # Create a minimal TemplateContext from the provided dictionary
                    # Extract known fields from context_dict, use defaults for missing ones
                    template_context = TemplateContext(
                        project_name=context_dict.get("project_name", "unknown"),
                        project_description=context_dict.get("project_description", ""),
                        branch_name=context_dict.get("branch_name", ""),
                        feature_name=context_dict.get("feature_name", ""),
                        task_name=context_dict.get("task_name", ""),
                        author_name=context_dict.get("author_name", ""),
                        author_email=context_dict.get("author_email", ""),
                        creation_date=context_dict.get("creation_date", ""),
                        creation_year=context_dict.get("creation_year", ""),
                        ai_assistant=context_dict.get("ai_assistant", "claude"),
                        spec_number=context_dict.get("spec_number", ""),
                        spec_title=context_dict.get("spec_title", ""),
                        spec_type=context_dict.get("spec_type", "feature"),
                        # Add any extra variables as template_variables
                        template_variables={
                            k: v
                            for k, v in context_dict.items()
                            if k
                            not in {
                                "project_name",
                                "project_description",
                                "branch_name",
                                "feature_name",
                                "task_name",
                                "author_name",
                                "author_email",
                                "creation_date",
                                "creation_year",
                                "ai_assistant",
                                "spec_number",
                                "spec_title",
                                "spec_type",
                            }
                        },
                    )

                    # Create Jinja2 template from string content
                    from jinja2 import Environment

                    env = Environment(keep_trailing_newline=True)

                    # Add custom filters (same as in JinjaTemplateService)
                    def regex_replace(
                        value: str, pattern: str, replacement: str = ""
                    ) -> str:
                        try:
                            return re.sub(pattern, replacement, str(value))
                        except Exception:
                            return str(value)

                    # Type the filter properly for Jinja2
                    from typing import cast

                    from jinja2 import Environment

                    env.filters["regex_replace"] = cast(Any, regex_replace)

                    # Create template and render
                    jinja_template = env.from_string(template_content)

                    # Prepare context for rendering (similar to template service)
                    render_context = template_context.to_dict()

                    # Add platform-specific variables (same as in JinjaTemplateService)
                    import platform

                    try:
                        render_context.update(
                            {
                                "platform_system": platform.system(),
                                "platform_machine": platform.machine(),
                                "platform_python_version": platform.python_version(),
                                "is_windows": platform.system().lower() == "windows",
                                "is_macos": platform.system().lower() == "darwin",
                                "is_linux": platform.system().lower() == "linux",
                                "path_separator": "\\"
                                if platform.system().lower() == "windows"
                                else "/",
                                "script_extension": ".bat"
                                if platform.system().lower() == "windows"
                                else ".sh",
                            }
                        )
                    except Exception:
                        # Continue with basic context if platform detection fails
                        render_context.update(
                            {
                                "platform_system": "unknown",
                                "is_windows": False,
                                "is_macos": False,
                                "is_linux": False,
                                "path_separator": "/",
                                "script_extension": ".sh",
                            }
                        )

                    # Render the template
                    rendered_content = jinja_template.render(**render_context)

                    # Write rendered content to output file
                    output_path.write_text(rendered_content, encoding="utf-8")

                except Exception as e:
                    return False, f"Failed to render template: {str(e)}"
            else:
                # Regular file - copy as-is
                try:
                    content = template_path.read_text(encoding="utf-8")
                    output_path.write_text(content, encoding="utf-8")
                except UnicodeDecodeError:
                    # Handle binary files
                    content = template_path.read_bytes()
                    output_path.write_bytes(content)
                except Exception as e:
                    return False, f"Failed to copy file: {str(e)}"

            # Make executable if requested
            if make_executable:
                try:
                    current_permissions = output_path.stat().st_mode
                    output_path.chmod(current_permissions | stat.S_IEXEC)
                except Exception as e:
                    return False, f"Failed to make file executable: {str(e)}"

            return True, None

        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def output_result(
        self, result: Dict[str, Any], success: bool = True, json_mode: bool = False
    ) -> None:
        """
        Output script results in either JSON or human-readable format.

        Args:
            result: Dictionary containing result data or error information
            success: Whether the operation was successful
            json_mode: Whether to output in JSON format
        """
        if json_mode:
            print(json.dumps(result, indent=2))
        elif success:
            for key, value in result.items():
                if key != "error":
                    # Format key names for better readability
                    display_key = key.replace("_", " ").title()
                    # Show relative paths when possible
                    if isinstance(value, str) and "/" in value:
                        try:
                            rel_path = Path(value).relative_to(Path.cwd())
                            print(f"{display_key}: {rel_path}")
                        except ValueError:
                            print(f"{display_key}: {value}")
                    else:
                        print(f"{display_key}: {value}")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"Error: {error_msg}", file=sys.stderr)

    def handle_typer_exceptions(self, func: Callable) -> Callable:
        """
        Decorator to handle common exceptions in Typer commands and provide user-friendly error messages.

        Args:
            func: The Typer command function to wrap

        Returns:
            Decorated function that handles exceptions gracefully
        """

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                console.print("\nOperation cancelled by user.", style="red")
                raise typer.Exit(1) from None
            except Exception as e:
                error_msg = str(e)
                console.print(f"Error: {error_msg}", style="red")
                raise typer.Exit(1) from e

        if hasattr(func, "__name__"):
            wrapper.__name__ = func.__name__
        if hasattr(func, "__doc__"):
            wrapper.__doc__ = func.__doc__

        return wrapper

    def extract_spec_context(self, spec_dir: Path) -> Dict[str, Any]:
        """
        Extract comprehensive project context from spec directory files.

        Args:
            spec_dir: Path to the spec directory

        Returns:
            Dict containing extracted context information
        """
        context_info: Dict[str, Any] = {
            "feature_name": "",
            "feature_dir": str(spec_dir),
            "current_phase": "",
            "progress": {},
            "tech_stack": [],
            "current_tasks": [],
            "files": [],
            "file_sizes": {},
            "summary": "",
            "spec_tree": "",
        }

        # Scan available files
        spec_files = {
            "spec.md": spec_dir / "spec.md",
            "plan.md": spec_dir / "plan.md",
            "tasks.md": spec_dir / "tasks.md",
            "research.md": spec_dir / "research.md",
            "data-model.md": spec_dir / "data-model.md",
            "quickstart.md": spec_dir / "quickstart.md",
        }

        available_files = []
        for name, path in spec_files.items():
            if path.exists():
                available_files.append(name)
                context_info["file_sizes"][name] = (
                    f"{path.stat().st_size // 1024}KB"
                    if path.stat().st_size > 1024
                    else f"{path.stat().st_size}B"
                )

        context_info["files"] = available_files

        # Generate spec tree
        context_info["spec_tree"] = self._generate_spec_tree(spec_dir)

        # Determine current phase based on available files
        if "tasks.md" in available_files:
            context_info["current_phase"] = "Phase 3: Implementation"
        elif "plan.md" in available_files:
            context_info["current_phase"] = "Phase 2: Planning Complete"
        elif "spec.md" in available_files:
            context_info["current_phase"] = "Phase 1: Specification"
        else:
            context_info["current_phase"] = "Phase 0: Setup"

        # Extract from spec.md
        if spec_files["spec.md"].exists():
            spec_info = self._extract_from_spec(spec_files["spec.md"])
            if "feature_name" in spec_info:
                context_info["feature_name"] = spec_info["feature_name"]
            if "summary" in spec_info:
                context_info["summary"] = spec_info["summary"]
            if "progress" in spec_info:
                context_info["progress"].update(spec_info["progress"])

        # Extract from plan.md
        if spec_files["plan.md"].exists():
            plan_info = self._extract_from_plan(spec_files["plan.md"])
            if "tech_stack" in plan_info:
                context_info["tech_stack"].extend(plan_info["tech_stack"])
            if "progress" in plan_info:
                context_info["progress"].update(plan_info["progress"])

        # Extract from tasks.md
        if spec_files["tasks.md"].exists():
            tasks_info = self._extract_from_tasks(spec_files["tasks.md"])
            if "current_tasks" in tasks_info:
                context_info["current_tasks"] = tasks_info["current_tasks"]
            if "progress" in tasks_info:
                context_info["progress"].update(tasks_info["progress"])

        return context_info

    def _generate_spec_tree(self, spec_dir: Path) -> str:
        """Generate a tree structure of the spec directory."""
        try:
            result = subprocess.run(
                ["tree", str(spec_dir), "-a", "-I", ".git"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Clean up the tree output
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    return "\n".join(lines[1:])  # Skip the root directory name

            # Fallback to simple listing if tree is not available
            return self._simple_directory_listing(spec_dir)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return self._simple_directory_listing(spec_dir)

    def _simple_directory_listing(self, spec_dir: Path) -> str:
        """Simple fallback directory listing when tree command is not available."""
        items = []
        try:
            for item in sorted(spec_dir.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.is_file():
                    size = item.stat().st_size
                    size_str = f"{size // 1024}KB" if size > 1024 else f"{size}B"
                    items.append(f"├── {item.name} ({size_str})")
                elif item.is_dir():
                    items.append(f"├── {item.name}/")

            # Fix last item to use └── instead of ├──
            if items:
                items[-1] = items[-1].replace("├──", "└──")

            return "\n".join(items)
        except Exception:
            return "└── (unable to read directory)"

    def _extract_from_spec(self, spec_file: Path) -> Dict[str, Any]:
        """Extract information from spec.md file."""
        info: Dict[str, Any] = {"progress": {}}
        try:
            spec_content = spec_file.read_text()

            # Get feature name
            feature_match = re.search(r"# Feature Specification:\s*(.+)", spec_content)
            if feature_match:
                info["feature_name"] = feature_match.group(1).strip()

            # Get summary from user scenarios or first section
            summary_patterns = [
                r"## User Scenarios.*?\n(.*?)(?=##|\Z)",
                r"## Summary.*?\n(.*?)(?=##|\Z)",
                r"## Overview.*?\n(.*?)(?=##|\Z)",
            ]
            for pattern in summary_patterns:
                match = re.search(pattern, spec_content, re.DOTALL | re.MULTILINE)
                if match:
                    summary = match.group(1).strip()[:150]
                    summary = re.sub(r"\n+", " ", summary).strip()
                    if summary and not summary.startswith("["):
                        info["summary"] = summary + "..."
                        break

            # Extract progress from spec.md checkboxes
            completed = len(re.findall(r"- \[x\]", spec_content))
            checkbox_items = len(re.findall(r"- \[[x ]\]", spec_content))
            if checkbox_items > 0:
                info["progress"]["spec"] = f"{completed}/{checkbox_items} items"

        except Exception:
            pass
        return info

    def _extract_from_plan(self, plan_file: Path) -> Dict[str, Any]:
        """Extract information from plan.md file."""
        info: Dict[str, Any] = {"progress": {}, "tech_stack": []}
        try:
            plan_content = plan_file.read_text()

            # Extract tech stack more carefully
            tech_patterns = [
                r"Language/Version.*?:\s*(.+)",
                r"Primary Dependencies.*?:\s*(.+)",
                r"Storage.*?:\s*(.+)",
                r"Testing.*?:\s*(.+)",
                r"Target Platform.*?:\s*(.+)",
            ]

            for pattern in tech_patterns:
                matches = re.finditer(pattern, plan_content, re.IGNORECASE)
                for match in matches:
                    value = match.group(1).strip()
                    if (
                        value
                        and not value.startswith("[")
                        and "NEEDS CLARIFICATION" not in value
                    ):
                        items = [item.strip() for item in re.split(r"[,;]", value)]
                        valid_items = [item for item in items if item and len(item) > 2]
                        info["tech_stack"].extend(valid_items)

            # Keep only first 6 items
            info["tech_stack"] = info["tech_stack"][:6]

            # Progress from plan - look for checkboxes and checkmarks
            progress_section = re.search(
                r"## Progress Tracking.*?(?=##|\Z)", plan_content, re.DOTALL
            )
            if progress_section:
                progress_text = progress_section.group(0)
                # Count completed checkboxes: - [x]
                completed = len(re.findall(r"- \[x\]", progress_text))
                # Count all checkbox items: - [ ] or - [x] patterns
                checkbox_items = len(re.findall(r"- \[[x ]\]", progress_text))
                # Count bullet points if no checkboxes
                bullet_items = len(re.findall(r"[-\*]\s+(?![\[\(])", progress_text))

                total_items = checkbox_items if checkbox_items > 0 else bullet_items
                if total_items > 0:
                    info["progress"]["planning"] = f"{completed}/{total_items} items"

        except Exception:
            pass
        return info

    def _extract_from_tasks(self, tasks_file: Path) -> Dict[str, Any]:
        """Extract information from tasks.md file."""
        info: Dict[str, Any] = {"progress": {}, "current_tasks": []}
        try:
            tasks_content = tasks_file.read_text()

            # Parse task checkboxes: - [ ] or - [x]
            task_pattern = r"- \[([ x])\] (.+?)(?=\n|$)"
            task_matches = re.findall(task_pattern, tasks_content)

            if task_matches:
                completed_tasks = [
                    task for status, task in task_matches if status == "x"
                ]
                pending_tasks = [task for status, task in task_matches if status == " "]

                info["progress"]["tasks"] = (
                    f"{len(completed_tasks)}/{len(task_matches)} completed"
                )

                # Find first unchecked task and next 1-2 tasks
                if pending_tasks:
                    # Clean task descriptions (remove task IDs for readability)
                    clean_tasks = []
                    for task in pending_tasks[:3]:
                        # Remove T001, T002 prefixes and [P] markers
                        clean_task = re.sub(r"^T\d+\s*(\[P\])?\s*", "", task).strip()
                        clean_tasks.append(clean_task)
                    info["current_tasks"] = clean_tasks

        except Exception:
            pass
        return info

    def build_context_sections(
        self, context_info: Dict[str, Any], supports_imports: bool
    ) -> Tuple[List[str], str]:
        """
        Build enhanced context sections with file counts, spec tree, and helpful reminders.

        Args:
            context_info: Extracted context information
            supports_imports: Whether the assistant supports file imports

        Returns:
            Tuple of (sections_list, helpful_reminders)
        """
        sections = []

        if context_info.get("current_phase"):
            sections.append(f"**Phase**: {context_info['current_phase']}")

        if context_info.get("feature_name"):
            sections.append(f"**Feature**: {context_info['feature_name']}")

        if context_info.get("summary"):
            sections.append(f"**Goal**: {context_info['summary']}")

        # Enhanced progress tracking with separate spec, plan, tasks tracking
        if context_info.get("progress"):
            progress_dict = context_info["progress"]
            if "spec" in progress_dict:
                sections.append(f"**Spec Progress**: {progress_dict['spec']}")
            if "planning" in progress_dict:
                sections.append(f"**Plan Progress**: {progress_dict['planning']}")
            if "tasks" in progress_dict:
                sections.append(f"**Task Progress**: {progress_dict['tasks']}")

        # File counts section
        if context_info.get("files"):
            file_counts = []
            if "spec.md" in context_info["files"]:
                size = context_info.get("file_sizes", {}).get("spec.md", "")
                file_counts.append(f"spec.md ({size})" if size else "spec.md")
            if "plan.md" in context_info["files"]:
                size = context_info.get("file_sizes", {}).get("plan.md", "")
                file_counts.append(f"plan.md ({size})" if size else "plan.md")
            if "tasks.md" in context_info["files"]:
                size = context_info.get("file_sizes", {}).get("tasks.md", "")
                file_counts.append(f"tasks.md ({size})" if size else "tasks.md")

            sections.append(f"**Files**: {', '.join(file_counts)}")

        # Current tasks
        if context_info.get("current_tasks"):
            tasks = context_info["current_tasks"][:2]  # Next 2 tasks
            task_list = "; ".join(
                [task.split(" ", 1)[1] if " " in task else task for task in tasks]
            )
            sections.append(f"**Next Tasks**: {task_list}")

        # Tech stack
        if context_info.get("tech_stack"):
            tech_items = context_info["tech_stack"][:6]  # Keep concise
            sections.append(f"**Tech**: {', '.join(tech_items)}")

        # Spec tree structure
        if context_info.get("spec_tree"):
            sections.append(
                f"**Spec Structure**:\n```\n{context_info['spec_tree']}\n```"
            )

        # File references (imports for Claude/Cursor, paths for others)
        if context_info.get("files"):
            spec_dir = Path(context_info["feature_dir"])
            file_lines = []
            key_files = ["spec.md", "plan.md", "tasks.md", "data-model.md"]

            for file_name in key_files:
                if file_name in context_info["files"]:
                    file_path = spec_dir / file_name

                    if supports_imports:
                        # Use @import syntax for Claude/Cursor
                        try:
                            repo_root = self.get_repo_root()
                            rel_path = file_path.relative_to(repo_root)
                            file_lines.append(f"@{rel_path}")
                        except ValueError:
                            file_lines.append(f"@{file_path}")
                    else:
                        # Use plain paths for Copilot/Gemini
                        try:
                            repo_root = self.get_repo_root()
                            rel_path = file_path.relative_to(repo_root)
                            file_lines.append(str(rel_path))
                        except ValueError:
                            file_lines.append(str(file_path))

            if file_lines and len(file_lines) <= 4:  # Only if manageable
                label = "Spec Files" if supports_imports else "Spec Paths"
                sections.append(f"**{label}**: {', '.join(file_lines)}")

        # Generate helpful reminders
        reminders = self._generate_helpful_reminders(context_info)

        return sections, reminders

    def _generate_helpful_reminders(self, context_info: Dict[str, Any]) -> str:
        """Generate helpful reminders based on current project state."""
        reminders = []

        # Task completion reminders
        if context_info.get("current_tasks"):
            reminders.append(
                "**Remember**: Mark tasks as done by changing `- [ ]` to `- [x]` in tasks.md"
            )

        # Phase-specific reminders
        current_phase = context_info.get("current_phase", "")
        if "Implementation" in current_phase:
            reminders.append(
                "**TDD Reminder**: Write tests first, ensure they fail, then implement (Red-Green-Refactor)"
            )

        if context_info.get("progress", {}).get("tasks"):
            progress = context_info["progress"]["tasks"]
            if progress and not progress.startswith("0/"):
                reminders.append(
                    "**Progress Tip**: Update plan.md checkboxes as you complete implementation phases"
                )

        # File-specific reminders
        files = context_info.get("files", [])
        if "tasks.md" in files and "plan.md" in files:
            reminders.append(
                "**Workflow**: tasks.md contains specific todos, plan.md tracks overall phases"
            )

        return "\n".join(reminders) if reminders else ""


# Typer utility functions for script helpers
def echo_info(message: str, quiet: bool = False, json_mode: bool = False) -> None:
    """Echo informational message unless in quiet or JSON mode."""
    if not quiet and not json_mode:
        console.print(message)


def echo_debug(message: str, debug: bool = False) -> None:
    """Echo debug message if debug mode is enabled."""
    if debug:
        console.print(f"DEBUG: {message}", style="dim")


def echo_error(message: str, json_mode: bool = False, quiet: bool = False) -> None:
    """Echo error message to stderr."""
    if quiet or json_mode:
        return

    # Use stderr console to avoid corrupting JSON output
    stderr_console = Console(stderr=True)
    stderr_console.print(f"Error: {message}", style="red")


def echo_success(message: str, quiet: bool = False, json_mode: bool = False) -> None:
    """Echo success message unless in quiet or JSON mode."""
    if not quiet and not json_mode:
        console.print(f"✓ {message}", style="green")


# Convenience function for quick access
def get_script_helpers() -> ScriptHelpers:
    """Get a ScriptHelpers instance for use in scripts."""
    return ScriptHelpers()


def render_template_standalone(
    template_path: Path,
    context_dict: Dict[str, Any],
    output_path: Path,
    make_executable: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function for standalone template rendering without class instantiation.

    This function provides direct access to template rendering functionality
    for use in generated Python scripts and other standalone contexts.

    Args:
        template_path: Path to the template file (can be .j2 or regular file)
        context_dict: Dictionary with template variables for rendering
        output_path: Path where the rendered content should be written
        make_executable: Whether to make the output file executable (default: False)

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)

    Example:
        from specify_cli.utils.script_helpers import render_template_standalone

        context = {
            'project_name': 'my-project',
            'author_name': 'John Doe',
            'feature_name': 'auth-system'
        }
        success, error = render_template_standalone(
            template_path=Path('.specify/templates/spec-template.j2'),
            context_dict=context,
            output_path=Path('specs/003-auth-system/specification.md'),
            make_executable=False
        )
        if not success:
            print(f"Error: {error}")
    """
    helpers = ScriptHelpers()
    return helpers.render_template_standalone(
        template_path, context_dict, output_path, make_executable
    )

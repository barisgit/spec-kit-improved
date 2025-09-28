"""
Git Operations Helper - focused on git repository operations.

This helper handles:
- Repository root discovery
- Branch operations and validation
- Git status checks
- Branch existence validation
"""

import subprocess
from pathlib import Path
from typing import Optional

from specify_cli.services import CommandLineGitService


class GitOperationsHelper:
    """Helper for git repository operations."""

    def __init__(self):
        """Initialize with git service."""
        self._git_service = CommandLineGitService()

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
            # If git command fails, return current directory
            return Path.cwd()

    def get_current_branch(self) -> Optional[str]:
        """
        Get current git branch name.

        Returns:
            Optional[str]: Current branch name, or None if not in a git repository
                          or on a detached HEAD.
        """
        try:
            repo_root = self.get_repo_root()
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                cwd=repo_root,
            )
            branch_name = result.stdout.strip()

            # Check if we're in a detached HEAD state
            if branch_name == "HEAD":
                return None

            return branch_name

        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def check_branch_exists(self, branch_name: str) -> bool:
        """
        Check if a git branch exists.

        Args:
            branch_name: Name of the branch to check

        Returns:
            bool: True if branch exists, False otherwise
        """
        try:
            repo_root = self.get_repo_root()
            # Check if branch exists locally
            result = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
                capture_output=True,
                cwd=repo_root,
            )
            return result.returncode == 0

        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def check_git_repository(self) -> bool:
        """
        Check if current directory is in a git repository.

        Returns:
            bool: True if in a git repository, False otherwise
        """
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_feature_branch(self, branch_name: Optional[str] = None) -> bool:
        """
        Check if current or specified branch is a feature branch.

        Args:
            branch_name: Branch name to check. If None, uses current branch.

        Returns:
            bool: True if it's a feature branch
        """
        if branch_name is None:
            branch_name = self.get_current_branch()

        if not branch_name:
            return False

        # Common feature branch patterns
        feature_patterns = [
            r"^feature/",
            r"^feat/",
            r"^\d+-",  # Starts with number (like "001-feature-name")
            r"^[0-9]+\-feature\-",
        ]

        import re

        return any(re.match(pattern, branch_name) for pattern in feature_patterns)

    def is_no_branch_workflow(self) -> bool:
        """
        Check if we're using a no-branch workflow (main/master only).

        Returns:
            bool: True if using no-branch workflow
        """
        current_branch = self.get_current_branch()
        if not current_branch:
            return False

        # Check if we're on main/master and it's the only branch
        main_branches = ["main", "master"]
        return current_branch in main_branches

    def get_author_name(self) -> str:
        """
        Get git author name for current repository.

        Returns:
            str: Git author name, defaults to "Developer" if not configured
        """
        try:
            repo_root = self.get_repo_root()
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                check=True,
                cwd=repo_root,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "Developer"

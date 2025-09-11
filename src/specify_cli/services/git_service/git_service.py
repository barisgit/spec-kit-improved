"""
Git service for repository operations

Provides git repository management functionality including initialization,
branch management, staging, commits, and repository information.
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class GitService(ABC):
    """Abstract interface for git operations"""

    @abstractmethod
    def init_repository(self, project_path: Path) -> bool:
        """Initialize a git repository in the specified path"""
        pass

    @abstractmethod
    def create_branch(self, branch_name: str, project_path: Path) -> bool:
        """Create a new branch with the given name"""
        pass

    @abstractmethod
    def checkout_branch(self, branch_name: str, project_path: Path) -> bool:
        """Switch to the specified branch"""
        pass

    @abstractmethod
    def add_files(
        self, project_path: Path, file_patterns: Optional[List[str]] = None
    ) -> bool:
        """Add files to the staging area. If file_patterns is None, adds all files"""
        pass

    @abstractmethod
    def commit_changes(self, message: str, project_path: Path) -> bool:
        """Commit staged changes with the given message"""
        pass

    @abstractmethod
    def is_git_repository(self, project_path: Path) -> bool:
        """Check if the specified path is inside a git repository"""
        pass

    @abstractmethod
    def get_current_branch(self, project_path: Path) -> Optional[str]:
        """Get the name of the current branch"""
        pass

    @abstractmethod
    def get_remote_url(self, project_path: Path) -> Optional[str]:
        """Get the remote origin URL"""
        pass

    @abstractmethod
    def configure_platform_line_endings(self, project_path: Path) -> bool:
        """Configure git for platform-specific line endings"""
        pass


class CommandLineGitService(GitService):
    """Implementation using command-line git via subprocess"""

    def init_repository(self, project_path: Path) -> bool:
        """Initialize a git repository in the specified path"""
        try:
            # Initialize git repository
            subprocess.run(
                ["git", "init"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Check if there are any files to add using a more robust approach
            try:
                # First, try to check if there are any files in the directory
                import os

                files_in_dir = [
                    f
                    for f in os.listdir(project_path)
                    if f != ".git" and not f.startswith(".")
                ]

                if files_in_dir:
                    # Add all files
                    subprocess.run(
                        ["git", "add", "."],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                        text=True,
                    )

                    # Create initial commit
                    subprocess.run(
                        [
                            "git",
                            "commit",
                            "-m",
                            "Initial commit from SpecifyX template",
                        ],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                        text=True,
                    )

            except (subprocess.CalledProcessError, OSError):
                # If file operations fail, still return True if init succeeded
                # The repository was initialized successfully
                pass

            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_branch(self, branch_name: str, project_path: Path) -> bool:
        """Create a new branch with the given name"""
        # Check if we're already on the target branch
        current_branch = self.get_current_branch(project_path)
        if current_branch == branch_name:
            return True

        try:
            # Check if the branch already exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", f"refs/heads/{branch_name}"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Branch exists, just checkout to it
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                # Branch doesn't exist, create it
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def checkout_branch(self, branch_name: str, project_path: Path) -> bool:
        """Switch to the specified branch"""
        try:
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def add_files(
        self, project_path: Path, file_patterns: Optional[List[str]] = None
    ) -> bool:
        """Add files to the staging area. If file_patterns is None, adds all files"""
        try:
            if file_patterns is None:
                # Add all files
                subprocess.run(
                    ["git", "add", "."],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                # Add specific files/patterns
                for pattern in file_patterns:
                    subprocess.run(
                        ["git", "add", pattern],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def commit_changes(self, message: str, project_path: Path) -> bool:
        """Commit staged changes with the given message"""
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_git_repository(self, project_path: Path) -> bool:
        """Check if the specified path is inside a git repository"""
        if not project_path.is_dir():
            return False

        try:
            # Use git command to check if inside a work tree
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_current_branch(self, project_path: Path) -> Optional[str]:
        """Get the name of the current branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            branch = result.stdout.strip()
            return branch if branch else None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def get_remote_url(self, project_path: Path) -> Optional[str]:
        """Get the remote origin URL"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def configure_platform_line_endings(self, project_path: Path) -> bool:
        """Configure git for platform-specific line endings.

        Args:
            project_path: Path to the git repository

        Returns:
            True if successful, False otherwise
        """
        try:
            import os

            # Configure git to handle line endings automatically based on platform
            if os.name == "nt":  # Windows
                # On Windows, convert LF to CRLF on checkout, CRLF to LF on commit
                subprocess.run(
                    ["git", "config", "core.autocrlf", "true"],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                )
            else:  # Unix-like systems (macOS, Linux)
                # On Unix, don't convert line endings
                subprocess.run(
                    ["git", "config", "core.autocrlf", "false"],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                )

            # Set core.safecrlf to warn about line ending issues
            subprocess.run(
                ["git", "config", "core.safecrlf", "warn"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )

            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

"""
Feature Discovery Helper - focused on feature directory discovery and numbering.

This helper handles:
- Feature directory discovery and validation
- Sequential feature numbering
- Spec file management
- Feature context extraction
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from .configuration_helper import ConfigurationHelper
from .git_operations_helper import GitOperationsHelper


class FeatureDiscoveryHelper:
    """Helper for feature discovery and management operations."""

    def __init__(self):
        """Initialize with supporting helpers."""
        self._config_helper = ConfigurationHelper()
        self._git_helper = GitOperationsHelper()

    def get_next_feature_number(self, specs_dir: Optional[Path] = None) -> str:
        """
        Get next sequential feature number.

        Args:
            specs_dir: Optional specs directory. Defaults to project specs.

        Returns:
            str: Next feature number (zero-padded)
        """
        if specs_dir is None:
            repo_root = self._git_helper.get_repo_root()
            specs_dir = repo_root / "specs"

        if not specs_dir.exists():
            return "001"  # Start with 001 if no specs directory

        # Get numbering configuration
        numbering_config = self._config_helper.get_feature_numbering_config()
        start_number = numbering_config.get("start_number", 1)
        pad_zeros = numbering_config.get("pad_zeros", 3)
        increment = numbering_config.get("increment", 1)

        # Find existing feature numbers
        existing_numbers = []
        pattern = re.compile(r"^(\d+)-")

        for item in specs_dir.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    existing_numbers.append(int(match.group(1)))

        # Calculate next number
        if existing_numbers:
            next_number = max(existing_numbers) + increment
        else:
            next_number = start_number

        return str(next_number).zfill(pad_zeros)

    def find_feature_directory(
        self, branch_name: Optional[str] = None, specs_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Find feature directory that matches branch name.

        Args:
            branch_name: Branch name to find directory for. Uses current if None.
            specs_dir: Optional specs directory. Defaults to project specs.

        Returns:
            Optional[Path]: Feature directory path or None if not found
        """
        if branch_name is None:
            branch_name = self._git_helper.get_current_branch()

        if not branch_name:
            return None

        if specs_dir is None:
            repo_root = self._git_helper.get_repo_root()
            specs_dir = repo_root / "specs"

        if not specs_dir.exists():
            return None

        # Try exact match first
        for item in specs_dir.iterdir():
            if item.is_dir() and self._directory_matches_branch(item.name, branch_name):
                return item

        return None

    def find_feature_directory_for_workflow(
        self, branch_name: Optional[str] = None
    ) -> Optional[Path]:
        """
        Find feature directory accounting for different workflows.

        Args:
            branch_name: Branch name to find directory for

        Returns:
            Optional[Path]: Feature directory path
        """
        if self._git_helper.is_no_branch_workflow():
            # In no-branch workflow, find the most recent feature
            return self._find_latest_feature_directory()

        return self.find_feature_directory(branch_name)

    def check_spec_id_exists(
        self, spec_id: str, specs_dir: Optional[Path] = None
    ) -> tuple[bool, Optional[Path]]:
        """
        Check if a spec ID already exists.

        Args:
            spec_id: Spec ID to check
            specs_dir: Optional specs directory

        Returns:
            tuple[bool, Optional[Path]]: (exists, directory_path)
        """
        if specs_dir is None:
            repo_root = self._git_helper.get_repo_root()
            specs_dir = repo_root / "specs"

        if not specs_dir.exists():
            return False, None

        # Look for directories that start with the spec ID
        for item in specs_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"{spec_id}-"):
                return True, item

        return False, None

    def list_available_specs(self) -> List[Dict[str, str]]:
        """
        List all available spec directories.

        Returns:
            List[Dict[str, str]]: List of spec info dictionaries
        """
        repo_root = self._git_helper.get_repo_root()
        specs_dir = repo_root / "specs"

        if not specs_dir.exists():
            return []

        specs = []
        for item in specs_dir.iterdir():
            if item.is_dir():
                # Extract spec number and description
                match = re.match(r"^(\d+)-(.+)$", item.name)
                if match:
                    spec_num, description = match.groups()
                    specs.append(
                        {
                            "id": spec_num,
                            "description": description.replace("-", " ").title(),
                            "directory": item.name,
                            "path": str(item),
                        }
                    )

        # Sort by spec number
        specs.sort(key=lambda x: int(x["id"]))
        return specs

    def find_spec_by_id(self, spec_id: str) -> Optional[Path]:
        """
        Find spec directory by ID.

        Args:
            spec_id: Spec ID to find

        Returns:
            Optional[Path]: Spec directory path or None if not found
        """
        repo_root = self._git_helper.get_repo_root()
        specs_dir = repo_root / "specs"

        if not specs_dir.exists():
            return None

        # Look for directory starting with spec ID
        for item in specs_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"{spec_id}-"):
                return item

        return None

    def extract_spec_context(self, spec_dir: Path) -> Dict[str, Any]:
        """
        Extract context information from spec directory.

        Args:
            spec_dir: Spec directory to analyze

        Returns:
            Dict[str, Any]: Extracted context information
        """
        context: Dict[str, Any] = {
            "spec_directory": str(spec_dir),
            "spec_name": spec_dir.name,
            "has_spec": False,
            "has_plan": False,
            "has_tasks": False,
            "files": [],
            "spec_tree": "",
        }

        if not spec_dir.exists():
            return context

        # Generate directory tree
        context["spec_tree"] = self._generate_spec_tree(spec_dir)

        # Check for standard files
        spec_file = spec_dir / "spec.md"
        plan_file = spec_dir / "plan.md"
        tasks_file = spec_dir / "tasks.md"

        context["has_spec"] = spec_file.exists()
        context["has_plan"] = plan_file.exists()
        context["has_tasks"] = tasks_file.exists()

        # Extract content from standard files
        if context["has_spec"]:
            context.update(self._extract_from_spec(spec_file))

        if context["has_plan"]:
            context.update(self._extract_from_plan(plan_file))

        if context["has_tasks"]:
            context.update(self._extract_from_tasks(tasks_file))

        # List all files
        try:
            files_list = cast(List[str], context["files"])
            for item in spec_dir.rglob("*"):
                if item.is_file():
                    files_list.append(str(item.relative_to(spec_dir)))
        except Exception:
            pass

        return context

    def _directory_matches_branch(self, dir_name: str, branch_name: str) -> bool:
        """
        Check if directory name matches branch name.

        Args:
            dir_name: Directory name to check
            branch_name: Branch name to match against

        Returns:
            bool: True if they match
        """
        # Direct match
        if dir_name == branch_name:
            return True

        # Try extracting directory suffix and compare with branch suffix
        dir_suffix = self._extract_directory_suffix(dir_name)
        branch_suffix = self._extract_branch_suffix(branch_name)

        return dir_suffix == branch_suffix

    def _extract_directory_suffix(self, dir_name: str) -> str:
        """Extract meaningful suffix from directory name."""
        # Handle numbered directories like "001-feature-name"
        match = re.match(r"^(\d+)-(.+)$", dir_name)
        if match:
            return match.group(2)
        return dir_name

    def _extract_branch_suffix(self, branch_name: str) -> str:
        """Extract meaningful suffix from branch name."""
        # Remove common prefixes
        prefixes = ["feature/", "feat/", "bugfix/", "fix/", "hotfix/"]
        for prefix in prefixes:
            if branch_name.startswith(prefix):
                return branch_name[len(prefix) :]

        # Handle numbered patterns
        match = re.match(r"^(\d+)[-_](feature|feat|bugfix|fix)[-_](.+)$", branch_name)
        if match:
            return match.group(3)

        return branch_name

    def _find_latest_feature_directory(self) -> Optional[Path]:
        """Find the most recently created feature directory."""
        repo_root = self._git_helper.get_repo_root()
        specs_dir = repo_root / "specs"

        if not specs_dir.exists():
            return None

        # Find directory with highest number
        highest_num = 0
        latest_dir = None

        pattern = re.compile(r"^(\d+)-")
        for item in specs_dir.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    num = int(match.group(1))
                    if num > highest_num:
                        highest_num = num
                        latest_dir = item

        return latest_dir

    def _generate_spec_tree(self, spec_dir: Path) -> str:
        """Generate a tree view of spec directory."""
        try:
            lines = []
            lines.append(f"├── {spec_dir.name}/")

            items = sorted(spec_dir.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                prefix = "└── " if is_last else "├── "

                if item.is_dir():
                    lines.append(f"│   {prefix}{item.name}/")
                    # Add subdirectory contents (limited depth)
                    sub_items = list(item.iterdir())[:5]  # Limit to avoid huge trees
                    for j, sub_item in enumerate(sub_items):
                        is_sub_last = j == len(sub_items) - 1
                        sub_prefix = "    └── " if is_sub_last else "    ├── "
                        lines.append(f"│   {sub_prefix}{sub_item.name}")
                else:
                    size = item.stat().st_size if item.exists() else 0
                    size_str = f" ({size}B)" if size < 1024 else f" ({size // 1024}KB)"
                    lines.append(f"│   {prefix}{item.name}{size_str}")

            return "\n".join(lines)

        except Exception:
            return self._simple_directory_listing(spec_dir)

    def _simple_directory_listing(self, spec_dir: Path) -> str:
        """Simple directory listing fallback."""
        try:
            items = list(spec_dir.iterdir())
            file_list = [item.name for item in items]
            return ", ".join(sorted(file_list))
        except Exception:
            return "Unable to read directory"

    def _extract_from_spec(self, spec_file: Path) -> Dict[str, Any]:
        """Extract information from spec.md file."""
        try:
            content = spec_file.read_text(encoding="utf-8")
            return {
                "spec_content_preview": content[:500] + "..."
                if len(content) > 500
                else content,
                "spec_size": f"{len(content.encode('utf-8'))}B",
            }
        except Exception:
            return {}

    def _extract_from_plan(self, plan_file: Path) -> Dict[str, Any]:
        """Extract information from plan.md file."""
        try:
            content = plan_file.read_text(encoding="utf-8")

            # Count checkboxes for progress tracking
            total_checkboxes = len(re.findall(r"- \[[ x]\]", content))
            completed_checkboxes = len(re.findall(r"- \[x\]", content))

            return {
                "plan_progress": f"{completed_checkboxes}/{total_checkboxes} items",
                "plan_size": f"{len(content.encode('utf-8'))}B",
            }
        except Exception:
            return {}

    def _extract_from_tasks(self, tasks_file: Path) -> Dict[str, Any]:
        """Extract information from tasks.md file."""
        try:
            content = tasks_file.read_text(encoding="utf-8")

            # Count tasks
            total_tasks = len(re.findall(r"- \[[ x]\]", content))
            completed_tasks = len(re.findall(r"- \[x\]", content))

            return {
                "task_progress": f"{completed_tasks}/{total_tasks} completed",
                "tasks_size": f"{len(content.encode('utf-8'))}B",
            }
        except Exception:
            return {}

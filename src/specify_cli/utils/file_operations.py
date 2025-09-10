"""File operations utilities for spec-kit CLI."""

import shutil
import stat
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from rich.console import Console


class FileOperations:
    """Utility class for common file and directory operations."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize file operations utility.

        Args:
            console: Rich console instance for output
        """
        self._console = console or Console()

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary.

        Args:
            path: Directory path to ensure exists

        Returns:
            Path object for the directory
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def copy_tree(
        src: Union[str, Path],
        dst: Union[str, Path],
        ignore_patterns: Optional[List[str]] = None,
    ) -> None:
        """Copy directory tree with optional ignore patterns.

        Args:
            src: Source directory path
            dst: Destination directory path
            ignore_patterns: List of glob patterns to ignore
        """
        src_path = Path(src)
        dst_path = Path(dst)

        if ignore_patterns:

            def ignore_func(_: str, names: List[str]) -> List[str]:
                ignored = []
                for pattern in ignore_patterns or []:
                    for name in names:
                        if Path(name).match(pattern):
                            ignored.append(name)
                return ignored

            shutil.copytree(src_path, dst_path, ignore=ignore_func, dirs_exist_ok=True)
        else:
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

    @staticmethod
    def safe_write_file(
        path: Union[str, Path],
        content: str,
        backup: bool = True,
        encoding: str = "utf-8",
    ) -> bool:
        """Safely write content to file with optional backup.

        Args:
            path: File path to write to
            content: Content to write
            backup: Whether to create backup if file exists
            encoding: File encoding

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(path)

        tmp_path = None
        try:
            # Create backup if requested and file exists
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + ".backup")
                shutil.copy2(file_path, backup_path)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content atomically using temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", encoding=encoding, dir=file_path.parent, delete=False
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = Path(tmp_file.name)

            # Atomic move
            tmp_path.replace(file_path)
            return True

        except Exception:
            # Clean up temporary file if it exists
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            return False

    @staticmethod
    def write_file_with_permissions(
        path: Union[str, Path],
        content: str,
        executable: bool = False,
        encoding: str = "utf-8",
    ) -> bool:
        """Write file with specific permissions.

        Args:
            path: File path to write to
            content: Content to write
            executable: Whether to make file executable
            encoding: File encoding

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(path)

        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            file_path.write_text(content, encoding=encoding)

            # Set permissions
            if executable:
                # Make file executable for owner, group, and others
                current_mode = file_path.stat().st_mode
                file_path.chmod(
                    current_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
                )

            return True

        except Exception:
            return False

    @staticmethod
    def ensure_cross_platform_path(path: Union[str, Path]) -> Path:
        """Ensure path is cross-platform compatible.

        Args:
            path: Path to normalize

        Returns:
            Normalized Path object
        """
        # Convert to Path if string and resolve any relative components
        path_obj = Path(path)

        # Use forward slashes on all platforms (pathlib handles conversion)
        return path_obj.resolve() if path_obj.is_absolute() else path_obj

    @staticmethod
    def create_directory_structure(directories: List[Union[str, Path]]) -> List[Path]:
        """Create multiple directories ensuring cross-platform compatibility.

        Args:
            directories: List of directory paths to create

        Returns:
            List of created Path objects
        """
        created_paths = []

        for dir_path in directories:
            path = FileOperations.ensure_cross_platform_path(dir_path)
            try:
                path.mkdir(parents=True, exist_ok=True)
                created_paths.append(path)
            except Exception:
                # Continue creating other directories even if one fails
                pass

        return created_paths

    @staticmethod
    def find_files(
        directory: Union[str, Path], pattern: str = "*", recursive: bool = True
    ) -> List[Path]:
        """Find files matching pattern in directory.

        Args:
            directory: Directory to search in
            pattern: Glob pattern to match
            recursive: Whether to search recursively

        Returns:
            List of matching file paths
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        if recursive:
            return list(dir_path.rglob(pattern))
        else:
            return list(dir_path.glob(pattern))

    @staticmethod
    def get_file_info(
        path: Union[str, Path],
    ) -> Dict[str, Union[str, int, bool, float]]:
        """Get information about a file or directory.

        Args:
            path: Path to examine

        Returns:
            Dictionary with file information
        """
        file_path = Path(path)

        if not file_path.exists():
            return {"exists": False}

        stat = file_path.stat()
        return {
            "exists": True,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "size": stat.st_size,
            "modified_time": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
            "absolute_path": str(file_path.absolute()),
        }

    def clean_directory(
        self,
        path: Union[str, Path],
        keep_patterns: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> List[Path]:
        """Clean directory by removing files/dirs not matching keep patterns.

        Args:
            path: Directory path to clean
            keep_patterns: List of glob patterns for files to keep
            dry_run: If True, only show what would be removed

        Returns:
            List of removed (or would-be-removed) paths
        """
        dir_path = Path(path)
        if not dir_path.exists():
            return []

        keep_patterns = keep_patterns or []
        removed = []

        for item in dir_path.iterdir():
            should_keep = False

            # Check if item matches any keep pattern
            for pattern in keep_patterns:
                if item.match(pattern):
                    should_keep = True
                    break

            if not should_keep:
                removed.append(item)
                if not dry_run:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    self._console.print(f"[dim]Removed: {item}[/dim]")

        return removed

    @staticmethod
    def create_template_structure(
        base_path: Union[str, Path], structure: Dict[str, Union[str, Dict]]
    ) -> None:
        """Create directory structure from template definition.

        Args:
            base_path: Base directory for the structure
            structure: Nested dict defining structure
                      - String values create files with that content
                      - Dict values create subdirectories
        """
        base = Path(base_path)
        base.mkdir(parents=True, exist_ok=True)

        def _create_recursive(current_path: Path, struct: Dict[str, Union[str, Dict]]):
            for name, content in struct.items():
                item_path = current_path / name

                if isinstance(content, dict):
                    # Create subdirectory and recurse
                    item_path.mkdir(exist_ok=True)
                    _create_recursive(item_path, content)
                else:
                    # Create file with content
                    FileOperations.safe_write_file(item_path, content)

        _create_recursive(base, structure)

    @staticmethod
    def normalize_path_separators(path: Union[str, Path]) -> str:
        """Normalize path separators for the current platform.

        Args:
            path: Path to normalize

        Returns:
            Path string with platform-specific separators
        """
        import os

        path_str = str(Path(path))

        # Convert to platform-specific separators
        if os.name == "nt":  # Windows
            return path_str.replace("/", "\\")
        else:  # Unix-like systems
            return path_str.replace("\\", "/")

    @staticmethod
    def set_executable_permissions(path: Union[str, Path]) -> bool:
        """Set executable permissions on a file.

        Args:
            path: File path to make executable

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                return False

            # Make file executable for owner, group, and others
            current_mode = file_path.stat().st_mode
            file_path.chmod(current_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            return True
        except Exception:
            return False

    @staticmethod
    def get_platform_specific_line_endings() -> str:
        """Get platform-specific line ending string.

        Returns:
            Line ending string for current platform
        """
        import os

        return "\r\n" if os.name == "nt" else "\n"

    @staticmethod
    def create_file_with_inherited_permissions(
        path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> bool:
        """Create file with permissions inherited from parent directory.

        Args:
            path: File path to create
            content: Content to write
            encoding: File encoding

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(path)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            file_path.write_text(content, encoding=encoding)

            # Try to inherit permissions from parent directory
            # This may fail on some platforms, so we make it optional
            try:
                parent_mode = file_path.parent.stat().st_mode
                file_path.chmod(parent_mode)
            except (OSError, PermissionError):
                # Permission inheritance failed, but file was created successfully
                pass

            return True
        except Exception:
            return False


def ensure_directory(path: Union[str, Path]) -> Path:
    """Top-level helper to ensure a directory exists.

    Delegates to FileOperations.ensure_directory for backward compatibility.
    """
    return FileOperations.ensure_directory(path)

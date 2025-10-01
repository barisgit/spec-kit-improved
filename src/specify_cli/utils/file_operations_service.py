"""
File Operations Service - centralized file and path operations.

This service handles:
- File existence checks and validation
- File content reading and writing
- Directory creation and management
- File permission handling
- Path manipulation utilities
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from specify_cli.core.constants import CONSTANTS

logger = logging.getLogger(__name__)


class FileOperationsService:
    """Centralized service for file and path operations."""

    @staticmethod
    def ensure_file_exists(file_path: Union[str, Path]) -> bool:
        """Check if a file exists.

        Args:
            file_path: Path to check

        Returns:
            True if file exists
        """
        return Path(file_path).exists()

    @staticmethod
    def ensure_directory_exists(
        directory_path: Union[str, Path], create_if_missing: bool = False
    ) -> bool:
        """Check if a directory exists, optionally create it.

        Args:
            directory_path: Path to check
            create_if_missing: Whether to create directory if it doesn't exist

        Returns:
            True if directory exists or was created successfully
        """
        dir_path = Path(directory_path)

        if dir_path.exists():
            return dir_path.is_dir()

        if create_if_missing:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                return True
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                return False

        return False

    @staticmethod
    def read_file_content(
        file_path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[str]:
        """Read content from a file.

        Args:
            file_path: Path to file
            encoding: File encoding

        Returns:
            File content or None if failed
        """
        try:
            return Path(file_path).read_text(encoding=encoding)
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    @staticmethod
    def write_file_content(
        file_path: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> bool:
        """Write content to a file.

        Args:
            file_path: Path to file
            content: Content to write
            encoding: File encoding
            create_dirs: Whether to create parent directories

        Returns:
            True if successful
        """
        try:
            path = Path(file_path)

            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding=encoding)
            return True

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False

    @staticmethod
    def read_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Read and parse a JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data or None if failed
        """
        try:
            content = FileOperationsService.read_file_content(file_path)
            if content is None:
                return None
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read JSON file {file_path}: {e}")
            return None

    @staticmethod
    def write_json_file(
        file_path: Union[str, Path],
        data: Dict[str, Any],
        indent: int = 2,
        create_dirs: bool = True,
    ) -> bool:
        """Write data to a JSON file.

        Args:
            file_path: Path to JSON file
            data: Data to write
            indent: JSON indentation
            create_dirs: Whether to create parent directories

        Returns:
            True if successful
        """
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return FileOperationsService.write_file_content(
                file_path, content, create_dirs=create_dirs
            )
        except Exception as e:
            logger.error(f"Failed to write JSON file {file_path}: {e}")
            return False

    @staticmethod
    def make_executable(file_path: Union[str, Path]) -> bool:
        """Make a file executable.

        Args:
            file_path: Path to file

        Returns:
            True if successful
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False

            path.chmod(CONSTANTS.FILE.EXECUTABLE_PERMISSIONS)
            return True

        except Exception as e:
            logger.error(f"Failed to make file executable {file_path}: {e}")
            return False

    @staticmethod
    def should_be_executable(file_path: Union[str, Path]) -> bool:
        """Check if a file should be made executable based on patterns.

        Args:
            file_path: Path to check

        Returns:
            True if file should be executable
        """
        path = Path(file_path)

        # Check file extension
        if path.suffix in CONSTANTS.PATTERNS.EXECUTABLE_EXTENSIONS:
            return True

        # Check path patterns
        if any(
            path.match(pattern)
            for pattern in CONSTANTS.PATTERNS.EXECUTABLE_PATH_PATTERNS
        ):
            return True

        # Check filename patterns
        filename = path.name.lower()
        return any(
            pattern in filename
            for pattern in CONSTANTS.PATTERNS.EXECUTABLE_NAME_PATTERNS
        )

    @staticmethod
    def should_skip_file(file_path: Union[str, Path]) -> bool:
        """Check if a file should be skipped based on patterns.

        Args:
            file_path: Path to check

        Returns:
            True if file should be skipped
        """
        path = Path(file_path)
        return any(path.match(pattern) for pattern in CONSTANTS.PATTERNS.SKIP_PATTERNS)

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0

    @staticmethod
    def copy_file(source_path: Union[str, Path], dest_path: Union[str, Path]) -> bool:
        """Copy a file from source to destination.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if successful
        """
        try:
            import shutil

            shutil.copy2(source_path, dest_path)
            return True
        except Exception as e:
            logger.error(f"Failed to copy file from {source_path} to {dest_path}: {e}")
            return False

    @staticmethod
    def find_files_with_pattern(
        search_path: Union[str, Path], pattern: str, recursive: bool = True
    ) -> List[Path]:
        """Find files matching a pattern.

        Args:
            search_path: Directory to search
            pattern: File pattern (glob style)
            recursive: Whether to search recursively

        Returns:
            List of matching file paths
        """
        try:
            path = Path(search_path)
            if not path.exists():
                return []

            if recursive:
                return list(path.rglob(pattern))
            else:
                return list(path.glob(pattern))

        except Exception as e:
            logger.error(
                f"Failed to find files with pattern {pattern} in {search_path}: {e}"
            )
            return []

    @staticmethod
    def create_directory_structure(
        directories: List[Union[str, Path]],
        base_path: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Create multiple directories in a structure.

        Args:
            directories: List of directory paths to create
            base_path: Optional base path to prepend

        Returns:
            True if all directories were created successfully
        """
        success = True
        base = Path(base_path) if base_path else Path(".")

        for directory in directories:
            dir_path = base / directory if base_path else Path(directory)
            if not FileOperationsService.ensure_directory_exists(
                dir_path, create_if_missing=True
            ):
                success = False

        return success

    @staticmethod
    def get_file_extension(file_path: Union[str, Path]) -> str:
        """Get file extension.

        Args:
            file_path: Path to file

        Returns:
            File extension including the dot
        """
        return Path(file_path).suffix

    @staticmethod
    def remove_file_extension(file_path: Union[str, Path], extension: str) -> str:
        """Remove a specific extension from a file path.

        Args:
            file_path: Original file path
            extension: Extension to remove (including dot)

        Returns:
            File path without the extension
        """
        path_str = str(file_path)
        if path_str.endswith(extension):
            return path_str[: -len(extension)]
        return path_str

    @staticmethod
    def normalize_path(file_path: Union[str, Path]) -> Path:
        """Normalize a path for cross-platform compatibility.

        Args:
            file_path: Path to normalize

        Returns:
            Normalized Path object
        """
        return Path(file_path).resolve()

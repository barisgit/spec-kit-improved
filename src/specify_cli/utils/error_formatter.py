"""
Error formatting utilities for cross-platform compatibility

Provides platform-aware error message formatting with proper path separators.
"""

import platform
from pathlib import Path
from typing import Optional


def format_path_error(error_message: str, platform_name: Optional[str] = None) -> str:
    """Format error message with platform-specific path separators.

    Args:
        error_message: Base error message that may contain paths
        platform_name: Platform name (windows, macos, linux) or None for auto-detect

    Returns:
        Error message with platform-appropriate path separators
    """
    if platform_name is None:
        platform_name = platform.system().lower()

    # Determine the appropriate path separator
    separator = "\\" if platform_name == "windows" else "/"

    # For Windows, ensure paths use backslashes
    if platform_name == "windows":
        # Always convert forward slashes to backslashes on Windows
        # This handles both cases: paths with only forward slashes and mixed separators
        formatted_message = error_message.replace("/", separator)
    else:
        # For Unix-like systems, convert backslashes to forward slashes
        formatted_message = error_message.replace("\\", separator)

    return formatted_message


def format_file_not_found_error(
    file_path: Path, platform_name: Optional[str] = None
) -> str:
    """Format a file not found error with platform-specific paths.

    Args:
        file_path: Path to the file that was not found
        platform_name: Platform name or None for auto-detect

    Returns:
        Formatted error message
    """
    if platform_name is None:
        platform_name = platform.system().lower()

    # Convert path to platform-specific format
    if platform_name == "windows":
        formatted_path = str(file_path).replace("/", "\\")
    else:
        formatted_path = str(file_path)

    return f"File not found: {formatted_path}"


def format_permission_error(
    file_path: Path, operation: str, platform_name: Optional[str] = None
) -> str:
    """Format a permission error with platform-specific paths.

    Args:
        file_path: Path to the file with permission issues
        operation: Operation that failed (read, write, execute, etc.)
        platform_name: Platform name or None for auto-detect

    Returns:
        Formatted error message
    """
    if platform_name is None:
        platform_name = platform.system().lower()

    # Convert path to platform-specific format
    if platform_name == "windows":
        formatted_path = str(file_path).replace("/", "\\")
    else:
        formatted_path = str(file_path)

    return f"Permission denied: cannot {operation} '{formatted_path}'"


def format_directory_error(
    dir_path: Path, operation: str, platform_name: Optional[str] = None
) -> str:
    """Format a directory-related error with platform-specific paths.

    Args:
        dir_path: Path to the directory
        operation: Operation that failed (create, access, etc.)
        platform_name: Platform name or None for auto-detect

    Returns:
        Formatted error message
    """
    if platform_name is None:
        platform_name = platform.system().lower()

    # Convert path to platform-specific format
    if platform_name == "windows":
        formatted_path = str(dir_path).replace("/", "\\")
    else:
        formatted_path = str(dir_path)

    return f"Directory error: cannot {operation} '{formatted_path}'"

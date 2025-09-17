"""
Claude setup and environment validation.

This module handles validation of Claude's setup, including
CLI availability, authentication status, and configuration.
"""

import shutil
from pathlib import Path

from ..interfaces import ValidationResult
from ..types import AssistantConfig


class ClaudeValidator:
    """Handles Claude setup validation."""

    def __init__(self, config: AssistantConfig):
        """Initialize with Claude configuration."""
        self._config = config

    def validate_setup(self) -> ValidationResult:
        """Validate that Claude is properly set up."""
        result = ValidationResult(is_valid=True)

        # Check if claude command is available
        if not self._is_cli_available():
            result = result.add_warning(
                "Claude CLI not found in PATH - some features may not work"
            )

        # Check authentication status
        if not self._is_authenticated():
            result = result.add_warning(
                "Run 'claude auth' to authenticate with Anthropic for full functionality"
            )

        # Check configuration files
        result = self._validate_config_files(result)

        return result

    def _is_cli_available(self) -> bool:
        """Check if Claude CLI is available in PATH."""
        return shutil.which("claude") is not None

    def _is_authenticated(self) -> bool:
        """Check if Claude is authenticated (basic check)."""
        # In a real implementation, this would check for auth tokens
        # For now, just return True to avoid blocking functionality
        # TODO
        return True

    def _validate_config_files(self, result: ValidationResult) -> ValidationResult:
        """Validate Claude configuration files."""
        context_file = Path(self._config.context_file.file)

        # Note: Don't require files to exist during validation
        # They will be created during project initialization
        if context_file.exists() and not context_file.is_file():
            result = result.add_error(
                f"Context file path exists but is not a file: {context_file}"
            )

        commands_dir = Path(self._config.command_files.directory)
        if commands_dir.exists() and not commands_dir.is_dir():
            result = result.add_error(
                f"Commands directory path exists but is not a directory: {commands_dir}"
            )

        return result

    def is_properly_configured(self) -> bool:
        """Quick check if Claude is properly configured."""
        validation = self.validate_setup()
        return validation.is_valid and not validation.has_errors

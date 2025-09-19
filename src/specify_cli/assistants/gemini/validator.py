"""
Gemini setup validation.

This module provides validation capabilities for the Gemini assistant,
checking for proper CLI installation, Node.js requirements, and API configuration.
"""

import os
import shutil
import subprocess

from ..interfaces import ValidationResult
from ..types import AssistantConfig


class GeminiValidator:
    """Validates Gemini CLI setup and configuration."""

    def __init__(self, config: AssistantConfig):
        """Initialize with Gemini configuration."""
        self._config = config

    def validate_setup(self) -> ValidationResult:
        """Validate that Gemini is properly set up."""
        errors = []
        warnings = []

        # Check if Node.js is available
        if not shutil.which("node"):
            errors.append(
                "Node.js not found. Install Node.js 20+ from: https://nodejs.org/"
            )
        else:
            # Check Node.js version if available
            try:
                result = subprocess.run(
                    ["node", "--version"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    # Extract major version number
                    major_version = int(version.lstrip("v").split(".")[0])
                    if major_version < 20:
                        warnings.append(
                            f"Node.js version {version} detected. Gemini CLI requires Node.js 20+"
                        )
                else:
                    warnings.append("Could not verify Node.js version")
            except Exception:
                warnings.append("Could not verify Node.js version")

        # Check if gemini CLI is available
        if not shutil.which("gemini"):
            errors.append(
                "Gemini CLI not found. Install with: npm install -g @google/gemini-cli"
            )

        # Check for API key configuration
        if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            warnings.append(
                "Google API key not configured. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable"
            )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

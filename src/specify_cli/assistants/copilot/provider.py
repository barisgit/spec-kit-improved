"""
GitHub Copilot AI assistant provider implementation.

This module provides the CopilotProvider class that implements the
AssistantProvider interface for GitHub Copilot integration.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List

from ..injection_points import InjectionPoint
from ..interfaces import AssistantProvider, ValidationResult
from ..types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    InjectionValues,
    TemplateConfig,
)


class CopilotProvider(AssistantProvider):
    """GitHub Copilot AI assistant provider implementation."""

    def __init__(self):
        """Initialize the Copilot provider."""
        self._assistant_config = AssistantConfig(
            name="copilot",
            display_name="GitHub Copilot",
            description="GitHub's Copilot AI assistant",
            base_directory=".github",
            context_file=ContextFileConfig(
                file=".github/copilot-instructions.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".github/copilot/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".github/copilot/agents", file_format=FileFormat.MARKDOWN
            ),
        )

    @property
    def config(self) -> AssistantConfig:
        """Return the Copilot assistant configuration."""
        return self._assistant_config

    def get_injection_values(self) -> InjectionValues:
        """Return GitHub Copilot-specific injection point values."""
        return {
            InjectionPoint.COMMAND_PREFIX: "gh copilot ",
            InjectionPoint.SETUP_INSTRUCTIONS: (
                "Install GitHub CLI, run 'gh auth login' and "
                "'gh extension install github/gh-copilot'"
            ),
            InjectionPoint.CONTEXT_FILE_PATH: self._assistant_config.context_file.file,
            InjectionPoint.CONTEXT_FILE_DESCRIPTION: ", .github/copilot-instructions.md for GitHub Copilot",
            InjectionPoint.MEMORY_CONFIGURATION: (
                "# GitHub Copilot Memory Configuration\n"
                "# Store project context, coding patterns, and preferences\n"
                "# Copilot learns from your codebase and Git history\n"
                "\n"
                "## Project Context\n"
                "- Language and framework preferences\n"
                "- Code style and formatting rules\n"
                "- Architecture patterns and conventions\n"
                "\n"
                "## Coding Guidelines\n"
                "- Follow existing patterns in the codebase\n"
                "- Maintain consistency with team conventions\n"
                "- Consider performance and security implications"
            ),
            InjectionPoint.REVIEW_COMMAND: "gh copilot suggest",
            InjectionPoint.DOCUMENTATION_URL: "https://docs.github.com/en/copilot",
            InjectionPoint.WORKFLOW_INTEGRATION: (
                "# GitHub Copilot integrates naturally with GitHub workflows\n"
                "# - Automatic context from repository and commit history\n"
                "# - Integration with GitHub Actions and pull requests\n"
                "# - Code suggestions based on repository patterns"
            ),
            InjectionPoint.CUSTOM_COMMANDS: (
                "# Custom Copilot Commands\n"
                "# gh copilot suggest          # Get code suggestions\n"
                "# gh copilot explain          # Explain code functionality\n"
                "# gh copilot config           # Configure Copilot settings\n"
                "# gh copilot alias            # Create command aliases"
            ),
            InjectionPoint.CONTEXT_FRONTMATTER: 'description: "GitHub Copilot instructions for this project"',
            InjectionPoint.IMPORT_SYNTAX: "No special import syntax - use standard GitHub repository structure and file references",
            InjectionPoint.BEST_PRACTICES: "Write clear, specific instructions; use examples; leverage GitHub context; structure content hierarchically",
            InjectionPoint.TROUBLESHOOTING: "Check `gh copilot` extension status, verify GitHub CLI authentication, ensure proper repository context",
            InjectionPoint.LIMITATIONS: "Context limited to repository scope, requires GitHub Copilot subscription, works best with GitHub-hosted projects",
            InjectionPoint.FILE_EXTENSIONS: ".md, .js, .ts, .py, .java, .go, .rb (GitHub's supported languages)",
        }

    def validate_setup(self) -> ValidationResult:
        """Validate that GitHub Copilot is properly set up."""
        errors = []
        warnings = []

        # Check if gh CLI is available
        if not shutil.which("gh"):
            errors.append("GitHub CLI not found. Install from: https://cli.github.com/")
        else:
            # Check if user is authenticated
            try:
                result = subprocess.run(
                    ["gh", "auth", "status"], capture_output=True, text=True
                )
                if result.returncode != 0:
                    warnings.append("GitHub CLI not authenticated. Run 'gh auth login'")
            except Exception:
                warnings.append("Could not verify GitHub CLI authentication status")

            # Check if Copilot extension is installed
            try:
                result = subprocess.run(
                    ["gh", "extension", "list"], capture_output=True, text=True
                )
                if "github/gh-copilot" not in result.stdout:
                    errors.append(
                        "GitHub Copilot extension not installed. Run 'gh extension install github/gh-copilot'"
                    )
            except Exception:
                warnings.append("Could not verify Copilot extension status")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def get_setup_instructions(self) -> List[str]:
        """Return step-by-step setup instructions for GitHub Copilot."""
        return [
            "1. Install GitHub CLI from https://cli.github.com/",
            "2. Authenticate with GitHub: gh auth login",
            "3. Install Copilot extension: gh extension install github/gh-copilot",
            "4. Verify installation with 'gh copilot --version'",
            f"5. Configure context file at {self._assistant_config.context_file.file}",
            "6. Test Copilot with 'gh copilot suggest'",
        ]

    @property
    def imports_supported(self) -> bool:
        """GitHub Copilot supports file imports using HTML comment syntax."""
        return True

    def format_import(self, current_dir: Path, target_file: Path) -> str:
        """
        Format file import for GitHub Copilot using HTML comment syntax.

        Copilot uses relative paths in HTML comments for imports.
        """
        if not self.imports_supported:
            return ""

        try:
            # Calculate relative path from current directory to target file
            relative_path = target_file.relative_to(current_dir)
            return f"<!-- @import {relative_path} -->"
        except ValueError:
            # If relative path calculation fails, use filename only
            return f"<!-- @import {target_file.name} -->"

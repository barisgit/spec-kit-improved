"""
Cursor AI assistant provider implementation.

This module implements the AssistantProvider ABC for Cursor AI-powered code editor,
providing configuration, injection values, validation, and setup instructions.

The CursorProvider class encapsulates all Cursor-specific logic including:
- Configuration management using Pydantic models
- Template injection point values
- Setup validation and instructions
- Integration with Cursor editor and MDC rule files
"""

import platform
import shutil
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


class CursorProvider(AssistantProvider):
    """Cursor AI assistant provider implementation."""

    def __init__(self):
        """Initialize the Cursor provider."""
        self._assistant_config = AssistantConfig(
            name="cursor",
            display_name="Cursor",
            description="Cursor AI assistant with MDC rule files",
            base_directory=".cursor",
            context_file=ContextFileConfig(
                file=".cursor/rules/main.mdc", file_format=FileFormat.MDC
            ),
            command_files=TemplateConfig(
                directory=".cursor/rules", file_format=FileFormat.MDC
            ),
            agent_files=TemplateConfig(
                directory=".cursor/agents", file_format=FileFormat.MDC
            ),
        )

    @property
    def config(self) -> AssistantConfig:
        """Return the Cursor assistant configuration."""
        return self._assistant_config

    def get_injection_values(self) -> InjectionValues:
        """Return Cursor-specific injection point values."""
        return {
            InjectionPoint.COMMAND_PREFIX: "Ctrl+K (or Cmd+K), ",
            InjectionPoint.SETUP_INSTRUCTIONS: "Install Cursor editor and configure .cursor/rules/main.mdc with project-specific rules",
            InjectionPoint.CONTEXT_FILE_PATH: self._assistant_config.context_file.file,
            InjectionPoint.CONTEXT_FILE_DESCRIPTION: ", .cursor/rules/main.mdc for Cursor",
            InjectionPoint.MEMORY_CONFIGURATION: (
                "MDC rule file configuration for Cursor AI behavior and project context"
            ),
            InjectionPoint.REVIEW_COMMAND: "Use Cursor's AI chat or Ctrl+K for code review",
            InjectionPoint.DOCUMENTATION_URL: "https://docs.cursor.com",
            InjectionPoint.WORKFLOW_INTEGRATION: (
                "Configure .cursor/rules for AI-powered code completion and chat"
            ),
            InjectionPoint.CUSTOM_COMMANDS: (
                "Use Cursor's AI chat and code completion features for development assistance"
            ),
            InjectionPoint.CONTEXT_FRONTMATTER: 'alwaysApply: true\ndescription: "Main Cursor AI rules for this project"',
            InjectionPoint.IMPORT_SYNTAX: "Use `@file-path` syntax in .mdc files to reference other rule files",
            InjectionPoint.BEST_PRACTICES: "Create specific .cursor/rules files for different contexts, use clear rule descriptions, enable alwaysApply for main rules",
            InjectionPoint.TROUBLESHOOTING: "Check .cursor/rules syntax, ensure proper MDC formatting, restart Cursor editor if rules not loading",
            InjectionPoint.LIMITATIONS: "Cursor AI context window limits, requires well-formed .mdc files, works best with TypeScript/JavaScript projects",
            InjectionPoint.FILE_EXTENSIONS: ".mdc, .md, .ts, .js, .tsx, .jsx, .py (specializes in .mdc rule files)",
        }

    def validate_setup(self) -> ValidationResult:
        """Validate that Cursor is properly set up."""
        errors = []
        warnings = []

        # Check if Cursor is installed
        cursor_found = False

        # Check common installation paths
        system = platform.system()
        if system == "Darwin":  # macOS
            cursor_paths = [
                "/Applications/Cursor.app",
                Path.home() / "Applications" / "Cursor.app",
            ]
            cursor_found = any(Path(path).exists() for path in cursor_paths)
        elif system == "Windows":
            cursor_paths = [
                Path.home() / "AppData" / "Local" / "Programs" / "cursor",
                Path("C:") / "Program Files" / "Cursor",
            ]
            cursor_found = any(Path(path).exists() for path in cursor_paths)
        elif system == "Linux":
            # Check for cursor command or common installation paths
            cursor_found = shutil.which("cursor") is not None
            if not cursor_found:
                cursor_paths = [
                    Path.home() / ".local" / "bin" / "cursor",
                    Path("/usr/local/bin/cursor"),
                    Path("/opt/cursor"),
                    Path.home() / "Applications" / "cursor",
                ]
                cursor_found = any(Path(path).exists() for path in cursor_paths)

        if not cursor_found:
            errors.append("Cursor editor not found. Download from: https://cursor.sh/")

        # Check if .cursor directory exists in current project
        cursor_dir = Path.cwd() / ".cursor"
        if not cursor_dir.exists():
            warnings.append(
                "No .cursor directory found in current project. Create .cursor/rules/main.mdc for project-specific AI rules"
            )
        else:
            # Check for rules directory and main.mdc file
            rules_dir = cursor_dir / "rules"
            main_mdc = rules_dir / "main.mdc"

            if not rules_dir.exists():
                warnings.append(
                    "No .cursor/rules directory found. Create it to configure project-specific AI rules"
                )
            elif not main_mdc.exists():
                warnings.append(
                    "No .cursor/rules/main.mdc file found. Create it to configure project-specific AI rules"
                )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def get_setup_instructions(self) -> List[str]:
        """Return step-by-step setup instructions for Cursor."""
        return [
            "1. Download and install Cursor from https://cursor.sh/",
            "2. Open Cursor and complete the initial setup",
            "3. Create .cursor directory in your project root",
            "4. Create .cursor/rules/main.mdc file for project-specific AI rules",
            "5. Configure AI features in Cursor settings (Cmd/Ctrl + ,)",
            "6. Test AI chat feature with Cmd/Ctrl + L",
            "7. Test AI code completion while editing files",
        ]

    @property
    def imports_supported(self) -> bool:
        """Cursor supports file imports using @ syntax in .mdc files."""
        return True

    def format_import(self, current_dir: Path, target_file: Path) -> str:
        """
        Format file import for Cursor using @ syntax with relative paths.

        Cursor uses @ syntax similar to Claude but in .mdc files.
        """
        if not self.imports_supported:
            return ""

        try:
            # Calculate relative path from current directory to target file
            relative_path = target_file.relative_to(current_dir)
            return f"@{relative_path}"
        except ValueError:
            # If relative path calculation fails, use filename only
            return f"@{target_file.name}"

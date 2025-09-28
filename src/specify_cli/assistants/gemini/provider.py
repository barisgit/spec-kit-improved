"""
Gemini AI assistant provider implementation.

This module provides the main GeminiProvider class that orchestrates
all Gemini-specific components for configuration, injection management,
validation, and setup instructions.

The provider uses a modular architecture with separate components for:
- Configuration management (GeminiConfig)
- Template injection points (GeminiInjectionManager)
- Setup validation (GeminiValidator)
- Installation guidance (GeminiSetupManager)

Usage:
    provider = GeminiProvider()
    config = provider.config
    injections = provider.get_injection_values()
"""

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
from .validator import GeminiValidator


class GeminiProvider(AssistantProvider):
    """Gemini AI assistant provider implementation."""

    def __init__(self):
        """Initialize the Gemini provider with modular components."""
        self._assistant_config = AssistantConfig(
            name="gemini",
            display_name="Gemini CLI",
            description="Google's Gemini CLI AI assistant",
            base_directory=".gemini",
            context_file=ContextFileConfig(
                file=".gemini/GEMINI.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".gemini/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=None,
        )
        self._validator = GeminiValidator(self._assistant_config)

    @property
    def config(self) -> AssistantConfig:
        """Return the Gemini assistant configuration."""
        return self._assistant_config

    def get_injection_values(self) -> InjectionValues:
        """Return Gemini-specific injection point values."""
        return {
            InjectionPoint.COMMAND_PREFIX: "gemini ",
            InjectionPoint.SETUP_INSTRUCTIONS: "Install Node.js 20+, run 'npm install -g @google/gemini-cli', and configure API key",
            InjectionPoint.CONTEXT_FILE_PATH: self._assistant_config.context_file.file,
            InjectionPoint.CONTEXT_FILE_DESCRIPTION: ", GEMINI.md for Gemini CLI",
            InjectionPoint.MEMORY_CONFIGURATION: (
                "# Gemini CLI Memory Configuration\n"
                "# Project-specific context and conversation history\n"
                "# Configure context using .gemini/GEMINI.md files\n"
                "# Enable conversation persistence with 1M token context window\n"
                "# Use built-in tools: Google Search, file operations, shell commands"
            ),
            InjectionPoint.REVIEW_COMMAND: 'gemini -p "Review this code for security vulnerabilities and best practices"',
            InjectionPoint.DOCUMENTATION_URL: "https://developers.google.com/gemini-code-assist/docs/gemini-cli",
            InjectionPoint.WORKFLOW_INTEGRATION: (
                "# Gemini CLI workflow integration\n"
                "# Use '/tools' to list available built-in tools\n"
                "# Install extensions for additional capabilities:\n"
                "# - Security: gemini extensions install https://github.com/google-gemini/gemini-cli-security\n"
                "# - Deploy: gemini extensions install https://github.com/GoogleCloudPlatform/cloud-run-mcp\n"
                "# Use 'gemini -p \"prompt\"' for quick prompts without terminal UI"
            ),
            InjectionPoint.CUSTOM_COMMANDS: (
                "# Gemini CLI built-in tools and commands\n"
                "# /tools - List all available built-in tools\n"
                '# gemini -p "prompt" - Quick prompt without terminal interface\n'
                "# Built-in tools: Google Search grounding, file operations, shell commands, web fetching\n"
                "# Extensions (require separate install):\n"
                "#   /security:analyze - Security analysis (via extension)\n"
                "#   /deploy - Cloud Run deployment (via extension)"
            ),
            InjectionPoint.CONTEXT_FRONTMATTER: 'description: "Gemini AI configuration for this project"',
            InjectionPoint.IMPORT_SYNTAX: "No file import syntax - provide full context in each interaction",
            InjectionPoint.BEST_PRACTICES: "Use specific prompts, leverage Google Search grounding, utilize built-in tools, provide clear context",
            InjectionPoint.TROUBLESHOOTING: "Check `gemini --version`, verify API key configuration, ensure Node.js 20+ compatibility",
            InjectionPoint.LIMITATIONS: "Requires API key, limited conversation history, no persistent file context across sessions",
            InjectionPoint.FILE_EXTENSIONS: ".md, .js, .ts, .py, .json, .yaml (supports most common formats)",
        }

    def validate_setup(self) -> ValidationResult:
        """Validate that Gemini is properly set up."""
        return self._validator.validate_setup()

    def get_setup_instructions(self) -> List[str]:
        """Return step-by-step setup instructions for Gemini."""
        return [
            "1. Install Node.js 20+ from https://nodejs.org/",
            "2. Install Gemini CLI: npm install -g @google/gemini-cli",
            "3. Get your API key from https://makersuite.google.com/app/apikey",
            "4. Set environment variable: export GOOGLE_API_KEY=your_api_key_here",
            "5. Verify installation with 'gemini --version'",
            "6. Test the setup with 'gemini -p \"Hello, Gemini!\"'",
        ]

    @property
    def imports_supported(self) -> bool:
        """Gemini currently does not support file imports."""
        return False

    def format_import(self, current_dir: Path, target_file: Path) -> str:
        """
        Gemini does not support file imports, returns empty string.

        Future versions might support imports, in which case this method
        would implement Gemini-specific import syntax.

        Args:
            current_dir: Current working directory (unused for Gemini)
            target_file: Target file to import (unused for Gemini)
        """
        # Parameters are unused since Gemini doesn't support file imports
        _ = current_dir
        _ = target_file
        return ""

"""
Claude AI assistant provider implementation.

This module provides the main ClaudeProvider class with focused,
practical components that avoid unnecessary abstractions.

The provider uses a modular architecture with separate components for:
- Template injection points (ClaudeInjectionManager)
- Setup validation (ClaudeValidator)

Usage:
    provider = ClaudeProvider()
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
from .validator import ClaudeValidator


class ClaudeProvider(AssistantProvider):
    """Claude AI assistant provider implementation."""

    def __init__(self):
        """Initialize the Claude provider with modular components."""
        self._assistant_config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Anthropic's Claude Code AI assistant",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file="CLAUDE.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands",
                file_format=FileFormat.MARKDOWN,  # Slash commands to bash scripts
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )
        self._validator = ClaudeValidator(self._assistant_config)

    @property
    def config(self) -> AssistantConfig:
        """Return the Claude assistant configuration."""
        return self._assistant_config

    def get_injection_values(self) -> InjectionValues:
        """Return Claude-specific injection point values."""
        return {
            InjectionPoint.COMMAND_PREFIX: "claude ",
            InjectionPoint.SETUP_INSTRUCTIONS: "Install Claude Code with 'npm install -g @anthropic-ai/claude-code', then run 'claude' (prompts for login on first use)",
            InjectionPoint.CONTEXT_FILE_PATH: self._assistant_config.context_file.file,
            InjectionPoint.CONTEXT_FILE_DESCRIPTION: ", CLAUDE.md for Claude Code",
            InjectionPoint.MEMORY_CONFIGURATION: "Spec-driven development workflow with Claude Code integration",
            InjectionPoint.REVIEW_COMMAND: "/review (within Claude Code REPL)",
            InjectionPoint.DOCUMENTATION_URL: "https://docs.anthropic.com/en/docs/claude-code",
            InjectionPoint.WORKFLOW_INTEGRATION: "GitHub Actions integration with Claude Code for automated code review and generation",
            InjectionPoint.CUSTOM_COMMANDS: 'claude (interactive REPL), claude "query" (start with prompt), claude -p "query" (SDK query), claude -c (continue conversation), claude update, claude mcp',
            InjectionPoint.CONTEXT_FRONTMATTER: 'description: "Claude Code context file for this project"',
            # High-priority injection points
            InjectionPoint.IMPORT_SYNTAX: "Use `@path/to/file.ext` syntax to import files with relative paths",
            InjectionPoint.BEST_PRACTICES: "Use descriptive prompts, break complex tasks into steps, leverage Claude's code analysis capabilities",
            InjectionPoint.TROUBLESHOOTING: "Check Claude Code status with `claude --version`, restart authentication by running `claude` again, verify file permissions",
            InjectionPoint.LIMITATIONS: "Claude Code works best with well-structured projects, requires clear context, may need multiple iterations for complex tasks",
            InjectionPoint.FILE_EXTENSIONS: ".md, .py, .js, .ts, .json, .yaml, .toml (prefers markdown for documentation)",
        }

    def validate_setup(self) -> ValidationResult:
        """Validate that Claude is properly set up."""
        return self._validator.validate_setup()

    def get_setup_instructions(self) -> List[str]:
        """Return step-by-step setup instructions for Claude."""
        config = self._assistant_config
        instructions = [
            "Install Claude Code CLI from Anthropic",
            "Run 'claude' to start authentication (prompts on first use)",
            "Verify installation with 'claude --version'",
            "Test functionality with 'claude' to start interactive session",
            f"Configure context file at {config.context_file.file} ({config.context_file.file_format.value} format)",
            f"Set up commands directory at {config.command_files.directory} ({config.command_files.file_format.value} format)",
        ]

        if config.agent_files:
            instructions.append(
                f"Create agent files in {config.agent_files.directory} ({config.agent_files.file_format.value} format)"
            )

        return instructions

    @property
    def imports_supported(self) -> bool:
        """Claude supports file imports with @ syntax."""
        return True

    def format_import(self, current_dir: Path, target_file: Path) -> str:
        """
        Format file import for Claude using @ syntax with relative paths.

        Claude prefers relative paths for imports to keep context files portable.
        """
        if not self.imports_supported:
            return ""

        try:
            # Calculate relative path from current directory to target file
            relative_path = target_file.relative_to(current_dir)
            return f"@{relative_path}"
        except ValueError:
            # If relative path calculation fails, fall back to absolute path
            return f"@{target_file}"

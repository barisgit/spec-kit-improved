"""AI Assistant developer defaults for SpecifyX

This module provides centralized, immutable AI assistant configurations that are
packaged with SpecifyX. These are developer defaults, not user configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Final, List, Optional


@dataclass(frozen=True)
class AIAssistant:
    """Single AI assistant configuration"""

    name: str
    base_directory: str  # Base directory for the AI assistant
    display_name: str
    context_file: str  # The main context/instruction file
    commands_directory: str  # Where commands go
    memory_directory: str  # Where memory/constitution files go
    description: str = ""

    def __post_init__(self):
        """Validate AI assistant configuration"""
        if not self.name or not self.base_directory:
            raise ValueError("Name and base_directory must be non-empty")
        if not self.base_directory.startswith("."):
            object.__setattr__(self, "base_directory", f".{self.base_directory}")


@dataclass(frozen=True)
class AIAssistantDefaults:
    """Developer defaults for AI assistant configurations - packaged with SpecifyX"""

    # Supported AI assistants
    ASSISTANTS: Final[List[AIAssistant]] = field(
        default_factory=lambda: [
            AIAssistant(
                name="claude",
                base_directory=".claude",
                display_name="Claude Code",
                context_file=".claude/CLAUDE.md",
                commands_directory=".claude/commands",
                memory_directory=".claude/memory",
                description="Anthropic's Claude Code AI assistant",
            ),
            AIAssistant(
                name="gemini",
                base_directory=".gemini",
                display_name="Gemini CLI",
                context_file=".gemini/GEMINI.md",
                commands_directory=".gemini/commands",
                memory_directory=".gemini/memory",
                description="Google's Gemini CLI AI assistant",
            ),
            AIAssistant(
                name="copilot",
                base_directory=".github",
                display_name="GitHub Copilot",
                context_file=".github/copilot-instructions.md",
                commands_directory=".github/copilot/commands",
                memory_directory=".github/copilot/memory",
                description="GitHub's Copilot AI assistant",
            ),
            AIAssistant(
                name="cursor",
                base_directory=".cursor",
                display_name="Cursor",
                context_file=".cursor/rules/main.mdc",  # Main MDC rule file
                commands_directory=".cursor/rules",  # Rules directory for commands
                memory_directory=".cursor/rules",  # Rules directory for memory/constitution
                description="Cursor AI assistant with MDC rule files",
            ),
        ]
    )

    # Default AI assistant when none specified
    DEFAULT_ASSISTANT: Final[str] = "claude"

    # Fallback directory pattern for unknown assistants
    FALLBACK_DIRECTORY_PATTERN: Final[str] = ".{assistant_name}"

    def get_assistant_by_name(self, name: str) -> Optional[AIAssistant]:
        """Get AI assistant configuration by name"""
        for assistant in self.ASSISTANTS:
            if assistant.name.lower() == name.lower():
                return assistant
        return None

    def get_directory_for_assistant(self, name: str) -> str:
        """Get base directory path for given AI assistant"""
        assistant = self.get_assistant_by_name(name)
        if assistant:
            return assistant.base_directory
        # Fallback for unknown assistants
        return self.FALLBACK_DIRECTORY_PATTERN.format(assistant_name=name.lower())

    def get_all_assistant_names(self) -> List[str]:
        """Get list of all supported AI assistant names"""
        return [assistant.name for assistant in self.ASSISTANTS]

    def get_assistant_choices(self) -> List[str]:
        """Get list of assistant names for CLI choices"""
        return [assistant.name for assistant in self.ASSISTANTS]

    def get_display_names(self) -> Dict[str, str]:
        """Get mapping of assistant name to display name"""
        return {assistant.name: assistant.display_name for assistant in self.ASSISTANTS}

    def is_supported_assistant(self, name: str) -> bool:
        """Check if AI assistant is officially supported"""
        return self.get_assistant_by_name(name) is not None

    def get_directory_mapping(self) -> Dict[str, str]:
        """Get mapping of assistant name to base directory"""
        return {
            assistant.name: assistant.base_directory for assistant in self.ASSISTANTS
        }

    def validate_assistant_name(self, name: str) -> str:
        """Validate and normalize assistant name"""
        if not name:
            return self.DEFAULT_ASSISTANT

        # Check if supported
        if self.is_supported_assistant(name):
            return name.lower()

        # Allow unknown assistants with warning
        return name.lower()

    def get_config_files_for_assistant(self, name: str) -> List[str]:
        """Get typical config files for an AI assistant"""
        assistant = self.get_assistant_by_name(name)
        if not assistant:
            return []

        files = []

        # Add main context file
        if assistant.context_file:
            files.append(assistant.context_file)

        # Add directories
        if assistant.commands_directory:
            files.append(assistant.commands_directory)
        if (
            assistant.memory_directory
            and assistant.memory_directory != assistant.commands_directory
        ):
            files.append(assistant.memory_directory)

        return files

    def get_target_path_for_category(self, assistant_name: str, category: str) -> str:
        """Get target path for given assistant and category"""
        assistant = self.get_assistant_by_name(assistant_name)

        if not assistant:
            # Fallback for unknown assistants - use category defaults
            from .category_defaults import CATEGORY_DEFAULTS

            try:
                return CATEGORY_DEFAULTS.resolve_target_for_category(
                    category, assistant_name
                )
            except ValueError:
                # Unknown category, use generic pattern
                return f".{assistant_name}/{category}"

        # Use assistant-specific directories for AI-specific categories
        from .category_defaults import CATEGORY_DEFAULTS

        try:
            category_config = CATEGORY_DEFAULTS.get_category_by_name(category)
            if category_config.is_ai_specific:
                # Map to assistant's specific directories
                if category == "commands":
                    return assistant.commands_directory
                elif category == "memory":
                    return assistant.memory_directory
                else:
                    # Fallback for other AI-specific categories
                    return f"{assistant.base_directory}/{category}"
            else:
                # Use category defaults for non-AI-specific categories
                return category_config.resolve_target(assistant_name)
        except ValueError:
            # Unknown category, use generic pattern
            return f"{assistant.base_directory}/{category}"


# Module-level singleton for easy access
AI_DEFAULTS = AIAssistantDefaults()

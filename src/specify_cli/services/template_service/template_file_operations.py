"""
Template File Operations - handles file and path operations for templates.

This service handles:
- AI-specific directory mappings
- Output filename determination
- File categorization and classification
- Skip logic for updates
- Path resolution for different assistants
"""

import logging
from pathlib import Path
from typing import Optional

from specify_cli.assistants import get_all_assistants, get_assistant
from specify_cli.core.constants import CONSTANTS
from specify_cli.services.template_registry import TEMPLATE_REGISTRY

logger = logging.getLogger(__name__)


class TemplateFileOperations:
    """Service focused on template file and path operations."""

    def __init__(self):
        """Initialize template file operations service."""
        pass

    def get_ai_folder_mapping(self, ai_assistant: str) -> str:
        """Get AI-specific folder structure.

        Args:
            ai_assistant: Name of the AI assistant

        Returns:
            Directory path for the assistant's commands
        """
        assistant = get_assistant(ai_assistant)
        if assistant:
            return assistant.config.command_files.directory
        return f".{ai_assistant}/commands"

    def get_ai_context_folder_mapping(self, ai_assistant: str) -> str:
        """Get AI-specific context file directory.

        Args:
            ai_assistant: Name of the AI assistant

        Returns:
            Directory path for the assistant's context file
        """
        assistant = get_assistant(ai_assistant)
        if assistant:
            context_file_path = Path(assistant.config.context_file.file)
            if context_file_path.name == context_file_path.as_posix():
                return "."
            else:
                return str(context_file_path.parent)
        return f".{ai_assistant}"

    def determine_output_filename(
        self, template_name: str, ai_assistant: str, category: str
    ) -> str:
        """Determine output filename based on template, assistant, and category.

        Args:
            template_name: Name of the template file
            ai_assistant: Target AI assistant
            category: Template category

        Returns:
            Appropriate output filename for the target assistant
        """
        base_name = template_name
        if base_name.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
            base_name = base_name[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]

        assistant = get_assistant(ai_assistant)
        if not assistant:
            return base_name

        if base_name == "context-file" and category == "context":
            context_file_path = assistant.config.context_file.file
            return Path(context_file_path).name

        if category == "commands":
            file_format = assistant.config.command_files.file_format.value
        elif category == "context":
            file_format = assistant.config.context_file.file_format.value
        else:
            return base_name

        if "." in base_name:
            name_without_ext = base_name.rsplit(".", 1)[0]
            return f"{name_without_ext}.{file_format}"
        else:
            return f"{base_name}.{file_format}"

    def determine_output_path_for_ai(
        self,
        template_path: str,
        ai_assistant: str,
        project_path: Path,
    ) -> Optional[str]:
        """Determine where a template would be rendered for a specific AI assistant.

        Args:
            template_path: Path to the template
            ai_assistant: Target AI assistant
            project_path: Project root path (unused but kept for compatibility)

        Returns:
            Output path for the rendered template, or None if not applicable
        """
        _ = project_path  # Keep for compatibility

        if "/" not in template_path:
            return None

        category = template_path.split("/")[0]
        should_render = TEMPLATE_REGISTRY.should_render_category(category)

        if should_render and template_path.endswith(
            CONSTANTS.FILE.TEMPLATE_J2_EXTENSION
        ):
            base_path = template_path[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]
        else:
            base_path = template_path

        if "/" not in base_path:
            return None

        category, filename = base_path.split("/", 1)

        if category == "commands":
            assistant = get_assistant(ai_assistant)
            if assistant:
                commands_dir = assistant.config.command_files.directory
                return f"{commands_dir}/{filename}"
        elif category == "context":
            assistant = get_assistant(ai_assistant)
            if assistant:
                return assistant.config.context_file.file
        elif category == "scripts":
            return f"{CONSTANTS.DIRECTORY.SPECIFY_SCRIPTS_DIR}/{filename}"
        elif category == "memory":
            return f"{CONSTANTS.DIRECTORY.SPECIFY_MEMORY_DIR}/{filename}"
        elif category == "agent-prompts" or category == "agent-templates":
            cat_info = TEMPLATE_REGISTRY.get_category(category)
            if cat_info:
                base_path = cat_info.resolve_target(ai_assistant)
                if base_path:
                    return f"{base_path}/{filename}"
                return None

        return None

    def get_file_category(self, file_path: str) -> str:
        """Get category for a project file.

        Args:
            file_path: Path to the file

        Returns:
            Category classification of the file
        """
        if file_path.startswith(f"{CONSTANTS.DIRECTORY.SPECIFY_DIR}/"):
            if "scripts" in file_path:
                return "scripts"
            elif "memory" in file_path:
                return "memory"
            return "config"
        elif file_path.startswith("."):
            return "assistant"
        elif "/" not in file_path:
            return "root"
        else:
            return "other"

    def should_skip_file_update(self, file_path: str, project_path: Path) -> bool:
        """Determine if a file should be skipped during updates.

        Args:
            file_path: Path to the file
            project_path: Project root path

        Returns:
            True if file should be skipped during updates
        """
        if self.is_context_file(file_path, project_path):
            return True

        return file_path.startswith(f"{CONSTANTS.DIRECTORY.SPECIFY_MEMORY_DIR}/")

    def is_context_file(self, file_path: str, project_path: Path) -> bool:
        """Check if a file is a context file.

        Args:
            file_path: Path to the file
            project_path: Project root path (unused but kept for compatibility)

        Returns:
            True if the file is a context file for any assistant
        """
        _ = project_path  # Keep for compatibility

        assistants = get_all_assistants()
        for assistant in assistants:
            if file_path == assistant.config.context_file.file:
                return True
        return False

    def get_ai_directories(self, project_path: Path) -> list[str]:
        """Get list of AI assistant directories in the project.

        Args:
            project_path: Path to the project root

        Returns:
            List of AI assistant directory names found in the project
        """
        ai_dirs = []
        for dir_path in project_path.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith("."):
                known_assistants = ["claude", "copilot", "cursor", "gemini"]
                dir_name = dir_path.name[1:]
                if dir_name in known_assistants:
                    ai_dirs.append(dir_name)
        return ai_dirs

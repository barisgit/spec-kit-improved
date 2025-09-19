"""
Memory file import formatter service.

This module provides services for formatting memory file imports using
assistant-specific import syntax with proper error handling.
"""

from pathlib import Path
from typing import List, Optional

from specify_cli.assistants import get_assistant
from specify_cli.assistants.types import AssistantName

from .types import DiscoveredMemoryFile, FormattedMemoryImport


class MemoryFileFormatter:
    """Service for formatting memory file imports for different assistants."""

    def __init__(self, project_path: Path):
        """
        Initialize formatter service.

        Args:
            project_path: Path to the project root
        """
        self.project_path = project_path

    def format_imports_for_assistant(
        self,
        assistant_name: AssistantName,
        memory_files: List[DiscoveredMemoryFile],
        context_file_dir: Path,
    ) -> List[FormattedMemoryImport]:
        """
        Format memory file imports for a specific assistant.

        Args:
            assistant_name: Name of the assistant
            memory_files: List of memory files to format
            context_file_dir: Directory where the context file will be located

        Returns:
            List of formatted imports for the assistant
        """
        assistant = get_assistant(assistant_name)

        if not assistant:
            # Return empty list if assistant not found
            return []

        if not assistant.imports_supported:
            # Assistant doesn't support imports
            return []

        formatted_imports = []

        for memory_file in memory_files:
            # Only format existing files
            if not memory_file.exists:
                continue

            try:
                formatted_import_string = assistant.format_import(
                    context_file_dir, memory_file.path
                )

                if formatted_import_string:  # Only add non-empty imports
                    formatted_import = FormattedMemoryImport(
                        import_string=formatted_import_string,
                        source_file=memory_file,
                        assistant_name=assistant_name,
                    )
                    formatted_imports.append(formatted_import)

            except Exception:
                # Skip files that fail to format instead of crashing
                continue

        return formatted_imports

    def format_single_file(
        self,
        assistant_name: AssistantName,
        memory_file: DiscoveredMemoryFile,
        context_file_dir: Path,
    ) -> Optional[FormattedMemoryImport]:
        """
        Format a single memory file import.

        Args:
            assistant_name: Name of the assistant
            memory_file: Memory file to format
            context_file_dir: Directory where the context file will be located

        Returns:
            Formatted import or None if formatting fails
        """
        formatted_imports = self.format_imports_for_assistant(
            assistant_name, [memory_file], context_file_dir
        )

        return formatted_imports[0] if formatted_imports else None

    def get_assistant_context_dir(
        self, assistant_name: AssistantName
    ) -> Optional[Path]:
        """
        Get the context file directory for an assistant.

        Args:
            assistant_name: Name of the assistant

        Returns:
            Context file directory path or None if assistant not found
        """
        assistant = get_assistant(assistant_name)

        if not assistant or not assistant.config:
            return None

        context_file_path = self.project_path / assistant.config.context_file.file
        return context_file_path.parent

    def supports_imports(self, assistant_name: AssistantName) -> bool:
        """
        Check if an assistant supports file imports.

        Args:
            assistant_name: Name of the assistant

        Returns:
            True if the assistant supports imports
        """
        assistant = get_assistant(assistant_name)
        return assistant is not None and assistant.imports_supported

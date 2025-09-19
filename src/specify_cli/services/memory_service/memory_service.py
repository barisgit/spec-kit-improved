"""
Memory file management for dynamic imports in context files.

This module provides a backwards-compatible interface to the new type-safe
memory management system while maintaining the same API.
"""

from pathlib import Path
from typing import List, Optional

from specify_cli.assistants.types import AssistantName

from . import MemoryConfigManager, MemoryFileDiscovery, MemoryFileFormatter
from .types import MemoryImportSection


class MemoryManager:
    """
    Manages memory file discovery and import formatting.

    This class provides a backwards-compatible interface to the new type-safe
    memory management system.
    """

    def __init__(self, project_path: Path):
        """Initialize with project path."""
        self.project_path = project_path
        self.memory_path = project_path / ".specify" / "memory"

        # Initialize the new type-safe services
        self._config_manager = MemoryConfigManager(project_path)
        self._discovery = MemoryFileDiscovery(
            project_path, self._config_manager.load_config()
        )
        self._formatter = MemoryFileFormatter(project_path)

    def discover_memory_files(
        self, extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """
        Discover available memory files in .specify/memory directory.

        Args:
            extensions: List of file extensions to include (e.g., ['.md', '.txt'])
                       If None, uses configured extensions.

        Returns:
            List of Path objects for discovered memory files
        """
        # Use new discovery service but maintain backwards compatibility
        discovered_files = self._discovery.discover_existing_files_only()

        # Filter by extensions if provided
        if extensions is not None:
            discovered_files = [
                f for f in discovered_files if f.path.suffix.lower() in extensions
            ]

        return [f.path for f in discovered_files]

    def get_default_import_list(self) -> List[str]:
        """
        Get default list of memory files to import.

        Returns priority files like constitution.md first.
        """
        discovered_files = self._discovery.discover_existing_files_only()
        return [f.filename for f in discovered_files]

    def format_imports_for_assistant(
        self,
        ai_assistant: AssistantName,
        context_file_dir: Path,
        import_list: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Format memory file imports using the assistant's format_import method.

        Args:
            ai_assistant: Name of the AI assistant
            context_file_dir: Directory where the context file will be located
            import_list: List of memory filenames to import. If None, uses all discovered files.

        Returns:
            List of formatted import strings for the assistant
        """
        if not self._formatter.supports_imports(ai_assistant):
            return []

        # Get files to import
        if import_list is None:
            memory_files = self._discovery.discover_existing_files_only()
        else:
            # Filter discovered files by the provided import list
            all_files = self._discovery.discover_existing_files_only()
            memory_files = [f for f in all_files if f.filename in import_list]

        # Format imports
        formatted_imports = self._formatter.format_imports_for_assistant(
            ai_assistant, memory_files, context_file_dir
        )

        return [imp.import_string for imp in formatted_imports]

    def generate_import_section(
        self,
        ai_assistant: AssistantName,
        context_file_dir: Path,
        import_list: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a complete import section for context files.

        Args:
            ai_assistant: Name of the AI assistant
            context_file_dir: Directory where the context file will be located
            import_list: List of memory filenames to import

        Returns:
            Formatted string with all imports, or empty string if none available
        """
        if not self._formatter.supports_imports(ai_assistant):
            return ""

        # Get files to import
        if import_list is None:
            memory_files = self._discovery.discover_existing_files_only()
        else:
            # Filter discovered files by the provided import list
            all_files = self._discovery.discover_existing_files_only()
            memory_files = [f for f in all_files if f.filename in import_list]

        if not memory_files:
            return ""

        # Format imports
        formatted_imports = self._formatter.format_imports_for_assistant(
            ai_assistant, memory_files, context_file_dir
        )

        if not formatted_imports:
            return ""

        # Create and render section
        section = MemoryImportSection(
            imports=formatted_imports,
            assistant_name=ai_assistant,
            has_constitution=any(
                f.source_file.category.value == "constitution"
                for f in formatted_imports
            ),
            has_other_files=any(
                f.source_file.category.value != "constitution"
                for f in formatted_imports
            ),
        )

        return section.render()

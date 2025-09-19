"""
Memory file discovery service with type-safe pattern matching.

This module provides services for discovering memory files in project directories
with configurable patterns and categorization.
"""

import fnmatch
from pathlib import Path
from typing import List, Optional

from .types import (
    DiscoveredMemoryFile,
    MemoryCategory,
    MemoryFilePattern,
    MemoryImportConfig,
)


class MemoryFileDiscovery:
    """Service for discovering memory files with pattern matching."""

    def __init__(self, project_path: Path, config: Optional[MemoryImportConfig] = None):
        """
        Initialize discovery service.

        Args:
            project_path: Path to the project root
            config: Configuration for memory imports. Uses defaults if None.
        """
        self.project_path = project_path
        self.memory_path = project_path / ".specify" / "memory"
        self.config = config or MemoryImportConfig()

    def discover_all_files(self) -> List[DiscoveredMemoryFile]:
        """
        Discover all memory files matching the configured patterns.

        Returns:
            List of discovered files sorted by priority and category
        """
        if not self.config.enabled:
            return []

        if not self.memory_path.exists():
            return []

        discovered_files = []

        # Get all files with matching extensions
        all_files = []
        for file_path in self.memory_path.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.config.extensions
            ):
                all_files.append(file_path)

        # Match against patterns
        for file_path in all_files:
            matched_pattern = self._match_file_to_pattern(file_path)
            if matched_pattern:
                discovered_file = DiscoveredMemoryFile(
                    path=file_path,
                    filename=file_path.name,
                    category=matched_pattern.category,
                    priority=matched_pattern.priority,
                    exists=file_path.exists(),
                )
                discovered_files.append(discovered_file)

        # Sort by priority (lower = higher priority) then by filename
        discovered_files.sort(key=lambda f: (f.priority, f.filename))

        # Limit results
        return discovered_files[: self.config.max_files]

    def discover_by_category(
        self, category: MemoryCategory
    ) -> List[DiscoveredMemoryFile]:
        """
        Discover memory files for a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of discovered files in the specified category
        """
        all_files = self.discover_all_files()
        return [f for f in all_files if f.category == category]

    def discover_existing_files_only(self) -> List[DiscoveredMemoryFile]:
        """
        Discover only memory files that actually exist.

        Returns:
            List of discovered files that exist on disk
        """
        all_files = self.discover_all_files()
        return [f for f in all_files if f.exists]

    def has_constitution_files(self) -> bool:
        """
        Check if any constitution files exist.

        Returns:
            True if constitution files are found
        """
        constitution_files = self.discover_by_category(MemoryCategory.CONSTITUTION)
        return len(constitution_files) > 0 and any(f.exists for f in constitution_files)

    def get_priority_files(self, max_priority: int = 10) -> List[DiscoveredMemoryFile]:
        """
        Get high-priority memory files.

        Args:
            max_priority: Maximum priority value to include (lower = higher priority)

        Returns:
            List of high-priority files
        """
        all_files = self.discover_existing_files_only()
        return [f for f in all_files if f.priority <= max_priority]

    def _match_file_to_pattern(self, file_path: Path) -> Optional[MemoryFilePattern]:
        """
        Match a file against configured patterns.

        Args:
            file_path: Path to the file to match

        Returns:
            Matching pattern or None if no match
        """
        filename = file_path.name

        # Find the first matching pattern (patterns are already sorted by priority)
        for pattern in self.config.patterns:
            if fnmatch.fnmatch(filename, pattern.filename_pattern):
                return pattern

        # If no specific pattern matches, categorize as OTHER
        return MemoryFilePattern(
            filename_pattern=filename,
            category=MemoryCategory.OTHER,
            priority=999,  # Low priority for uncategorized files
        )

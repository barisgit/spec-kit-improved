"""
Memory file management services.

This module provides type-safe, configurable services for discovering,
categorizing, and formatting memory file imports for AI assistants.
"""

from .config import MemoryConfigManager
from .discovery import MemoryFileDiscovery
from .formatter import MemoryFileFormatter
from .memory_service import MemoryManager
from .types import (
    AssistantImportMap,
    DiscoveredMemoryFile,
    FormattedMemoryImport,
    MemoryCategory,
    MemoryFileMap,
    MemoryFilePattern,
    MemoryImportConfig,
    MemoryImportSection,
)

__all__ = [
    # Main services
    "MemoryConfigManager",
    "MemoryFileDiscovery",
    "MemoryFileFormatter",
    "MemoryManager",
    # Types
    "MemoryCategory",
    "MemoryFilePattern",
    "MemoryImportConfig",
    "DiscoveredMemoryFile",
    "FormattedMemoryImport",
    "MemoryImportSection",
    # Type aliases
    "MemoryFileMap",
    "AssistantImportMap",
]

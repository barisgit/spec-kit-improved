"""
Developer defaults for SpecifyX

This package provides immutable developer defaults that are packaged with SpecifyX.
These are NOT user configuration - they are maintainable constants that replace
hardcoded values throughout the codebase.

Main modules:
- ai_defaults: AI assistant configurations and directory mappings
- category_defaults: Template category configurations and folder mappings
- path_defaults: Template processing, path resolution, and project structure defaults
"""

from .ai_defaults import AI_DEFAULTS, AIAssistant, AIAssistantDefaults
from .branch_defaults import (
    BRANCH_DEFAULTS,
    BranchNamingDefaults,
    BranchNamingPattern,
)
from .category_defaults import (
    CATEGORY_DEFAULTS,
    CategoryDefaults,
    CategoryMapping,
    FolderMappingResult,
)
from .path_defaults import (
    PATH_DEFAULTS,
    PathDefaults,
    ProjectContextVars,
    ProjectDefaults,
)

__all__ = [
    "AI_DEFAULTS",
    "AIAssistant",
    "AIAssistantDefaults",
    "BRANCH_DEFAULTS",
    "BranchNamingDefaults",
    "BranchNamingPattern",
    "CATEGORY_DEFAULTS",
    "CategoryDefaults",
    "CategoryMapping",
    "FolderMappingResult",
    "PATH_DEFAULTS",
    "PathDefaults",
    "ProjectContextVars",
    "ProjectDefaults",
]

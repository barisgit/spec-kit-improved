"""
Developer defaults for SpecifyX

This package provides immutable developer defaults that are packaged with SpecifyX.
These are NOT user configuration - they are maintainable constants that replace
hardcoded values throughout the codebase.

Main modules:
- branch_defaults: Branch naming patterns and conventions
- category_defaults: Template category configurations and folder mappings (deprecated - use TemplateRegistry)
- path_defaults: Template processing, path resolution, and project structure defaults (deprecated - use TemplateRegistry)

NOTE: ai_defaults has been removed - use the assistant registry instead (specify_cli.assistants)
"""

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

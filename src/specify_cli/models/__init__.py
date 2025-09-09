"""
Data models for spec-kit

This module provides all data structures used throughout the application
for configuration, project management, templating, and script generation.
"""

# Configuration models
from .config import (
    BranchNamingConfig,
    ProjectConfig,
    TemplateConfig,
)

# Project and template context models
from .project import (
    ProjectInitOptions,
    ProjectInitResult,
    ProjectInitStep,
    TemplateContext,
    TemplateDict,
    TemplateFile,
)

# Script generation models
from .script import (
    GeneratedScript,
    ScriptState,
)

# Template processing models
from .template import (
    GranularTemplate,
    TemplateCategory,
    TemplatePackage,
    TemplateState,
)

__all__ = [
    # Configuration
    "BranchNamingConfig",
    "ProjectConfig",
    "TemplateConfig",
    # Project and context
    "ProjectInitOptions",
    "ProjectInitResult",
    "ProjectInitStep",
    "TemplateContext",
    "TemplateDict",
    "TemplateFile",
    # Script generation
    "GeneratedScript",
    "ScriptState",
    # Template processing
    "GranularTemplate",
    "TemplateCategory",
    "TemplatePackage",
    "TemplateState",
]

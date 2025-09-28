"""
Utils package - centralized utility services and helpers.

This package provides:
- FileOperationsService: File and path operations
- PathResolverService: Path resolution logic
- ValidationService: Validation patterns and rules
- AgentNameExtractor: Agent name parsing and extraction
- ScriptHelpers: Unified script utilities (modernized)
- Focused helper modules for specific operations
"""

from .agent_name_extractor import AgentNameExtractor
from .file_operations_service import FileOperationsService

# Import helpers for direct access
from .helpers import (
    BranchNamingHelper,
    CliUtilities,
    ConfigurationHelper,
    FeatureDiscoveryHelper,
    GitOperationsHelper,
    TemplateRenderingHelper,
    echo_debug,
    echo_error,
    echo_info,
    echo_success,
)
from .path_resolver_service import PathResolverService
from .script_helpers import ScriptHelpers, get_script_helpers
from .validation_service import ValidationResult, ValidationService

__all__ = [
    # Core utility services
    "FileOperationsService",
    "PathResolverService",
    "ValidationService",
    "ValidationResult",
    "AgentNameExtractor",
    # Script utilities (unified interface)
    "ScriptHelpers",
    "get_script_helpers",
    # Focused helpers (for direct use)
    "GitOperationsHelper",
    "ConfigurationHelper",
    "BranchNamingHelper",
    "FeatureDiscoveryHelper",
    "TemplateRenderingHelper",
    "CliUtilities",
    # Convenience functions
    "echo_info",
    "echo_debug",
    "echo_error",
    "echo_success",
]

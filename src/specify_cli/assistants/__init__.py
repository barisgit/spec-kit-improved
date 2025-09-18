"""
AI Assistant organization system for SpecifyX.

This package provides a type-safe, modular system for organizing AI assistant
logic, replacing hardcoded configurations with clean, pluggable components.
"""

from .assistant_registry import StaticAssistantRegistry
from .constants import (
    ALL_INJECTION_POINTS,
    OPTIONAL_INJECTION_POINTS,
    REQUIRED_INJECTION_POINTS,
    InjectionPointNames,
)
from .injection_points import InjectionPoint
from .interfaces import (
    AssistantFactory,
    AssistantProvider,
    ValidationResult,
)
from .interfaces import (
    AssistantRegistry as IAssistantRegistry,
)
from .interfaces import (
    # Backward compatibility
    InjectionValues as InjectionPoints,
)
from .registry import (
    get_all_assistants,
    get_assistant,
    is_assistant_registered,
    list_assistant_names,
    registry,
    validate_all,
)
from .types import (
    AssistantConfig,
    AssistantName,
    AssistantPath,
    AssistantPaths,
    ContextFileConfig,
    FileFormat,
    InjectionValues,
    TemplateConfig,
)

__all__ = [
    # Registry (concrete implementation & instance)
    "StaticAssistantRegistry",
    "registry",
    # Convenience functions
    "get_all_assistants",
    "get_assistant",
    "is_assistant_registered",
    "list_assistant_names",
    "validate_all",
    # Types
    "AssistantConfig",
    "AssistantName",
    "AssistantPath",
    "AssistantPaths",
    "ContextFileConfig",
    "FileFormat",
    "TemplateConfig",
    "ValidationResult",
    # ABC Interfaces
    "AssistantProvider",
    "AssistantFactory",
    "IAssistantRegistry",
    "InjectionValues",
    "InjectionPoint",
    # Backward compatibility
    "InjectionPoints",  # Alias for InjectionValues
    # Constants
    "InjectionPointNames",
    "REQUIRED_INJECTION_POINTS",
    "OPTIONAL_INJECTION_POINTS",
    "ALL_INJECTION_POINTS",
]

"""
Type-safe contracts for AI assistant organization system.

This package provides typed interfaces for organizing AI assistant logic
in SpecifyX through simple folder structure and injection points, without
the complexity of a full plugin system.

The contracts define:
- AssistantConfig: Typed configuration for assistant definitions
- InjectionProvider: Interface for providing template injection points
- AssistantRegistry: Static registry for managing assistants
- TemplateContext: Enhanced context with assistant injections
- Various validation and processing protocols

All interfaces are designed for static typing and build-time validation
rather than runtime discovery for maximum performance and type safety.
"""

from .assistant_config_interface import (
    AssistantConfig,
    AssistantValidator,
    DocumentationGenerator,
    InjectionPointNames,
    InjectionProvider,
    OPTIONAL_INJECTION_POINTS,
    REQUIRED_INJECTION_POINTS,
)
from .assistant_registry_interface import (
    AssistantRegistry,
    BuildTimeValidator,
    RegistryInitializer,
    TemplateEnhancer,
)
from .template_injection_interface import (
    ConditionalConverter,
    InjectionPointResolver,
    InjectionValidator,
    TemplateAnalyzer,
    TemplateContext,
    TemplateRenderer,
)

# Type aliases for convenience
from .assistant_config_interface import (
    AssistantName,
    InjectionPoints,
    ValidationErrors,
)

__all__ = [
    # Core configuration types
    "AssistantConfig",
    "InjectionProvider",
    "AssistantName",
    "InjectionPoints",
    "ValidationErrors",

    # Registry interfaces
    "AssistantRegistry",
    "RegistryInitializer",
    "BuildTimeValidator",

    # Template interfaces
    "TemplateContext",
    "TemplateRenderer",
    "InjectionPointResolver",
    "ConditionalConverter",
    "TemplateAnalyzer",
    "TemplateEnhancer",

    # Validation interfaces
    "AssistantValidator",
    "InjectionValidator",

    # Documentation interfaces
    "DocumentationGenerator",

    # Constants
    "InjectionPointNames",
    "REQUIRED_INJECTION_POINTS",
    "OPTIONAL_INJECTION_POINTS",
]
"""
Type-safe contracts for the assistant registry system.

This module defines interfaces for the static registry that manages
AI assistant configurations and injection providers.
"""

from typing import Any, Dict, List, Optional, Protocol

from specify_cli.assistants.interfaces import AssistantProvider
from specify_cli.assistants.types import (
    AssistantConfig,
    AssistantName,
    InjectionValues,
)


class AssistantRegistry(Protocol):
    """
    Protocol for the static assistant registry.

    Manages AI assistant configurations and injection providers
    through static imports rather than dynamic discovery.
    """

    @property
    def assistants(self) -> List[AssistantConfig]:
        """
        Get all registered assistant configurations.

        Returns:
            List of all assistant configurations
        """
        ...

    @property
    def assistant_names(self) -> List[AssistantName]:
        """
        Get list of all assistant names.

        Returns:
            List of assistant names for CLI choices
        """
        ...

    def get_assistant_config(self, name: AssistantName) -> Optional[AssistantConfig]:
        """
        Get assistant configuration by name.

        Args:
            name: Assistant name to look up

        Returns:
            Assistant configuration or None if not found
        """
        ...

    def get_injection_provider(
        self, name: AssistantName
    ) -> Optional[AssistantProvider]:
        """
        Get injection provider for assistant.

        Args:
            name: Assistant name to look up

        Returns:
            Injection provider or None if not found
        """
        ...

    def get_injections(self, name: AssistantName) -> InjectionValues:
        """
        Get injection points for assistant.

        Args:
            name: Assistant name to get injections for

        Returns:
            Dictionary of injection point names to values
        """
        ...

    def validate_all(self) -> List[str]:
        """
        Validate all registered assistants.

        Returns:
            List of validation errors (empty if all valid)
        """
        ...


class TemplateEnhancer(Protocol):
    """
    Protocol for enhancing templates with injection points.

    Provides methods for converting templates from conditional
    logic to clean injection points.
    """

    def identify_conditionals(self, template_content: str) -> List[str]:
        """
        Identify conditional logic in template that can be replaced.

        Args:
            template_content: Template content to analyze

        Returns:
            List of conditional blocks found
        """
        ...

    def convert_to_injection_points(self, template_content: str) -> str:
        """
        Convert template conditionals to injection points.

        Args:
            template_content: Original template with conditionals

        Returns:
            Enhanced template with injection points
        """
        ...

    def validate_injection_usage(self, template_content: str) -> List[str]:
        """
        Validate injection point usage in template.

        Args:
            template_content: Template content to validate

        Returns:
            List of validation errors (empty if valid)
        """
        ...


class BuildTimeValidator(Protocol):
    """
    Protocol for build-time validation of assistant system.

    Ensures type safety and configuration correctness at build time
    rather than runtime for faster feedback.
    """

    def validate_type_safety(self) -> List[str]:
        """
        Validate type safety across all assistant modules.

        Returns:
            List of type safety violations
        """
        ...

    def validate_injection_points(self) -> List[str]:
        """
        Validate injection point definitions and usage.

        Returns:
            List of injection point validation errors
        """
        ...

    def validate_template_compatibility(self) -> List[str]:
        """
        Validate template compatibility with all assistants.

        Returns:
            List of template compatibility issues
        """
        ...

    def generate_validation_report(self) -> str:
        """
        Generate comprehensive validation report.

        Returns:
            Markdown formatted validation report
        """
        ...


# Registry initialization and management
class RegistryInitializer(Protocol):
    """
    Protocol for initializing the assistant registry.

    Handles static import and validation of all assistant modules.
    """

    def load_assistants(self) -> List[AssistantConfig]:
        """
        Load all assistant configurations from static imports.

        Returns:
            List of loaded assistant configurations
        """
        ...

    def load_injection_providers(self) -> Dict[AssistantName, AssistantProvider]:
        """
        Load all injection providers from static imports.

        Returns:
            Dictionary mapping assistant names to providers
        """
        ...

    def validate_consistency(
        self,
        configs: List[AssistantConfig],
        providers: Dict[AssistantName, AssistantProvider],
    ) -> List[str]:
        """
        Validate consistency between configs and providers.

        Args:
            configs: Assistant configurations
            providers: Injection providers

        Returns:
            List of consistency validation errors
        """
        ...


# Type aliases for registry operations
RegistryState = Dict[str, Any]
LoadResult = tuple[List[AssistantConfig], Dict[AssistantName, AssistantProvider]]
InitializationResult = tuple[bool, List[str]]

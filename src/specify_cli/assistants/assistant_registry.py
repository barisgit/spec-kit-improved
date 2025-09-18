"""
Concrete implementation of the AssistantRegistry.

This module provides the StaticAssistantRegistry class that implements
the AssistantRegistry ABC with a simple dictionary-based storage system.
"""

from typing import Dict, List, Optional

from .interfaces import AssistantProvider, AssistantRegistry, ValidationResult
from .types import AssistantName


class StaticAssistantRegistry(AssistantRegistry):
    """
    Static registry implementation for managing assistant providers.

    Uses dictionary-based storage with validation and type safety.
    Suitable for applications with a known set of assistants.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._assistants: Dict[AssistantName, AssistantProvider] = {}

    def register_assistant(self, assistant: AssistantProvider) -> None:
        """Register an assistant provider instance in the registry."""
        if not isinstance(assistant, AssistantProvider):
            raise TypeError(
                f"Assistant must implement AssistantProvider, got {type(assistant)}"
            )

        # Validate the assistant configuration
        config = assistant.config
        if not config.name:
            raise ValueError("Assistant must have a non-empty name")

        # Check for name conflicts
        if config.name in self._assistants:
            raise ValueError(f"Assistant '{config.name}' is already registered")

        # Store the assistant
        self._assistants[config.name] = assistant

    def get_assistant(self, name: AssistantName) -> Optional[AssistantProvider]:
        """Retrieve a registered assistant by name."""
        if not isinstance(name, str):
            raise TypeError(
                f"Assistant name must be a string, got {type(name).__name__}"
            )
        return self._assistants.get(name)

    def get_all_assistants(self) -> List[AssistantProvider]:
        """Get all currently registered assistant instances."""
        return list(self._assistants.values())

    def validate_all(self) -> Dict[AssistantName, ValidationResult]:
        """Validate all registered assistants and return comprehensive results."""
        results: Dict[AssistantName, ValidationResult] = {}

        for name, assistant in self._assistants.items():
            try:
                results[name] = assistant.validate_setup()
            except (AttributeError, TypeError, ValueError) as e:
                # If validation itself fails, create an error result
                results[name] = ValidationResult(
                    is_valid=False, errors=[f"Validation failed: {str(e)}"], warnings=[]
                )
            except Exception as e:
                # Catch-all for unexpected errors
                results[name] = ValidationResult(
                    is_valid=False,
                    errors=[f"Unexpected validation error: {str(e)}"],
                    warnings=[],
                )

        return results

    def unregister_assistant(self, name: AssistantName) -> bool:
        """Remove an assistant from the registry."""
        if not isinstance(name, str):
            raise TypeError(
                f"Assistant name must be a string, got {type(name).__name__}"
            )
        if name in self._assistants:
            del self._assistants[name]
            return True
        return False

    def clear(self) -> None:
        """Remove all assistants from the registry."""
        self._assistants.clear()

    def list_assistant_names(self) -> List[AssistantName]:
        """Get list of all registered assistant names."""
        return list(self._assistants.keys())

    def is_registered(self, name: AssistantName) -> bool:
        """Check if an assistant is registered."""
        if not isinstance(name, str):
            raise TypeError(
                f"Assistant name must be a string, got {type(name).__name__}"
            )
        return name in self._assistants

    def __len__(self) -> int:
        """Return number of registered assistants."""
        return len(self._assistants)

    def __contains__(self, name: AssistantName) -> bool:
        """Support 'in' operator for checking registration."""
        if not isinstance(name, str):
            raise TypeError(
                f"Assistant name must be a string, got {type(name).__name__}"
            )
        return name in self._assistants

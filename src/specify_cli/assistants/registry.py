"""
Main registry instance with all assistant providers registered.

This module provides the main registry instance that applications should use.
All assistant providers are automatically registered and ready for use.

Usage:
    from specify_cli.assistants.registry import registry

    # Get a specific assistant
    claude = registry.get_assistant("claude")
    if claude:
        injections = claude.get_injection_values()

    # Get all assistants
    all_assistants = registry.get_all_assistants()

    # Validate all assistants
    results = registry.validate_all()
    for name, result in results.items():
        if not result.is_valid:
            print(f"{name}: {result.errors}")
"""

from .assistant_registry import StaticAssistantRegistry

# Import all providers
from .claude import ClaudeProvider
from .copilot import CopilotProvider
from .cursor import CursorProvider
from .gemini import GeminiProvider

# Create the main registry instance
registry = StaticAssistantRegistry()

# Register all providers
registry.register_assistant(ClaudeProvider())
registry.register_assistant(CopilotProvider())
registry.register_assistant(CursorProvider())
registry.register_assistant(GeminiProvider())


# Convenience functions for backward compatibility and ease of use
def get_assistant(name: str):
    """Get an assistant by name."""
    return registry.get_assistant(name)


def get_all_assistants():
    """Get all registered assistants."""
    return registry.get_all_assistants()


def validate_all():
    """Validate all registered assistants."""
    return registry.validate_all()


def list_assistant_names():
    """Get list of all assistant names."""
    return registry.list_assistant_names()


def is_assistant_registered(name: str) -> bool:
    """Check if an assistant is registered."""
    return registry.is_registered(name)

"""
Claude AI assistant module.

This module provides a modular Claude assistant implementation with
separate components for configuration, injection management, validation,
and setup instructions.

Architecture:
- ClaudeProvider: Main orchestrator implementing AssistantProvider
- ClaudeConfig: Configuration management
- ClaudeInjectionManager: Template injection points
- ClaudeValidator: Setup and environment validation
- ClaudeSetupManager: Installation and setup guidance

Usage:
    from specify_cli.assistants.claude import ClaudeProvider

    provider = ClaudeProvider()
    config = provider.config
    injections = provider.get_injection_values()
"""

from .provider import ClaudeProvider
from .validator import ClaudeValidator

__all__ = [
    "ClaudeProvider",
    "ClaudeValidator",
]

"""
Gemini AI assistant module.

This module provides a modular Gemini assistant implementation with
separate components for configuration, injection management, validation,
and setup instructions.

Architecture:
- GeminiProvider: Main orchestrator implementing AssistantProvider
- GeminiConfig: Configuration management
- GeminiInjectionManager: Template injection points
- GeminiValidator: Setup and environment validation
- GeminiSetupManager: Installation and setup guidance

Usage:
    from specify_cli.assistants.gemini import GeminiProvider

    provider = GeminiProvider()
    config = provider.config
    injections = provider.get_injection_values()
"""

from .provider import GeminiProvider
from .validator import GeminiValidator

__all__ = [
    "GeminiProvider",
    "GeminiInjectionManager",
    "GeminiValidator",
]

"""
GitHub Copilot AI assistant configuration module.

This module provides GitHub Copilot-specific configuration and injection
providers for SpecifyX project initialization. Copilot uses GitHub's
standard directory structure with .github as the base directory.
"""

from .provider import CopilotProvider

__all__ = ["CopilotProvider"]

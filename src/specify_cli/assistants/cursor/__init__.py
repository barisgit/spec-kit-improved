"""
Cursor AI assistant configuration module.

This module provides Cursor-specific configuration and injection providers
for the type-safe AI assistant organization system. Cursor is an AI-powered
code editor that uses MDC rule files for configuration.

The Cursor assistant organizes files under .cursor/ directory:
- Base directory: .cursor
- Context file: .cursor/rules/main.mdc (MDC rule file)
- Commands directory: .cursor/rules (rules directory for commands)
- Memory directory: .cursor/rules (rules directory for memory/constitution)
"""

from .provider import CursorProvider

__all__ = ["CursorProvider"]

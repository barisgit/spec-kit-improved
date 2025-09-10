#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#    "typer",
#    "rich",
#    "httpx",
#    "platformdirs",
#    "readchar",
#    "jinja2",
#    "dynaconf",
#    "tomli-w"
# ]
# ///

"""
SpecifyX CLI - Enhanced spec-driven development CLI

Usage:
    uvx specifyx init <project-name>
    uvx specifyx init --here

Or install globally:
    uv tool install specifyx
    specifyx init <project-name>
    specifyx init --here
"""

from .core.app import main

if __name__ == "__main__":
    main()

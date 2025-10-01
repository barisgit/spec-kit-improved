"""
Template Rendering Helper - focused on standalone template rendering.

This helper handles:
- Standalone template rendering without full project initialization
- Context preparation for templates
- Platform-aware template variables
- Template file operations
"""

import contextlib
import platform
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from specify_cli.core.constants import CONSTANTS
from specify_cli.models.project import TemplateContext
from specify_cli.services.template_service import JinjaTemplateService

from .configuration_helper import ConfigurationHelper
from .git_operations_helper import GitOperationsHelper


class TemplateRenderingHelper:
    """Helper for template rendering operations."""

    def __init__(self):
        """Initialize with supporting services."""
        self._template_service = JinjaTemplateService()
        self._config_helper = ConfigurationHelper()
        self._git_helper = GitOperationsHelper()

    def render_template_standalone(
        self,
        template_path: Path,
        output_path: Path,
        context_variables: Optional[Dict[str, Any]] = None,
        make_executable: bool = False,
    ) -> bool:
        """
        Render a single template file without full project initialization.

        Args:
            template_path: Path to template file
            output_path: Where to write rendered output
            context_variables: Additional context variables
            make_executable: Whether to make output file executable

        Returns:
            bool: True if rendering succeeded
        """
        try:
            if not template_path.exists():
                return False

            # Prepare template context
            context = self._prepare_standalone_context(context_variables or {})

            # Setup Jinja2 environment
            template_dir = template_path.parent
            env = Environment(loader=FileSystemLoader(str(template_dir)))

            # Add custom filters
            def regex_replace(value: str, pattern: str, replacement: str = "") -> str:
                """Jinja2 filter for regex replacement"""
                import re

                return re.sub(pattern, replacement, value)

            env.filters["regex_replace"] = regex_replace  # type: ignore

            # Load and render template
            template = env.get_template(template_path.name)
            rendered_content = template.render(context)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write rendered content
            output_path.write_text(rendered_content, encoding="utf-8")

            # Make executable if requested
            if make_executable:
                self._make_file_executable(output_path)

            return True

        except Exception:
            return False

    def prepare_template_context(
        self, base_context: Optional[Dict[str, Any]] = None
    ) -> TemplateContext:
        """
        Prepare a complete template context for rendering.

        Args:
            base_context: Base context variables to include

        Returns:
            TemplateContext: Complete context object
        """
        context_dict = base_context or {}

        # Add project information
        context_dict.update(
            {
                "project_name": self._config_helper.get_project_name(),
                "ai_assistant": self._config_helper.get_ai_assistant_config(),
                "created_date": self._config_helper.get_current_date(),
                "author_name": self._git_helper.get_author_name(),
            }
        )

        # Add platform information
        context_dict.update(self._get_platform_context())

        # Add repository information
        repo_root = self._git_helper.get_repo_root()
        current_branch = self._git_helper.get_current_branch()
        context_dict.update(
            {
                "repo_root": str(repo_root),
                "current_branch": current_branch or "main",
                "is_git_repo": self._git_helper.check_git_repository(),
            }
        )

        # Create TemplateContext object
        return TemplateContext(**context_dict)

    def validate_template_syntax(
        self, template_path: Path
    ) -> tuple[bool, Optional[str]]:
        """
        Validate template syntax without rendering.

        Args:
            template_path: Path to template file

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            if not template_path.exists():
                return False, f"Template file not found: {template_path}"

            # Setup Jinja2 environment
            template_dir = template_path.parent
            env = Environment(loader=FileSystemLoader(str(template_dir)))

            # Try to parse template
            template_content = template_path.read_text(encoding="utf-8")
            env.parse(template_content)

            return True, None

        except Exception as e:
            return False, str(e)

    def extract_template_variables(self, template_path: Path) -> list[str]:
        """
        Extract variables used in a template.

        Args:
            template_path: Path to template file

        Returns:
            list[str]: List of variable names
        """
        try:
            if not template_path.exists():
                return []

            template_content = template_path.read_text(encoding="utf-8")
            env = Environment()
            ast = env.parse(template_content)

            from jinja2.meta import find_undeclared_variables

            variables = find_undeclared_variables(ast)

            return sorted(variables)

        except Exception:
            return []

    def _prepare_standalone_context(
        self, additional_vars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare context for standalone template rendering.

        Args:
            additional_vars: Additional variables to include

        Returns:
            Dict[str, Any]: Complete context dictionary
        """
        context = {}

        # Add project basics
        context.update(
            {
                "project_name": self._config_helper.get_project_name(),
                "ai_assistant": self._config_helper.get_ai_assistant_config(),
                "created_date": self._config_helper.get_current_date(),
                "author_name": self._git_helper.get_author_name(),
            }
        )

        # Add platform information
        context.update(self._get_platform_context())

        # Add git information
        context.update(
            {
                "current_branch": self._git_helper.get_current_branch() or "main",
                "repo_root": str(self._git_helper.get_repo_root()),
            }
        )

        # Add additional variables
        context.update(additional_vars)

        return context

    def _get_platform_context(self) -> Dict[str, Any]:
        """Get platform-specific context variables."""
        system = platform.system().lower()

        context = {
            "platform_system": system,
            "platform_python_version": platform.python_version(),
        }

        if system == "windows":
            context.update(
                {
                    "path_separator": "\\",
                    "script_extension": CONSTANTS.FILE.BATCH_EXTENSION,
                }
            )
        else:
            context.update(
                {
                    "path_separator": "/",
                    "script_extension": CONSTANTS.FILE.SHELL_EXTENSION,
                }
            )

        return context

    def _make_file_executable(self, file_path: Path) -> None:
        """Make a file executable."""
        with contextlib.suppress(Exception):
            # Ignore permission errors
            file_path.chmod(CONSTANTS.FILE.EXECUTABLE_PERMISSIONS)

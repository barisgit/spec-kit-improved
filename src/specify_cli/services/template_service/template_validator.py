"""
Template Validation Service - focused on template syntax validation and analysis.

This service handles:
- Template syntax validation
- Variable extraction from templates
- Template structure analysis
- Validation error reporting
"""

import logging
from pathlib import Path
from typing import List, Tuple

from jinja2 import Environment, TemplateSyntaxError
from jinja2.meta import find_undeclared_variables

from specify_cli.core.constants import CONSTANTS

logger = logging.getLogger(__name__)


class TemplateValidator:
    """Service focused on template validation and analysis."""

    def __init__(self):
        """Initialize template validator."""
        self._environment = Environment()

    def validate_template_syntax(self, template_path: Path) -> Tuple[bool, str]:
        """Validate template syntax.

        Args:
            template_path: Path to template file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not template_path.exists():
                return False, f"Template file not found: {template_path}"

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Parse template to check for syntax errors
            self._environment.parse(template_content)
            return True, ""

        except TemplateSyntaxError as e:
            return False, CONSTANTS.ERRORS.TEMPLATE_VALIDATION_ERROR.format(
                error=str(e)
            )
        except Exception as e:
            return False, CONSTANTS.ERRORS.ERROR_VALIDATING_TEMPLATE.format(
                error=str(e)
            )

    def validate_template_content(self, template_content: str) -> Tuple[bool, str]:
        """Validate template content string.

        Args:
            template_content: Template content as string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse template to check for syntax errors
            self._environment.parse(template_content)
            return True, ""

        except TemplateSyntaxError as e:
            return False, CONSTANTS.ERRORS.TEMPLATE_VALIDATION_ERROR.format(
                error=str(e)
            )
        except Exception as e:
            return False, CONSTANTS.ERRORS.ERROR_VALIDATING_TEMPLATE.format(
                error=str(e)
            )

    def get_template_variables(self, template_path: Path) -> List[str]:
        """Extract variables used in template.

        Args:
            template_path: Path to template file

        Returns:
            List of variable names used in the template
        """
        try:
            if not template_path.exists():
                return []

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            return self.get_template_variables_from_content(template_content)

        except Exception as e:
            logger.error(f"Failed to extract variables from {template_path}: {e}")
            return []

    def get_template_variables_from_content(self, template_content: str) -> List[str]:
        """Extract variables from template content.

        Args:
            template_content: Template content as string

        Returns:
            List of variable names used in the template
        """
        try:
            # Parse the template and find undeclared variables
            ast = self._environment.parse(template_content)
            undeclared_vars = find_undeclared_variables(ast)
            return sorted(undeclared_vars)

        except Exception as e:
            logger.error(f"Failed to extract variables from template content: {e}")
            return []

    def analyze_template_complexity(self, template_path: Path) -> dict:
        """Analyze template complexity and structure.

        Args:
            template_path: Path to template file

        Returns:
            Dictionary with complexity metrics
        """
        try:
            if not template_path.exists():
                return {"error": "Template file not found"}

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            return self.analyze_template_complexity_from_content(template_content)

        except Exception as e:
            logger.error(f"Failed to analyze template complexity: {e}")
            return {"error": str(e)}

    def analyze_template_complexity_from_content(self, template_content: str) -> dict:
        """Analyze template complexity from content.

        Args:
            template_content: Template content as string

        Returns:
            Dictionary with complexity metrics
        """
        try:
            # Parse the template
            ast = self._environment.parse(template_content)

            # Basic metrics
            metrics = {
                "line_count": len(template_content.splitlines()),
                "character_count": len(template_content),
                "variable_count": len(find_undeclared_variables(ast)),
                "variables": sorted(find_undeclared_variables(ast)),
            }

            # Count template constructs
            metrics.update(self._count_template_constructs(template_content))

            return metrics

        except Exception as e:
            logger.error(f"Failed to analyze template complexity: {e}")
            return {"error": str(e)}

    def validate_multiple_templates(
        self, template_paths: List[Path]
    ) -> List[Tuple[Path, bool, str]]:
        """Validate multiple templates.

        Args:
            template_paths: List of template file paths

        Returns:
            List of (path, is_valid, error_message) tuples
        """
        results = []
        for template_path in template_paths:
            is_valid, error_msg = self.validate_template_syntax(template_path)
            results.append((template_path, is_valid, error_msg))
        return results

    def _count_template_constructs(self, template_content: str) -> dict:
        """Count various template constructs for complexity analysis.

        Args:
            template_content: Template content to analyze

        Returns:
            Dictionary with construct counts
        """
        import re

        counts = {
            "if_blocks": len(re.findall(r"{%\s*if\s+", template_content)),
            "for_loops": len(re.findall(r"{%\s*for\s+", template_content)),
            "variables": len(re.findall(r"{{\s*\w+", template_content)),
            "filters": len(re.findall(r"\|\s*\w+", template_content)),
            "includes": len(re.findall(r"{%\s*include\s+", template_content)),
            "extends": len(re.findall(r"{%\s*extends\s+", template_content)),
            "blocks": len(re.findall(r"{%\s*block\s+", template_content)),
            "macros": len(re.findall(r"{%\s*macro\s+", template_content)),
        }

        return counts

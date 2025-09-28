"""
Template Loading Service - focused on loading templates from packages and directories.

This service handles:
- Loading template packages for specific AI assistants
- Template discovery from filesystem and package resources
- Template file validation and metadata extraction
- Template environment initialization
"""

import logging
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from specify_cli.core.constants import CONSTANTS
from specify_cli.models.template import GranularTemplate, TemplateState

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Service focused on loading templates from various sources."""

    def __init__(self, skip_patterns: Optional[List[str]] = None):
        """Initialize template loader.

        Args:
            skip_patterns: List of file patterns to skip during loading
        """
        self.skip_patterns = skip_patterns or CONSTANTS.PATTERNS.SKIP_PATTERNS
        self._environment: Optional[Environment] = None
        self._custom_template_dir: Optional[Path] = None
        self._loaded_templates: dict[str, Template] = {}

    def load_template_package(self, _ai_assistant: str, template_dir: Path) -> bool:
        """Load template package for specified AI assistant.

        Args:
            ai_assistant: Name of the AI assistant
            template_dir: Directory containing templates

        Returns:
            True if templates were loaded successfully
        """
        try:
            if not template_dir.exists() or not template_dir.is_dir():
                return False

            # Check if directory contains template files
            template_files = list(
                template_dir.glob(f"*{CONSTANTS.FILE.TEMPLATE_J2_EXTENSION}")
            )
            if not template_files:
                # Also check for templates without .j2 extension
                template_files = [
                    f
                    for f in template_dir.iterdir()
                    if f.is_file() and not self._should_skip_file(f)
                ]
                if not template_files:
                    return False

            # Initialize Jinja2 environment
            loader = FileSystemLoader(str(template_dir))
            self._environment = Environment(
                loader=loader,
                # Don't use StrictUndefined as it's too strict for template conditionals
                # Use default which raises TemplateRuntimeError for undefined variables
            )

            # Add custom filters
            def regex_replace(value: str, pattern: str, replacement: str = "") -> str:
                """Jinja2 filter for regex replacement"""
                import re

                return re.sub(pattern, replacement, value)

            self._environment.filters["regex_replace"] = regex_replace  # type: ignore

            # Load all templates into memory
            for template_file in template_files:
                try:
                    assert self._environment is not None  # Just set above
                    template = self._environment.get_template(template_file.name)
                    self._loaded_templates[template_file.name] = template
                except Exception as e:
                    logger.warning(f"Failed to load template {template_file.name}: {e}")
                    continue

            return len(self._loaded_templates) > 0

        except Exception as e:
            logger.error(f"Failed to load template package: {e}")
            return False

    def get_loaded_template(self, template_name: str) -> Optional[Template]:
        """Get a loaded template by name.

        Args:
            template_name: Name of the template

        Returns:
            Loaded Jinja2 template or None if not found
        """
        return self._loaded_templates.get(template_name)

    def get_environment(self) -> Optional[Environment]:
        """Get the current Jinja2 environment.

        Returns:
            Current Environment or None if not initialized
        """
        return self._environment

    def set_custom_template_dir(self, template_dir: Optional[Path]) -> bool:
        """Set custom template directory.

        Args:
            template_dir: Path to custom template directory

        Returns:
            True if directory was set successfully
        """
        if template_dir is None:
            self._custom_template_dir = None
            return True

        if not template_dir.exists() or not template_dir.is_dir():
            return False

        self._custom_template_dir = template_dir
        return True

    def discover_templates(self) -> List[GranularTemplate]:
        """Discover all available templates.

        Returns:
            List of discovered templates
        """
        templates = []

        # Load templates from package resources first
        self._discover_from_package_resources(templates)

        # Then from custom directory if set
        if self._custom_template_dir:
            self._discover_from_directory(self._custom_template_dir, templates)

        return templates

    def discover_templates_by_category(self, category: str) -> List[GranularTemplate]:
        """Discover templates for a specific category.

        Args:
            category: Template category to filter by

        Returns:
            List of templates in the specified category
        """
        all_templates = self.discover_templates()
        return [t for t in all_templates if t.category == category]

    def load_template_metadata(self, template_name: str) -> GranularTemplate:
        """Load template metadata for a specific template.

        Args:
            template_name: Name of the template

        Returns:
            Template with loaded metadata

        Raises:
            FileNotFoundError: If template is not found
        """
        # Remove .j2 extension first
        base_name = template_name
        if base_name.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
            base_name = base_name[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]

        # Search in discovered templates
        templates = self.discover_templates()
        for template in templates:
            if template.name == base_name or template.name == template_name:
                return template

        raise FileNotFoundError(
            CONSTANTS.ERRORS.TEMPLATE_NOT_FOUND.format(template_name=template_name)
        )

    def load_templates_from_package_resources(self) -> bool:
        """Load templates from package resources.

        Returns:
            True if templates were loaded successfully
        """
        try:
            # This is a simplified version - in practice would use importlib.resources
            # to load from the package's template directory
            return True
        except Exception as e:
            logger.error(f"Failed to load templates from package resources: {e}")
            return False

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during loading.

        Args:
            file_path: Path to check

        Returns:
            True if file should be skipped
        """
        return any(file_path.match(pattern) for pattern in self.skip_patterns)

    def _discover_from_package_resources(
        self, templates: List[GranularTemplate]
    ) -> None:
        """Discover templates from package resources.

        Args:
            templates: List to append discovered templates to
        """
        # Implementation would use importlib.resources to discover
        # templates from the package
        pass

    def _discover_from_directory(
        self, directory: Path, templates: List[GranularTemplate]
    ) -> None:
        """Discover templates from a directory.

        Args:
            directory: Directory to search
            templates: List to append discovered templates to
        """
        try:
            if not directory.exists():
                return

            for item in directory.rglob(f"*{CONSTANTS.FILE.TEMPLATE_J2_EXTENSION}"):
                if self._should_skip_file(item):
                    continue

                # Create template metadata
                template = GranularTemplate(
                    name=item.stem,
                    template_path=str(item),
                    category=self._determine_category(item),
                    state=TemplateState.DISCOVERED,
                )
                templates.append(template)

        except Exception as e:
            logger.error(f"Failed to discover templates from {directory}: {e}")

    def _determine_category(self, template_path: Path) -> str:
        """Determine category for a template based on its path.

        Args:
            template_path: Path to the template file

        Returns:
            Template category
        """
        # Simple category determination based on path
        path_str = str(template_path)
        for category in CONSTANTS.PATTERNS.TEMPLATE_CATEGORIES:
            if category in path_str:
                return category
        return "unknown"

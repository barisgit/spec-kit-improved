"""
Template Service Interfaces - Abstract base classes for template operations.

This module defines the core interfaces and contracts for template services,
ensuring consistent behavior across different implementations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional, Tuple

from specify_cli.models.project import TemplateContext, TemplateFile
from specify_cli.models.template import GranularTemplate, TemplatePackage

from .models import TemplateDiff, TemplateRenderResult


class TemplateService(ABC):
    """Abstract base class for template processing services"""

    @abstractmethod
    def load_template_package(self, ai_assistant: str, template_dir: Path) -> bool:
        """
        Load template package for specified AI assistant

        Args:
            ai_assistant: Name of the AI assistant (e.g., "claude", "gpt")
            template_dir: Path to directory containing templates

        Returns:
            True if templates loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def render_template(
        self, template_name: str, context: Optional[TemplateContext]
    ) -> str:
        """
        Render a specific template with given context

        Args:
            template_name: Name of template file to render
            context: Template context with variables

        Returns:
            Rendered template content as string

        Raises:
            Exception: If template not found or rendering fails
        """
        pass

    @abstractmethod
    def render_project_templates(
        self, context: TemplateContext, output_dir: Path
    ) -> List[TemplateFile]:
        """
        Render all templates in the loaded package

        Args:
            context: Template context with variables
            output_dir: Directory where rendered files should be created

        Returns:
            List of TemplateFile objects with rendered content
        """
        pass

    @abstractmethod
    def validate_template_syntax(
        self, template_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate template syntax

        Args:
            template_path: Path to template file

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_template_variables(self, template_path: Path) -> List[str]:
        """
        Extract variables used in template

        Args:
            template_path: Path to template file

        Returns:
            List of variable names used in template
        """
        pass

    @abstractmethod
    def set_custom_template_dir(self, template_dir: Optional[Path]) -> bool:
        """
        Set custom template directory

        Args:
            template_dir: Path to custom template directory, or None to reset

        Returns:
            True if set successfully, False otherwise
        """
        pass

    @abstractmethod
    def discover_templates(self) -> List[GranularTemplate]:
        """
        Discover templates from package resources

        Returns:
            List of discovered GranularTemplate objects
        """
        pass

    @abstractmethod
    def discover_templates_by_category(self, category: str) -> List[GranularTemplate]:
        """
        Filter templates by category

        Args:
            category: Template category to filter by

        Returns:
            List of GranularTemplate objects in the category
        """
        pass

    @abstractmethod
    def load_template(self, template_name: str) -> GranularTemplate:
        """
        Load individual template object

        Args:
            template_name: Name of template to load

        Returns:
            GranularTemplate object with loaded Jinja2 template

        Raises:
            Exception: If template not found or loading fails
        """
        pass

    @abstractmethod
    def load_templates_from_package_resources(self) -> bool:
        """
        Load templates from package resources

        Returns:
            True if templates loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def validate_template_package(self, package: TemplatePackage) -> bool:
        """
        Validate template package

        Args:
            package: TemplatePackage to validate

        Returns:
            True if package is valid, False otherwise
        """
        pass

    @abstractmethod
    def render_template_package(
        self, package: TemplatePackage, context: TemplateContext
    ) -> List["TemplateRenderResult"]:
        """
        Render full template package

        Args:
            package: TemplatePackage to render
            context: Template context for rendering

        Returns:
            List of TemplateRenderResult objects
        """
        pass

    @abstractmethod
    def render_with_platform_context(
        self, template: GranularTemplate, context: TemplateContext
    ) -> str:
        """
        Render template with platform-specific context variables

        Args:
            template: GranularTemplate to render
            context: Base template context

        Returns:
            Rendered template content as string
        """
        pass

    @abstractmethod
    def enhance_context_with_platform_info(
        self, context: TemplateContext, platform_name: str
    ) -> TemplateContext:
        """Enhance template context with platform-specific information"""
        pass

    @abstractmethod
    def compare_templates(
        self,
        project_path: Path,
        new_template_dir: Optional[Path] = None,
        selected_agents: Optional[List[str]] = None,
    ) -> TemplateDiff:
        """Compare current project files with templates from a source.

        Args:
            project_path: Path to the current project
            new_template_dir: New template directory to compare against (None for built-in)

        Returns:
            TemplateDiff object with all changes
        """
        pass


class TemplateLoaderInterface(ABC):
    """Interface for template loading operations."""

    @abstractmethod
    def load_template_package(self, ai_assistant: str, template_dir: Path) -> bool:
        """Load template package for specified AI assistant."""
        pass

    @abstractmethod
    def discover_templates(self) -> List[GranularTemplate]:
        """Discover all available templates."""
        pass

    @abstractmethod
    def load_template_metadata(self, template_name: str) -> GranularTemplate:
        """Load template metadata for a specific template."""
        pass


class TemplateRendererInterface(ABC):
    """Interface for template rendering operations."""

    @abstractmethod
    def render_template(
        self, template: Any, context: TemplateContext, template_name: str = ""
    ) -> TemplateRenderResult:
        """Render a specific template with given context."""
        pass

    @abstractmethod
    def render_multiple_templates(
        self, templates: List[Tuple[Any, str]], context: TemplateContext
    ) -> List[TemplateRenderResult]:
        """Render multiple templates with the same context."""
        pass


class TemplateValidatorInterface(ABC):
    """Interface for template validation operations."""

    @abstractmethod
    def validate_template_syntax(self, template_path: Path) -> Tuple[bool, str]:
        """Validate template syntax."""
        pass

    @abstractmethod
    def get_template_variables(self, template_path: Path) -> List[str]:
        """Extract variables used in template."""
        pass


class TemplateComparatorInterface(ABC):
    """Interface for template comparison operations."""

    @abstractmethod
    def compare_template_sets(
        self,
        old_templates: dict[str, str],
        new_templates: dict[str, str],
        categories: Optional[dict[str, str]] = None,
    ) -> TemplateDiff:
        """Compare two sets of templates."""
        pass

    @abstractmethod
    def generate_change_summary(self, diff: TemplateDiff) -> str:
        """Generate a human-readable summary of changes."""
        pass

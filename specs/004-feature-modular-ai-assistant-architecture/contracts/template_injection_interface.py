"""
Type-safe contracts for template injection system.

This module defines interfaces for the template injection system that
replaces conditional logic with clean, assistant-agnostic injection points.
"""

from typing import Any, Dict, List, Protocol

from .assistant_config_interface import AssistantName, InjectionPoints


class TemplateContext(Protocol):
    """
    Protocol for enhanced template context with assistant injections.

    Provides type-safe context that includes both standard template
    variables and assistant-specific injection points.
    """

    @property
    def project_name(self) -> str:
        """Project name for template rendering."""
        ...

    @property
    def ai_assistant(self) -> AssistantName:
        """Selected AI assistant name."""
        ...

    @property
    def assistant_injections(self) -> InjectionPoints:
        """Assistant-specific injection point values."""
        ...

    @property
    def standard_context(self) -> Dict[str, Any]:
        """Standard template variables."""
        ...

    def merge_context(self) -> Dict[str, Any]:
        """
        Merge all context variables for template rendering.

        Returns:
            Complete context dictionary for Jinja2 rendering
        """
        ...


class InjectionPointResolver(Protocol):
    """
    Protocol for resolving injection points to their values.

    Handles the mapping between injection point names and their
    assistant-specific implementations.
    """

    def resolve_injection(
        self,
        assistant_name: AssistantName,
        injection_point: str
    ) -> str:
        """
        Resolve injection point to its value for given assistant.

        Args:
            assistant_name: Name of the assistant
            injection_point: Name of the injection point

        Returns:
            Resolved value for the injection point
        """
        ...

    def resolve_all_injections(
        self,
        assistant_name: AssistantName
    ) -> InjectionPoints:
        """
        Resolve all injection points for given assistant.

        Args:
            assistant_name: Name of the assistant

        Returns:
            Dictionary of all injection points and their values
        """
        ...

    def validate_injection_point(self, injection_point: str) -> bool:
        """
        Validate that injection point name is valid.

        Args:
            injection_point: Name to validate

        Returns:
            True if valid injection point name
        """
        ...


class TemplateRenderer(Protocol):
    """
    Protocol for rendering templates with injection points.

    Enhanced template renderer that processes injection points
    alongside standard Jinja2 template variables.
    """

    def render_with_injections(
        self,
        template_content: str,
        context: TemplateContext
    ) -> str:
        """
        Render template with injection points and standard context.

        Args:
            template_content: Jinja2 template content
            context: Enhanced template context with injections

        Returns:
            Rendered template content
        """
        ...

    def validate_template_syntax(self, template_content: str) -> List[str]:
        """
        Validate template syntax including injection points.

        Args:
            template_content: Template content to validate

        Returns:
            List of syntax errors (empty if valid)
        """
        ...

    def get_injection_points_used(self, template_content: str) -> List[str]:
        """
        Extract injection points used in template.

        Args:
            template_content: Template content to analyze

        Returns:
            List of injection point names used in template
        """
        ...


class ConditionalConverter(Protocol):
    """
    Protocol for converting template conditionals to injection points.

    Handles the migration from conditional logic to clean injection points.
    """

    def find_conditional_blocks(self, template_content: str) -> List[Dict[str, Any]]:
        """
        Find conditional blocks that can be converted to injection points.

        Args:
            template_content: Template content to analyze

        Returns:
            List of conditional block metadata
        """
        ...

    def convert_conditional_to_injection(
        self,
        template_content: str,
        conditional_block: Dict[str, Any],
        injection_point_name: str
    ) -> str:
        """
        Convert specific conditional block to injection point.

        Args:
            template_content: Original template content
            conditional_block: Conditional block to convert
            injection_point_name: Name for the injection point

        Returns:
            Updated template content with injection point
        """
        ...

    def suggest_injection_point_name(
        self,
        conditional_block: Dict[str, Any]
    ) -> str:
        """
        Suggest appropriate injection point name for conditional.

        Args:
            conditional_block: Conditional block metadata

        Returns:
            Suggested injection point name
        """
        ...


# Template processing types
ConditionalBlock = Dict[str, Any]
TemplateAnalysis = Dict[str, List[str]]
ConversionResult = tuple[str, List[str]]  # (converted_template, warnings)


class TemplateAnalyzer(Protocol):
    """
    Protocol for analyzing templates for injection point opportunities.

    Provides analysis capabilities to understand template structure
    and identify conversion opportunities.
    """

    def analyze_template(self, template_content: str) -> TemplateAnalysis:
        """
        Analyze template for conditional logic and injection opportunities.

        Args:
            template_content: Template content to analyze

        Returns:
            Analysis results including conditionals and variables used
        """
        ...

    def estimate_conversion_effort(self, template_content: str) -> Dict[str, int]:
        """
        Estimate effort required to convert template to injection points.

        Args:
            template_content: Template content to analyze

        Returns:
            Effort estimation with metrics
        """
        ...

    def generate_conversion_plan(self, template_content: str) -> List[Dict[str, Any]]:
        """
        Generate step-by-step conversion plan.

        Args:
            template_content: Template content to convert

        Returns:
            List of conversion steps with details
        """
        ...


# Injection point validation
class InjectionValidator(Protocol):
    """
    Protocol for validating injection point implementations.

    Ensures injection points are properly implemented and used.
    """

    def validate_injection_implementation(
        self,
        assistant_name: AssistantName,
        injection_points: InjectionPoints
    ) -> List[str]:
        """
        Validate injection point implementation for assistant.

        Args:
            assistant_name: Name of the assistant
            injection_points: Injection points to validate

        Returns:
            List of validation errors
        """
        ...

    def validate_template_injection_usage(
        self,
        template_content: str,
        available_injections: List[str]
    ) -> List[str]:
        """
        Validate injection point usage in template.

        Args:
            template_content: Template content to validate
            available_injections: Available injection point names

        Returns:
            List of validation errors
        """
        ...

    def check_injection_safety(self, injection_value: str) -> bool:
        """
        Check if injection value is safe for template rendering.

        Args:
            injection_value: Value to check for safety

        Returns:
            True if safe for template rendering
        """
        ...
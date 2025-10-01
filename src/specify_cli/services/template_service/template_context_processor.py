"""
Template Context Processor - handles template context preparation and enhancement.

This service handles:
- Context preparation for template rendering
- AI assistant injection point processing
- Memory imports integration
- Context attribute extraction and merging
- Platform-specific context enhancement
"""

import logging
from typing import Any, Dict

from specify_cli.models.project import TemplateContext
from specify_cli.utils.security import TemplateSanitizer, TemplateSecurityError

logger = logging.getLogger(__name__)


class TemplateContextProcessor:
    """Service focused on template context processing and preparation."""

    def __init__(self):
        """Initialize template context processor."""
        self._sanitizer = TemplateSanitizer()

    def prepare_context(self, context: TemplateContext) -> Dict[str, Any]:
        """Prepare context for template rendering.

        Args:
            context: Template context to prepare

        Returns:
            Dictionary of context variables ready for template rendering
        """
        # Primary path: Use structured dataclass approach via to_dict method
        if hasattr(context, "to_dict"):
            context_dict = context.to_dict()
        else:
            # Fallback path: Manual extraction for legacy test contexts
            context_dict = self.extract_context_attributes(context)

        # Add AI assistant injection points
        if hasattr(context, "ai_assistant") and context.ai_assistant:
            context_dict = self._add_assistant_injection_points(context_dict, context)

        # Add dynamic memory imports
        if (
            hasattr(context, "ai_assistant")
            and hasattr(context, "project_path")
            and context.project_path
        ):
            context_dict = self._add_memory_imports(context_dict, context)

        # Final security validation of the complete context
        try:
            context_dict = self._sanitizer.sanitize_context_dict(context_dict)
        except TemplateSecurityError as e:
            logger.warning(f"Context sanitization failed: {e}")
            # Remove potentially dangerous variables but continue
            context_dict = self._create_safe_fallback_context(context)

        return context_dict

    def extract_context_attributes(self, context: TemplateContext) -> Dict[str, Any]:
        """Fallback method to manually extract context attributes.

        Used only for test contexts that don't implement to_dict.
        In production, all contexts should use the structured dataclass approach.

        Args:
            context: Template context object

        Returns:
            Dictionary of extracted context attributes
        """
        context_dict = {}

        # Define standard fields in a maintainable way
        standard_fields = [
            "project_name",
            "ai_assistant",
            "feature_name",
            "branch_type",
            "author",
            "version",
            "branch_name",
            "task_name",
            "author_name",
            "author_email",
            "creation_date",
            "creation_year",
            "project_description",
        ]

        # Extract standard fields
        for attr in standard_fields:
            if hasattr(context, attr):
                context_dict[attr] = getattr(context, attr)

        # Handle special collections
        self.merge_collection_attributes(context, context_dict)

        return context_dict

    def merge_collection_attributes(
        self, context: TemplateContext, context_dict: Dict[str, Any]
    ) -> None:
        """Helper to merge collection attributes from context.

        Args:
            context: Source template context
            context_dict: Target dictionary to merge into
        """
        # Handle additional_vars
        if hasattr(context, "additional_vars") and isinstance(
            context.additional_vars, dict
        ):
            context_dict["additional_vars"] = context.additional_vars
            context_dict.update(context.additional_vars)

        # Handle template_variables
        if hasattr(context, "template_variables") and isinstance(
            context.template_variables, dict
        ):
            context_dict.update(context.template_variables)

        # Handle custom_fields
        if hasattr(context, "custom_fields") and isinstance(
            context.custom_fields, dict
        ):
            context_dict.update(context.custom_fields)

        # Handle date/creation_date variations for backward compatibility
        if "creation_date" in context_dict and "date" not in context_dict:
            context_dict["date"] = context_dict["creation_date"]

    def _add_assistant_injection_points(
        self, context_dict: Dict[str, Any], context: TemplateContext
    ) -> Dict[str, Any]:
        """Add AI assistant injection points to context.

        Args:
            context_dict: Current context dictionary
            context: Original template context

        Returns:
            Enhanced context dictionary with injection points
        """
        try:
            from specify_cli.assistants import get_assistant

            assistant = get_assistant(context.ai_assistant)
            if assistant:
                injection_values = assistant.get_injection_values()
                for injection_point, value in injection_values.items():
                    key_name = (
                        str(injection_point.name)
                        if hasattr(injection_point, "name")
                        else str(injection_point)
                    )
                    # Sanitize injection point values
                    try:
                        sanitized_value = self._sanitizer.sanitize_injection_value(
                            str(value)
                        )
                        context_dict[key_name] = sanitized_value
                    except TemplateSecurityError as e:
                        logger.warning(
                            f"Skipping dangerous injection point {key_name}: {e}"
                        )
                        # Skip this injection point rather than failing completely
                        continue
        except Exception as e:
            logger.debug(f"Failed to add assistant injection points: {e}")

        return context_dict

    def _add_memory_imports(
        self, context_dict: Dict[str, Any], context: TemplateContext
    ) -> Dict[str, Any]:
        """Add dynamic memory imports to context.

        Args:
            context_dict: Current context dictionary
            context: Original template context

        Returns:
            Enhanced context dictionary with memory imports
        """
        try:
            from specify_cli.assistants import get_assistant
            from specify_cli.services.memory_service import MemoryManager

            assert context.project_path is not None
            memory_manager = MemoryManager(context.project_path)
            assistant = get_assistant(context.ai_assistant)

            if assistant and assistant.config:
                # Determine context file directory
                context_file_path = (
                    context.project_path / assistant.config.context_file.file
                )
                context_file_dir = context_file_path.parent

                # Generate memory imports section
                memory_imports = memory_manager.generate_import_section(
                    context.ai_assistant, context_file_dir
                )

                if memory_imports:
                    # Sanitize memory imports content
                    try:
                        sanitized_imports = self._sanitizer.sanitize_injection_value(
                            memory_imports
                        )
                        context_dict["assistant_memory_imports"] = sanitized_imports
                    except TemplateSecurityError as e:
                        logger.warning(f"Memory imports contain dangerous content: {e}")
                        # Provide safe fallback
                        context_dict["assistant_memory_imports"] = (
                            "# Memory imports disabled due to security validation"
                        )
        except Exception as e:
            logger.debug(f"Failed to add memory imports: {e}")

        return context_dict

    def enhance_context_with_platform_info(
        self, context_dict: Dict[str, Any], platform_name: str
    ) -> Dict[str, Any]:
        """Enhance context with platform-specific information.

        Args:
            context_dict: Base context dictionary
            platform_name: Name of the target platform

        Returns:
            Enhanced context dictionary with platform information
        """
        # Add platform-specific information to the context
        context_dict["platform_name"] = platform_name

        # Add additional platform-specific variables as needed
        if platform_name == "windows":
            context_dict.update(
                {
                    "path_separator": "\\",
                    "line_ending": "\\r\\n",
                    "script_extension": ".bat",
                }
            )
        else:
            context_dict.update(
                {
                    "path_separator": "/",
                    "line_ending": "\\n",
                    "script_extension": ".sh",
                }
            )

        return context_dict

    def _create_safe_fallback_context(self, context: TemplateContext) -> Dict[str, Any]:
        """Create a safe fallback context when sanitization fails.

        Args:
            context: Original template context

        Returns:
            Safe minimal context dictionary
        """
        safe_context = {
            "project_name": getattr(context, "project_name", "unknown"),
            "ai_assistant": getattr(context, "ai_assistant", "unknown"),
            "creation_date": getattr(context, "creation_date", "unknown"),
            "author": getattr(context, "author", "unknown"),
            "security_warning": "Template context was sanitized due to security validation",
        }

        # Only include safe string values
        for key, value in safe_context.items():
            if isinstance(value, str) and len(value) <= 100:
                try:
                    safe_context[key] = self._sanitizer.sanitize_injection_value(value)
                except TemplateSecurityError:
                    safe_context[key] = "sanitized"

        return safe_context

"""
Template service for rendering Jinja2 templates in spec-kit

This module provides an interface and implementation for template processing,
supporting Jinja2 template rendering with context variables.
"""

import importlib.resources
import logging
import platform
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union, cast

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    TemplateSyntaxError,
)
from jinja2.meta import find_undeclared_variables
from rich.console import Console

from specify_cli.assistants import get_assistant
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.defaults import PATH_DEFAULTS
from specify_cli.models.defaults.path_defaults import (
    EXECUTABLE_PERMISSIONS,
    TEMPLATE_EXTENSION,
)
from specify_cli.models.project import TemplateContext, TemplateFile
from specify_cli.models.template import (
    GranularTemplate,
    TemplatePackage,
    TemplateState,
)


@dataclass(frozen=True)
class TemplateFolderMapping:
    """Type-safe template folder configuration"""

    source: str  # Source folder in templates/
    target_pattern: str  # Target pattern, supports {ai_assistant}, {project_name}
    render: bool  # Whether to render .j2 files or copy as-is
    executable_extensions: List[str]  # File extensions to make executable


@dataclass
class RenderResult:
    """Type-safe render operation result"""

    rendered_files: List[Path] = field(default_factory=list)
    copied_files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_files(self) -> int:
        return len(self.rendered_files) + len(self.copied_files)


class TemplateChangeType(Enum):
    """Types of template changes."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class TemplateChange:
    """Represents a change to a template."""

    template_name: str
    change_type: TemplateChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    category: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    should_skip: bool = False  # Whether this file should be skipped during updates


@dataclass
class TemplateDiff:
    """Result of comparing template sets."""

    changes: List[TemplateChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(
            change.change_type != TemplateChangeType.UNCHANGED
            for change in self.changes
        )

    @property
    def added_count(self) -> int:
        return len(
            [c for c in self.changes if c.change_type == TemplateChangeType.ADDED]
        )

    @property
    def modified_count(self) -> int:
        return len(
            [c for c in self.changes if c.change_type == TemplateChangeType.MODIFIED]
        )

    @property
    def deleted_count(self) -> int:
        return len(
            [c for c in self.changes if c.change_type == TemplateChangeType.DELETED]
        )


@dataclass
class TemplateRenderResult:
    """Result of rendering a single template"""

    template: GranularTemplate
    content: str
    success: bool = True
    error_message: Optional[str] = None


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
        self, project_path: Path, new_template_dir: Optional[Path] = None
    ) -> TemplateDiff:
        """Compare current project files with templates from a source.

        Args:
            project_path: Path to the current project
            new_template_dir: New template directory to compare against (None for built-in)

        Returns:
            TemplateDiff object with all changes
        """
        pass


class JinjaTemplateService(TemplateService):
    """Jinja2-based template service implementation"""

    def __init__(self, skip_patterns: Optional[List[str]] = None):
        self._template_dir: Optional[Path] = None
        self._custom_template_dir: Optional[Path] = None
        self._ai_assistant: Optional[str] = None
        self._environment: Optional[Environment] = None
        self._discovered_templates: List[GranularTemplate] = []
        self._use_filesystem: bool = False  # Flag for filesystem vs importlib access
        self._filesystem_root: Optional[Path] = None  # Store filesystem root separately

        # Use configurable skip patterns from PATH_DEFAULTS
        self.skip_patterns = skip_patterns or PATH_DEFAULTS.SKIP_PATTERNS

        # Get template root from package resources using Traversable API
        self._template_root = importlib.resources.files("specify_cli").joinpath(
            PATH_DEFAULTS.TEMPLATE_ROOT
        )
        self._console = Console()

    def load_template_package(self, ai_assistant: str, template_dir: Path) -> bool:
        """Load template package for specified AI assistant"""
        try:
            if not template_dir.exists() or not template_dir.is_dir():
                return False

            # Check if directory contains template files
            template_files = list(template_dir.glob(f"*{TEMPLATE_EXTENSION}"))
            if not template_files:
                # Also check for templates without .j2 extension
                template_files = [
                    f
                    for f in template_dir.iterdir()
                    if f.is_file() and not f.name.startswith(".")
                ]

            self._template_dir = template_dir
            self._ai_assistant = ai_assistant
            self._environment = Environment(
                loader=FileSystemLoader(str(template_dir)),
                keep_trailing_newline=True,
                # Don't use StrictUndefined as it's too strict for template conditionals
            )

            # Add custom filters (register as a plain callable for typing compatibility)
            def regex_replace(value: str, pattern: str, replacement: str = "") -> str:
                return self._regex_replace_filter(value, pattern, replacement)

            self._environment.filters["regex_replace"] = cast(
                Callable[..., Any], regex_replace
            )

            return True

        except Exception:
            return False

    def render_template(
        self,
        template_name: Union[str, GranularTemplate],
        context: Optional[TemplateContext],
    ) -> str:
        """Render a specific template with given context"""
        # Validate inputs
        if context is None:
            raise ValueError("Template context cannot be None")

        if not template_name:
            raise ValueError("Template name cannot be empty")

        try:
            # Handle GranularTemplate objects
            if isinstance(template_name, GranularTemplate):
                if not template_name.loaded_template:
                    # Load the template if not already loaded
                    template_name = self.load_template(template_name.name)
                return self.render_with_platform_context(template_name, context)

            # Handle string template names
            if self._environment is None:
                # Try to load from package resources if no environment set
                success = self.load_templates_from_package_resources()
                if not success:
                    raise RuntimeError("Failed to load template environment")

            # Try to load as GranularTemplate first
            try:
                granular_template = self.load_template(template_name)
                return self.render_with_platform_context(granular_template, context)
            except Exception as e:
                # Fall back to original method if available
                if self._environment is not None:
                    try:
                        template = self._environment.get_template(template_name)
                        context_dict = self._prepare_context(context)
                        return template.render(**context_dict)
                    except TemplateNotFound as te:
                        raise FileNotFoundError(
                            f"Template not found: {template_name}"
                        ) from te
                    except TemplateSyntaxError as tse:
                        raise RuntimeError(
                            f"Template syntax error in '{template_name}': {str(tse)}"
                        ) from tse
                    except Exception as re:
                        raise RuntimeError(
                            f"Failed to render template '{template_name}': {str(re)}"
                        ) from re
                else:
                    raise FileNotFoundError(
                        f"Template not found: {template_name}"
                    ) from e

        except (ValueError, FileNotFoundError, RuntimeError):
            # Re-raise these specific exceptions as-is
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise RuntimeError(
                f"Unexpected error rendering template '{template_name}': {str(e)}"
            ) from e

    def render_project_templates(
        self, context: TemplateContext, output_dir: Path
    ) -> List[TemplateFile]:
        """Render all templates in the loaded package"""
        if self._template_dir is None:
            return []

        template_files = []
        context_dict = self._prepare_context(context)

        # Find all template files
        for template_path in self._template_dir.iterdir():
            if not template_path.is_file() or template_path.name.startswith("."):
                continue

            try:
                # Determine output filename (remove .j2 extension if present)
                output_filename = template_path.name
                if output_filename.endswith(TEMPLATE_EXTENSION):
                    output_filename = output_filename[: -len(TEMPLATE_EXTENSION)]

                output_path = str(output_dir / output_filename)

                # Render template
                if self._environment:
                    template = self._environment.get_template(template_path.name)
                    content = template.render(**context_dict)
                else:
                    # Fallback for direct file reading
                    with open(template_path, "r", encoding="utf-8") as f:
                        content = f.read()

                # Determine if executable (simple heuristic)
                is_executable = self._is_executable_template(template_path, content)

                template_file = TemplateFile(
                    template_path=template_path,
                    output_path=output_path,
                    content=content,
                    is_executable=is_executable,
                )
                template_files.append(template_file)

            except Exception:
                # Skip problematic templates but continue processing others
                continue

        return template_files

    def validate_template_syntax(
        self, template_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """Validate template syntax"""
        try:
            if not template_path.exists():
                return False, f"Template file not found: {template_path}"

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Try to parse and compile template to catch more errors
            env = Environment()
            ast = env.parse(template_content)
            env.compile(ast)
            return True, None

        except TemplateSyntaxError as e:
            return False, f"Template syntax error: {str(e)}"
        except Exception as e:
            return False, f"Error validating template: {str(e)}"

    def get_template_variables(self, template_path: Path) -> List[str]:
        """Extract variables used in template"""
        try:
            if not template_path.exists():
                return []

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            env = Environment()
            ast = env.parse(template_content)
            variables = find_undeclared_variables(ast)
            return sorted(variables)

        except Exception:
            return []

    def set_custom_template_dir(self, template_dir: Optional[Path]) -> bool:
        """Set custom template directory"""
        try:
            if template_dir is None:
                self._custom_template_dir = None
                return True

            if not template_dir.exists() or not template_dir.is_dir():
                return False

            self._custom_template_dir = template_dir
            return True

        except Exception:
            return False

    def _prepare_context(self, context: TemplateContext) -> dict:
        """
        Prepare context for template rendering

        Uses the structured dataclass approach via to_dict() method.
        Maintains a fallback for test compatibility.
        Adds AI assistant injection points for enhanced template content.
        """
        # Primary path: Use structured dataclass approach via to_dict method
        if hasattr(context, "to_dict"):
            context_dict = context.to_dict()
        else:
            # Fallback path: Manual extraction for legacy test contexts
            # This should be rarely used as all proper TemplateContext objects have to_dict
            context_dict = self._extract_context_attributes(context)

        # Add AI assistant injection points
        if hasattr(context, "ai_assistant") and context.ai_assistant:
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
                    context_dict[key_name] = value

        # Add dynamic memory imports
        if (
            hasattr(context, "ai_assistant")
            and hasattr(context, "project_path")
            and context.project_path
        ):
            from specify_cli.assistants import get_assistant
            from specify_cli.services.memory_service import MemoryManager

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
                    context_dict["assistant_memory_imports"] = memory_imports

        return context_dict

    def _extract_context_attributes(self, context: TemplateContext) -> dict:
        """
        Fallback method to manually extract context attributes.

        Used only for test contexts that don't implement to_dict.
        In production, all contexts should use the structured dataclass approach.
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
        self._merge_collection_attributes(context, context_dict)

        return context_dict

    def _merge_collection_attributes(
        self, context: TemplateContext, context_dict: dict
    ) -> None:
        """Helper to merge collection attributes from context."""
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

    def _regex_replace_filter(
        self, value: str, pattern: str, replacement: str = ""
    ) -> str:
        """Jinja2 filter for regex replacement"""
        try:
            return re.sub(pattern, replacement, str(value))
        except Exception:
            return str(value)  # Return original if regex fails

    def _is_executable_template(self, template_path: Path, content: str) -> bool:
        """Determine if template should produce an executable file"""
        # Use configurable executable extensions from PATH_DEFAULTS
        # Check file extension patterns
        executable_extensions = set(PATH_DEFAULTS.EXECUTABLE_EXTENSIONS)

        # Remove .j2 extension if present for checking
        check_name = template_path.name
        if check_name.endswith(TEMPLATE_EXTENSION):
            check_name = check_name[: -len(TEMPLATE_EXTENSION)]

        check_path = Path(check_name)
        if check_path.suffix in executable_extensions:
            return True

        # Check for shebang in content
        if content.startswith("#!"):
            return True

        # Check for specific executable patterns in filename using PATH_DEFAULTS
        return any(
            pattern in check_name.lower()
            for pattern in PATH_DEFAULTS.EXECUTABLE_NAME_PATTERNS
        )

    def discover_templates(self) -> List[GranularTemplate]:
        """Discover templates from package resources"""
        if self._discovered_templates:
            logging.debug(
                f"Using cached templates: {len(self._discovered_templates)} templates"
            )
            return self._discovered_templates

        logging.debug("Starting template discovery from package resources")
        templates = []
        try:
            # Get reference to the templates package
            import specify_cli.templates as templates_pkg

            # Use configurable template categories from PATH_DEFAULTS
            # Discover templates in each category directory
            categories = PATH_DEFAULTS.TEMPLATE_CATEGORIES
            logging.debug(f"Scanning categories: {categories}")

            for category in categories:
                try:
                    # Get files in this category directory
                    category_files = importlib.resources.files(templates_pkg) / category
                    if category_files.is_dir():
                        for file_path in category_files.iterdir():
                            if file_path.is_file() and file_path.name.endswith(
                                TEMPLATE_EXTENSION
                            ):
                                # Simple mapping: filename.ext.j2 → filename.ext
                                # For "create-feature.py.j2" -> "create-feature.py"
                                # For "create-feature.j2" -> "create-feature"
                                filename_without_j2 = file_path.name[
                                    : -len(TEMPLATE_EXTENSION)
                                ]  # Remove .j2
                                template_name = filename_without_j2

                                # Determine if executable (scripts only)
                                executable = category == "scripts"

                                # All command, memory, and context templates are AI-aware
                                ai_aware = category in ["commands", "memory", "context"]

                                template = GranularTemplate(
                                    name=template_name,
                                    template_path=f"{category}/{file_path.name}",
                                    category=category,
                                    ai_aware=ai_aware,
                                    executable=executable,
                                    state=TemplateState.DISCOVERED,
                                )

                                templates.append(template)

                except Exception:
                    # Skip problematic categories but continue with others
                    continue

            self._discovered_templates = templates
            return templates

        except Exception:
            return []

    def _get_ai_folder_mapping(self, ai_assistant: str) -> str:
        """Get AI-specific folder structure"""
        # Use the assistant registry to get proper directory structure
        assistant = get_assistant(ai_assistant)
        if assistant:
            return assistant.config.command_files.directory
        # Fallback for unknown assistants
        return f".{ai_assistant}/commands"

    def _get_ai_context_folder_mapping(self, ai_assistant: str) -> str:
        """Get AI-specific context file directory"""
        # Use the assistant registry to get proper context file directory
        assistant = get_assistant(ai_assistant)
        if assistant:
            # Extract the directory from the context file path
            context_file_path = Path(assistant.config.context_file.file)

            # If context file is in project root (like CLAUDE.md), return "."
            if context_file_path.name == context_file_path.as_posix():
                return "."
            else:
                return str(context_file_path.parent)
        # Fallback for unknown assistants
        return f".{ai_assistant}"

    def _determine_output_filename(
        self, template_name: str, ai_assistant: str, category: str
    ) -> str:
        """Determine output filename based on template, assistant, and category."""
        # Remove .j2 extension first
        base_name = template_name
        if base_name.endswith(TEMPLATE_EXTENSION):
            base_name = base_name[: -len(TEMPLATE_EXTENSION)]

        # Get assistant configuration
        assistant = get_assistant(ai_assistant)
        if not assistant:
            # Fallback: just return base name for unknown assistants
            return base_name

        # Special handling for context files - use assistant's actual context file name
        if base_name == "context-file" and category == "context":
            # Extract just the filename from the full context file path
            context_file_path = assistant.config.context_file.file
            return Path(context_file_path).name

        # For category-specific formatting
        if category == "commands":
            file_format = assistant.config.command_files.file_format.value
        elif category == "context":
            file_format = assistant.config.context_file.file_format.value
        else:
            # For other categories (scripts, memory, runtime_templates), preserve original extension
            return base_name

        # If base_name already has an extension, replace it with the assistant's format
        if "." in base_name:
            name_without_ext = base_name.rsplit(".", 1)[0]
            return f"{name_without_ext}.{file_format}"
        else:
            # No extension, add the assistant's format
            return f"{base_name}.{file_format}"

    def discover_templates_by_category(self, category: str) -> List[GranularTemplate]:
        """Filter templates by category"""
        all_templates = self.discover_templates()
        return [t for t in all_templates if t.category == category]

    def load_template(self, template_name: str) -> GranularTemplate:
        """Load individual template object"""
        # Find template by name (with or without .j2 extension)
        search_name = template_name.replace(TEMPLATE_EXTENSION, "")

        templates = self.discover_templates()
        template = next((t for t in templates if t.name == search_name), None)

        if not template:
            raise FileNotFoundError(f"Template not found: {template_name}")

        # Load the Jinja2 template if not already loaded
        if template.state == TemplateState.DISCOVERED:
            try:
                # Load from package resources
                import specify_cli.templates as templates_pkg

                template_content = (
                    importlib.resources.files(templates_pkg) / template.template_path
                ).read_text(encoding="utf-8")

                # Create Jinja2 template from content
                env = Environment(keep_trailing_newline=True)

                # Add custom filters
                def regex_replace(
                    value: str, pattern: str, replacement: str = ""
                ) -> str:
                    return self._regex_replace_filter(value, pattern, replacement)

                env.filters["regex_replace"] = cast(Callable[..., Any], regex_replace)

                jinja_template = env.from_string(template_content)
                template.transition_to_loaded(jinja_template)

            except Exception as e:
                template.mark_error(f"Failed to load template: {str(e)}")
                raise RuntimeError(
                    f"Failed to load template '{template_name}': {str(e)}"
                ) from e

        return template

    def load_templates_from_package_resources(self) -> bool:
        """Load templates from package resources"""
        try:
            templates = self.discover_templates()
            return len(templates) > 0
        except Exception:
            return False

    def validate_template_package(self, package: TemplatePackage) -> bool:
        """Validate template package"""
        try:
            # Check that all templates in package exist
            available_templates = {t.name for t in self.discover_templates()}

            for template in package.templates:
                if template.name not in available_templates:
                    return False

            # Check that templates are compatible with AI assistant
            for template in package.templates:
                if not template.is_ai_specific_for(package.ai_assistant):
                    return False

            return True

        except Exception:
            return False

    def render_template_package(
        self, package: TemplatePackage, context: TemplateContext
    ) -> List[TemplateRenderResult]:
        """Render full template package"""
        results = []

        # Get processing order (respecting dependencies)
        templates_to_process = package.get_processing_order()

        for template in templates_to_process:
            try:
                # Load template if needed
                loaded_template = self.load_template(template.name)

                # Render with platform context
                content = self.render_with_platform_context(loaded_template, context)

                # Mark as rendered
                loaded_template.transition_to_rendered(content)

                # Create result
                result = TemplateRenderResult(
                    template=loaded_template,
                    content=content,
                    success=True,
                )
                results.append(result)

            except Exception as e:
                # Create error result
                template.mark_error(str(e))
                result = TemplateRenderResult(
                    template=template,
                    content="",
                    success=False,
                    error_message=str(e),
                )
                results.append(result)

        return results

    def render_with_platform_context(
        self, template: GranularTemplate, context: TemplateContext
    ) -> str:
        """Render template with platform-specific context variables"""
        if not template:
            raise ValueError("Template cannot be None")

        if not template.loaded_template:
            raise RuntimeError(f"Template '{template.name}' not loaded")

        if not context:
            raise ValueError("Context cannot be None")

        try:
            # Prepare base context
            context_dict = self._prepare_context(context)

            # Add platform-specific variables
            try:
                context_dict.update(
                    {
                        "platform_system": platform.system(),
                        "platform_machine": platform.machine(),
                        "platform_python_version": platform.python_version(),
                        "is_windows": platform.system().lower() == "windows",
                        "is_macos": platform.system().lower() == "darwin",
                        "is_linux": platform.system().lower() == "linux",
                        "path_separator": "\\"
                        if platform.system().lower() == "windows"
                        else "/",
                        "script_extension": ".bat"
                        if platform.system().lower() == "windows"
                        else ".sh",
                    }
                )
            except Exception:
                # Continue with basic context if platform detection fails
                context_dict.update(
                    {
                        "platform_system": "unknown",
                        "is_windows": False,
                        "is_macos": False,
                        "is_linux": False,
                        "path_separator": "/",
                        "script_extension": ".sh",
                    }
                )

            # Add template-specific variables
            context_dict.update(
                {
                    "template_name": template.name,
                    "template_category": template.category,
                    "is_executable": template.executable,
                }
            )

            # Add AI assistant injection points
            if hasattr(context, "ai_assistant") and context.ai_assistant:
                assistant = get_assistant(context.ai_assistant)
                if assistant:
                    injection_values = assistant.get_injection_values()
                    # Add injection values with a prefix to avoid naming conflicts
                    for injection_point, value in injection_values.items():
                        # Convert enum to string and make it template-friendly
                        key_name = (
                            str(injection_point.name)
                            if hasattr(injection_point, "name")
                            else str(injection_point)
                        )
                        context_dict[key_name] = value

            # Add branch pattern context if available
            if (
                hasattr(context, "branch_naming_config")
                and context.branch_naming_config
            ):
                patterns = context.branch_naming_config.patterns
                if patterns:
                    # Handle both list and dict patterns
                    if isinstance(patterns, dict):
                        # Dict case: get first value
                        context_dict["branch_pattern"] = next(iter(patterns.values()))
                        context_dict["branch_patterns"] = patterns
                    else:
                        # List case: get first item
                        context_dict["branch_pattern"] = patterns[0]
                        context_dict["branch_patterns"] = patterns

            # Add date alias for creation_date to support templates that expect 'date'
            if "creation_date" in context_dict and "date" not in context_dict:
                context_dict["date"] = context_dict["creation_date"]

            # Render the template with enhanced error information
            try:
                return template.loaded_template.render(**context_dict)
            except TemplateSyntaxError as e:
                raise RuntimeError(
                    f"Template syntax error in '{template.name}': {str(e)}"
                ) from e
            except Exception as e:
                # Add context about what variables were available for debugging
                available_vars = sorted(context_dict.keys())
                raise RuntimeError(
                    f"Failed to render template '{template.name}': {str(e)}. "
                    f"Available variables: {', '.join(available_vars[:10])}{'...' if len(available_vars) > 10 else ''}"
                ) from e

        except (ValueError, RuntimeError):
            # Re-raise validation and template errors as-is
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise RuntimeError(
                f"Unexpected error rendering template '{template.name}': {str(e)}"
            ) from e

    def render_all_templates_from_mappings(
        self,
        folder_mappings: List[TemplateFolderMapping],
        context: TemplateContext,
        verbose: bool = False,
    ) -> RenderResult:
        """Render all templates based on dynamic folder mappings"""
        result = RenderResult()

        logging.debug(
            f"render_all_templates_from_mappings called with {len(folder_mappings)} mappings"
        )

        for i, mapping in enumerate(folder_mappings):
            try:
                logging.debug(f"Processing mapping {i}: source={mapping.source}")

                # Build target path with AI-specific logic for commands and context
                if mapping.source == "commands":
                    # Use centralized AI-specific folder structure
                    target = self._get_ai_folder_mapping(context.ai_assistant)
                    logging.debug(f"Commands target: {target}")
                elif mapping.source == "context":
                    # Use assistant-specific context file directory
                    target = self._get_ai_context_folder_mapping(context.ai_assistant)
                    logging.debug(f"Context target: {target}")
                else:
                    # Use standard pattern formatting for other folders
                    target = mapping.target_pattern.format(
                        ai_assistant=context.ai_assistant,
                        project_name=context.project_name,
                    )
                    logging.debug(f"Other target: {target}")

                if context.project_path is None:
                    raise ValueError("Project path is required for template processing")
                target_path = context.project_path / target
                logging.debug(f"Target path: {target_path}")

                if verbose:
                    self._console.print(
                        f"[blue]Processing {mapping.source} → {target}[/blue]"
                    )

                # Get source folder and process templates
                if self._use_filesystem:
                    if self._filesystem_root is None:
                        raise ValueError("Filesystem root not set")
                    source_path = self._filesystem_root / mapping.source
                    if not source_path.exists():
                        raise FileNotFoundError(
                            f"Template source not found: {source_path}"
                        )

                    # Ensure target directory exists
                    target_path.mkdir(parents=True, exist_ok=True)

                    # Process files based on render flag
                    if mapping.render:
                        self._render_templates_from_path(
                            source_path,
                            target_path,
                            context,
                            mapping.executable_extensions,
                            result,
                            verbose,
                            mapping.source,  # Pass category for file format determination
                        )
                    else:
                        self._copy_templates_from_path(
                            source_path, target_path, result, verbose
                        )
                else:
                    source_traversable = self._template_root.joinpath(mapping.source)

                    # Ensure target directory exists
                    target_path.mkdir(parents=True, exist_ok=True)

                    # Process files based on render flag
                    if mapping.render:
                        self._render_templates_from_traversable(
                            source_traversable,
                            target_path,
                            context,
                            mapping.executable_extensions,
                            result,
                            verbose,
                            mapping.source,  # Pass category for file format determination
                        )
                    else:
                        self._copy_templates_from_traversable(
                            source_traversable, target_path, result, verbose
                        )

            except Exception as e:
                error_msg = f"Error processing {mapping.source}: {str(e)}"
                result.errors.append(error_msg)
                if verbose:
                    self._console.print(f"[red]Error:[/red] {error_msg}")

        return result

    def _render_templates_from_traversable(
        self,
        source_traversable,  # Traversable object from importlib.resources
        target_path: Path,
        context: TemplateContext,
        executable_extensions: List[str],
        result: RenderResult,
        verbose: bool = False,
        category: str = "",
    ) -> None:
        """Render .j2 templates from a Traversable resource"""
        try:
            # Iterate through items in the traversable
            for item in source_traversable.iterdir():
                # Skip files using PATH_DEFAULTS method
                if PATH_DEFAULTS.should_skip_file(Path(item.name)):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    # Recursively process subdirectories
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self._render_templates_from_traversable(
                        item,
                        sub_target,
                        context,
                        executable_extensions,
                        result,
                        verbose,
                        category,
                    )
                elif item.name.endswith(TEMPLATE_EXTENSION):
                    try:
                        # Read template content
                        template_content = item.read_text(encoding="utf-8")
                        template = Template(template_content)

                        # Determine output filename using assistant file format
                        output_name = self._determine_output_filename(
                            item.name, context.ai_assistant, category
                        )
                        output_file = target_path / output_name

                        if verbose:
                            self._console.print(
                                f"[green]Rendering:[/green] {item.name} → {output_name}"
                            )

                        # Build context for Jinja2
                        render_context = self._prepare_context(context)

                        # Render and write
                        rendered = template.render(**render_context)
                        output_file.write_text(rendered, encoding="utf-8")

                        # Set executable using PATH_DEFAULTS
                        if PATH_DEFAULTS.should_be_executable(output_file):
                            output_file.chmod(EXECUTABLE_PERMISSIONS)
                            if verbose:
                                self._console.print(
                                    f"[blue]Made executable:[/blue] {output_name}"
                                )

                        result.rendered_files.append(output_file)

                    except Exception as e:
                        error_msg = f"Failed to render {item.name}: {str(e)}"
                        result.errors.append(error_msg)
                        if verbose:
                            self._console.print(f"[red]Error:[/red] {error_msg}")

        except Exception as e:
            error_msg = f"Failed to process templates: {str(e)}"
            result.errors.append(error_msg)
            if verbose:
                self._console.print(f"[red]Error:[/red] {error_msg}")

    def _copy_templates_from_traversable(
        self,
        source_traversable,  # Traversable object from importlib.resources
        target_path: Path,
        result: RenderResult,
        verbose: bool = False,
    ) -> None:
        """Copy templates as-is from a Traversable resource (for runtime templates)"""
        try:
            # Iterate through items in the traversable
            for item in source_traversable.iterdir():
                # Skip files using PATH_DEFAULTS method
                if PATH_DEFAULTS.should_skip_file(Path(item.name)):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    # Recursively process subdirectories
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self._copy_templates_from_traversable(
                        item, sub_target, result, verbose
                    )
                else:
                    try:
                        # Copy file as-is
                        output_file = target_path / item.name
                        output_file.write_bytes(item.read_bytes())
                        result.copied_files.append(output_file)

                        if verbose:
                            self._console.print(f"[cyan]Copied:[/cyan] {item.name}")

                    except Exception as e:
                        error_msg = f"Failed to copy {item.name}: {str(e)}"
                        result.errors.append(error_msg)
                        if verbose:
                            self._console.print(f"[red]Error:[/red] {error_msg}")

        except Exception as e:
            error_msg = f"Failed to copy templates: {str(e)}"
            result.errors.append(error_msg)
            if verbose:
                self._console.print(f"[red]Error:[/red] {error_msg}")

    def enhance_context_with_platform_info(
        self, context: TemplateContext, platform_name: str
    ) -> TemplateContext:
        """Enhance template context with platform-specific information.

        Args:
            context: Base template context
            platform_name: Name of the platform (windows, macos, linux)

        Returns:
            Enhanced template context with platform information
        """
        # Create a copy of the context and add platform-specific information
        enhanced_context = TemplateContext(
            project_name=context.project_name,
            ai_assistant=context.ai_assistant,
            branch_naming_config=context.branch_naming_config,
            config_directory=context.config_directory,
            creation_date=context.creation_date,
            project_path=context.project_path,
        )

        # Add platform-specific information to the context
        enhanced_context.platform_name = platform_name

        return enhanced_context

    def _render_templates_from_path(
        self,
        source_path: Path,
        target_path: Path,
        context: TemplateContext,
        executable_extensions: List[str],
        result: RenderResult,
        verbose: bool = False,
        category: str = "",
    ) -> None:
        """Render .j2 templates from a filesystem Path"""
        try:
            for item in source_path.iterdir():
                if PATH_DEFAULTS.should_skip_file(item):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self._render_templates_from_path(
                        item,
                        sub_target,
                        context,
                        executable_extensions,
                        result,
                        verbose,
                        category,
                    )
                else:
                    try:
                        if item.name.endswith(TEMPLATE_EXTENSION):
                            # Determine output filename using assistant file format
                            output_name = self._determine_output_filename(
                                item.name, context.ai_assistant, category
                            )
                            template_content = item.read_text()

                            env = Environment(
                                loader=FileSystemLoader(str(item.parent)),
                                keep_trailing_newline=True,
                            )
                            template = env.from_string(template_content)
                            rendered = template.render(context.to_dict())

                            output_file = target_path / output_name
                            output_file.write_text(rendered)

                            if any(
                                output_name.endswith(ext)
                                for ext in executable_extensions
                            ):
                                output_file.chmod(EXECUTABLE_PERMISSIONS)
                                if verbose:
                                    self._console.print(
                                        f"[blue]Made executable:[/blue] {output_name}"
                                    )

                            result.rendered_files.append(output_file)
                            if verbose:
                                self._console.print(
                                    f"[green]Rendered:[/green] {item.name} → {output_name}"
                                )

                    except Exception as e:
                        error_msg = f"Failed to render {item.name}: {str(e)}"
                        result.errors.append(error_msg)
                        if verbose:
                            self._console.print(f"[red]Error:[/red] {error_msg}")

        except Exception as e:
            error_msg = f"Failed to process templates: {str(e)}"
            result.errors.append(error_msg)
            if verbose:
                self._console.print(f"[red]Error:[/red] {error_msg}")

    def _copy_templates_from_path(
        self,
        source_path: Path,
        target_path: Path,
        result: RenderResult,
        verbose: bool = False,
    ) -> None:
        """Copy templates as-is from a filesystem Path"""
        try:
            for item in source_path.iterdir():
                if PATH_DEFAULTS.should_skip_file(item):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self._copy_templates_from_path(item, sub_target, result, verbose)
                else:
                    try:
                        output_file = target_path / item.name
                        output_file.write_bytes(item.read_bytes())
                        result.copied_files.append(output_file)
                        if verbose:
                            self._console.print(f"[cyan]Copied:[/cyan] {item.name}")

                    except Exception as e:
                        error_msg = f"Failed to copy {item.name}: {str(e)}"
                        result.errors.append(error_msg)
                        if verbose:
                            self._console.print(f"[red]Error:[/red] {error_msg}")

        except Exception as e:
            error_msg = f"Failed to copy templates: {str(e)}"
            result.errors.append(error_msg)
            if verbose:
                self._console.print(f"[red]Error:[/red] {error_msg}")

    def render_templates(
        self,
        templates_path: Path,
        destination_path: Path,
        ai_assistants: List[str],
        project_name: str,
        branch_pattern: str,
    ) -> RenderResult:
        """
        Render templates from a given path for multiple AI assistants (used by fallback mechanism)

        Args:
            templates_path: Path to templates directory
            destination_path: Target project directory
            ai_assistants: List of AI assistant names (e.g., ["claude", "gemini"])
            project_name: Name of the project
            branch_pattern: Branch naming pattern

        Returns:
            RenderResult with success status and processed files
        """
        _branch_pattern = branch_pattern

        # Import here to avoid circular imports
        from specify_cli.services.project_manager import ProjectManager

        manager = ProjectManager()

        # Temporarily set the filesystem root to the provided path
        original_filesystem_root = self._filesystem_root
        original_use_filesystem = self._use_filesystem

        all_errors = []

        try:
            # For fallback, we need to use FileSystem access instead of importlib.resources
            self._filesystem_root = templates_path
            self._use_filesystem = True

            # Render templates for each AI assistant
            for ai_assistant in ai_assistants:
                # Create template context for this assistant
                context = TemplateContext(
                    project_name=project_name,
                    ai_assistant=ai_assistant,
                    project_path=destination_path,
                    branch_naming_config=BranchNamingConfig(),
                )

                # Get default folder mappings for this AI assistant
                folder_mappings = manager._get_default_folder_mappings(ai_assistant)

                result = self.render_all_templates_from_mappings(
                    folder_mappings, context, verbose=True
                )

                if not result.success:
                    all_errors.extend(
                        [f"{ai_assistant}: {error}" for error in result.errors]
                    )

        except Exception as e:
            raise RuntimeError(f"Failed to render templates: {str(e)}") from e
        finally:
            # Restore original state
            self._filesystem_root = original_filesystem_root
            self._use_filesystem = original_use_filesystem

        # Return combined result
        return RenderResult(errors=all_errors)

    def compare_templates(
        self, project_path: Path, new_template_dir: Optional[Path] = None
    ) -> TemplateDiff:
        """Compare current project files with templates from a source."""
        changes = []

        # Get new templates (built-in if new_template_dir is None)
        if new_template_dir is None:
            new_templates = self._get_builtin_template_contents()
        else:
            new_templates = self._get_directory_template_contents(new_template_dir)

        # Get all AI assistants in project to determine what files to compare
        ai_directories = self._get_ai_directories(project_path)

        # Render new templates to get final file contents
        rendered_new_files = self._render_templates_for_comparison(
            new_templates, project_path, ai_directories
        )

        # Only compare files that templates would actually generate
        # Don't include arbitrary project files like .claude/doc/*
        for file_path in sorted(rendered_new_files.keys()):
            # Get current content for this specific template-generated file
            current_file_path = project_path / file_path
            current_content = None
            if current_file_path.exists():
                try:
                    current_content = current_file_path.read_text(encoding="utf-8")
                except Exception:
                    # Skip files we can't read
                    continue

            new_content = rendered_new_files[file_path]

            # Check if this file should be skipped
            should_skip = self._should_skip_file_update(file_path, project_path)

            if current_content is None:
                # New file to be added
                lines_added = len(new_content.splitlines()) if new_content else 0
                changes.append(
                    TemplateChange(
                        template_name=file_path,
                        change_type=TemplateChangeType.ADDED,
                        new_content=new_content,
                        category=self._get_file_category(file_path),
                        lines_added=lines_added,
                        should_skip=should_skip,
                    )
                )
            elif current_content != new_content:
                # File modified
                lines_added, lines_removed = self._calculate_line_diff(
                    current_content, new_content
                )
                changes.append(
                    TemplateChange(
                        template_name=file_path,
                        change_type=TemplateChangeType.MODIFIED,
                        old_content=current_content,
                        new_content=new_content,
                        category=self._get_file_category(file_path),
                        lines_added=lines_added,
                        lines_removed=lines_removed,
                        should_skip=should_skip,
                    )
                )
            else:
                # File unchanged
                changes.append(
                    TemplateChange(
                        template_name=file_path,
                        change_type=TemplateChangeType.UNCHANGED,
                        category=self._get_file_category(file_path),
                        should_skip=should_skip,
                    )
                )

        return TemplateDiff(changes=changes)

    def _get_builtin_template_contents(self) -> dict[str, str]:
        """Get contents of all built-in templates."""
        templates = {}
        try:
            import specify_cli.templates as templates_pkg

            # Use the same categories as discover_templates
            categories = PATH_DEFAULTS.TEMPLATE_CATEGORIES

            for category in categories:
                try:
                    category_files = importlib.resources.files(templates_pkg) / category
                    if category_files.is_dir():
                        for file_path in category_files.iterdir():
                            if file_path.is_file() and file_path.name.endswith(
                                TEMPLATE_EXTENSION
                            ):
                                content = file_path.read_text(encoding="utf-8")
                                # Use relative path as key
                                template_key = f"{category}/{file_path.name}"
                                templates[template_key] = content
                except Exception:
                    # Skip problematic categories
                    continue
        except Exception:
            # Return empty dict if we can't access built-in templates
            pass

        return templates

    def _get_directory_template_contents(self, template_dir: Path) -> dict[str, str]:
        """Get contents of all templates in a directory."""
        templates = {}

        if not template_dir.exists() or not template_dir.is_dir():
            return templates

        try:
            # Recursively find all .j2 templates
            for template_file in template_dir.rglob(f"*{TEMPLATE_EXTENSION}"):
                if PATH_DEFAULTS.should_skip_file(template_file):
                    continue

                try:
                    content = template_file.read_text(encoding="utf-8")
                    # Use relative path from template_dir as key
                    relative_path = template_file.relative_to(template_dir)
                    templates[str(relative_path)] = content
                except Exception:
                    # Skip problematic files
                    continue
        except Exception:
            # Return what we have if there's an error
            pass

        return templates

    def _get_template_category(self, template_path: str) -> str:
        """Extract category from template path."""
        if "/" in template_path:
            return template_path.split("/")[0]
        return "unknown"

    def _get_ai_directories(self, project_path: Path) -> list[str]:
        """Get list of AI assistant directories in the project."""
        ai_dirs = []
        for dir_path in project_path.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith("."):
                # Check if this matches any known AI assistant pattern
                known_assistants = ["claude", "copilot", "cursor", "gemini"]
                dir_name = dir_path.name[1:]  # Remove the dot
                if dir_name in known_assistants:
                    ai_dirs.append(dir_name)
        return ai_dirs

    def _render_templates_for_comparison(
        self, templates: dict[str, str], project_path: Path, ai_assistants: list[str]
    ) -> dict[str, str]:
        """Render templates to get final file contents for comparison."""
        rendered_files = {}

        # For each AI assistant, render templates
        for ai_assistant in ai_assistants:
            context = self._create_comparison_context(project_path, ai_assistant)

            for template_path, template_content in templates.items():
                try:
                    # Create Jinja2 template
                    env = Environment(keep_trailing_newline=True)
                    template = env.from_string(template_content)

                    # Render with context
                    rendered_content = template.render(**self._prepare_context(context))

                    # Determine output file path
                    output_path = self._determine_output_path_for_ai(
                        template_path, ai_assistant, project_path
                    )

                    if output_path:
                        rendered_files[output_path] = rendered_content

                except Exception:
                    # Skip templates that can't be rendered
                    continue

        return rendered_files

    def _create_comparison_context(
        self, project_path: Path, ai_assistant: str
    ) -> TemplateContext:
        """Create a basic template context for comparison rendering."""
        from specify_cli.models.config import BranchNamingConfig

        return TemplateContext(
            project_name=project_path.name,
            ai_assistant=ai_assistant,
            project_path=project_path,
            branch_naming_config=BranchNamingConfig(),
        )

    def _determine_output_path_for_ai(
        self,
        template_path: str,
        ai_assistant: str,
        project_path: Path,  # noqa: ARG002
    ) -> Optional[str]:
        """Determine where a template would be rendered for a specific AI assistant."""
        # Remove .j2 extension
        if template_path.endswith(TEMPLATE_EXTENSION):
            base_path = template_path[: -len(TEMPLATE_EXTENSION)]
        else:
            base_path = template_path

        # Get category (first part of path)
        if "/" not in base_path:
            return None

        category, filename = base_path.split("/", 1)

        # Determine output path based on category and AI assistant
        if category == "commands":
            assistant = get_assistant(ai_assistant)
            if assistant:
                commands_dir = assistant.config.command_files.directory
                return f"{commands_dir}/{filename}"
        elif category == "context":
            assistant = get_assistant(ai_assistant)
            if assistant:
                return assistant.config.context_file.file
        elif category == "scripts":
            return f".specify/scripts/{filename}"
        elif category == "memory":
            return f".specify/memory/{filename}"

        return None

    def _should_skip_file_update(self, file_path: str, project_path: Path) -> bool:
        """Determine if a file should be skipped during updates."""
        # Skip context files by default (they contain user customizations)
        if self._is_context_file(file_path, project_path):
            return True

        # Skip any files in .specify/memory (user data)
        return file_path.startswith(".specify/memory/")

    def _is_context_file(self, file_path: str, project_path: Path) -> bool:  # noqa: ARG002
        """Check if a file is a context file (like CLAUDE.md, COPILOT.md, etc.)."""
        # Check against known AI assistants
        from specify_cli.assistants import get_all_assistants

        assistants = get_all_assistants()
        for assistant in assistants:
            if file_path == assistant.config.context_file.file:
                return True
        return False

    def _get_file_category(self, file_path: str) -> str:
        """Get category for a project file."""
        if file_path.startswith(".specify/"):
            if "scripts" in file_path:
                return "scripts"
            elif "memory" in file_path:
                return "memory"
            return "config"
        elif file_path.startswith("."):
            # AI assistant directory
            return "assistant"
        elif "/" not in file_path:
            return "root"
        else:
            return "other"

    def _calculate_line_diff(
        self, old_content: Optional[str], new_content: Optional[str]
    ) -> tuple[int, int]:
        """Calculate lines added and removed between two content strings."""
        old_lines = [] if old_content is None else old_content.splitlines()
        new_lines = [] if new_content is None else new_content.splitlines()

        # Simple line count difference (could be enhanced with proper diff algorithm)
        old_count = len(old_lines)
        new_count = len(new_lines)

        if new_count > old_count:
            lines_added = new_count - old_count
            lines_removed = 0
        elif old_count > new_count:
            lines_added = 0
            lines_removed = old_count - new_count
        else:
            # Same number of lines, but content changed
            # Count actual differences (simplified)
            different_lines = sum(
                1 for old, new in zip(old_lines, new_lines, strict=False) if old != new
            )
            lines_added = different_lines
            lines_removed = different_lines

        return lines_added, lines_removed


def get_template_service() -> JinjaTemplateService:
    """Factory function to create a JinjaTemplateService instance"""
    return JinjaTemplateService()

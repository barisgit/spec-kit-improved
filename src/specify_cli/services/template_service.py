"""
Template service for rendering Jinja2 templates in spec-kit

This module provides an interface and implementation for template processing,
supporting Jinja2 template rendering with context variables.
"""

import importlib.resources
import platform
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, TypedDict, Union, cast

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    TemplateSyntaxError,
)
from jinja2.meta import find_undeclared_variables
from rich.console import Console

from specify_cli.models.project import TemplateContext, TemplateFile
from specify_cli.models.template import (
    GranularTemplate,
    TemplatePackage,
    TemplateState,
)


class TemplateFolderMapping(TypedDict):
    """Type-safe template folder configuration"""

    source: str  # Source folder in init_templates/
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


@dataclass
class TemplateRenderResult:
    """Result of rendering a single template"""

    template: GranularTemplate
    content: str
    target_path: str
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
    def render_template(self, template_name: str, context: TemplateContext) -> str:
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


class JinjaTemplateService(TemplateService):
    """Jinja2-based template service implementation"""

    def __init__(self, skip_patterns: Optional[List[str]] = None):
        self._template_dir: Optional[Path] = None
        self._custom_template_dir: Optional[Path] = None
        self._ai_assistant: Optional[str] = None
        self._environment: Optional[Environment] = None
        self._discovered_templates: List[GranularTemplate] = []

        # FIXME: HARDCODED - Default patterns to skip when processing templates
        # TODO: Move to TemplateProcessingConfig with configurable skip patterns
        self.skip_patterns = skip_patterns or [
            "__init__.py",
            "__pycache__",
            ".pyc",
            ".DS_Store",
            ".gitkeep",
        ]

        # FIXME: HARDCODED - Template root path hardcoded to init_templates
        # TODO: Make configurable via TemplateProcessingConfig.template_root_path
        # Get template root from package resources using Traversable API
        # TODO: This should be configurable, now we are hardcoding it to the init_templates folder
        self._template_root = importlib.resources.files("specify_cli").joinpath(
            "init_templates"
        )
        self._console = Console()

    def load_template_package(self, ai_assistant: str, template_dir: Path) -> bool:
        """Load template package for specified AI assistant"""
        try:
            if not template_dir.exists() or not template_dir.is_dir():
                return False

            # Check if directory contains template files
            template_files = list(template_dir.glob("*.j2"))
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
        self, template_name: Union[str, GranularTemplate], context: TemplateContext
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
                if output_filename.endswith(".j2"):
                    output_filename = output_filename[:-3]

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

        Handles both test TemplateContext (with limited fields) and
        real TemplateContext (with full model).
        """
        # Use to_dict method if available (both test and real contexts should have it now)
        if hasattr(context, "to_dict"):
            return context.to_dict()
        else:
            # Fallback: extract common attributes manually
            context_dict = {}

            # Extract standard fields
            for attr in [
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
            ]:
                if hasattr(context, attr):
                    context_dict[attr] = getattr(context, attr)

            # Handle additional_vars separately
            if hasattr(context, "additional_vars"):
                additional_vars = context.additional_vars
                if isinstance(additional_vars, dict):
                    context_dict["additional_vars"] = additional_vars
                    # Also merge the values directly for backwards compatibility
                    context_dict.update(additional_vars)

            # Handle date/creation_date variations
            if "creation_date" in context_dict and "date" not in context_dict:
                context_dict["date"] = context_dict["creation_date"]

            # Handle template_variables and custom_fields
            if hasattr(context, "template_variables"):
                template_vars = context.template_variables
                if isinstance(template_vars, dict):
                    context_dict.update(template_vars)

            if hasattr(context, "custom_fields"):
                custom_fields = context.custom_fields
                if isinstance(custom_fields, dict):
                    context_dict.update(custom_fields)

            return context_dict

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
        # FIXME: HARDCODED - Executable extensions hardcoded
        # TODO: Move to TemplateProcessingConfig.executable_extensions
        # Check file extension patterns
        executable_extensions = {".sh", ".py", ".rb", ".pl", ".js"}

        # Remove .j2 extension if present for checking
        check_name = template_path.name
        if check_name.endswith(".j2"):
            check_name = check_name[:-3]

        check_path = Path(check_name)
        if check_path.suffix in executable_extensions:
            return True

        # Check for shebang in content
        if content.startswith("#!"):
            return True

        # FIXME: HARDCODED - Executable patterns hardcoded
        # TODO: Move to TemplateProcessingConfig.executable_patterns
        # Check for specific executable patterns in filename
        executable_patterns = ["run", "start", "stop", "deploy", "build", "test"]
        return any(pattern in check_name.lower() for pattern in executable_patterns)

    def discover_templates(self) -> List[GranularTemplate]:
        """Discover templates from package resources"""
        if self._discovered_templates:
            return self._discovered_templates

        templates = []
        try:
            # Get reference to the init_templates package
            import specify_cli.init_templates as templates_pkg

            # FIXME: HARDCODED - Template categories hardcoded
            # TODO: Make configurable via TemplateProcessingConfig.template_categories
            # Discover templates in each category directory
            categories = ["commands", "scripts", "memory", "runtime_templates"]

            for category in categories:
                try:
                    # Get files in this category directory
                    category_files = importlib.resources.files(templates_pkg) / category
                    if category_files.is_dir():
                        for file_path in category_files.iterdir():
                            if file_path.is_file() and file_path.name.endswith(".j2"):
                                # Simple mapping: filename.ext.j2 → filename.ext
                                # For "create-feature.py.j2" -> "create-feature.py"
                                # For "create-feature.j2" -> "create-feature"
                                filename_without_j2 = file_path.name[:-3]  # Remove .j2
                                template_name = filename_without_j2

                                # Determine target path based on category and template name
                                target_path = self._determine_target_path(
                                    category, template_name
                                )

                                # Determine if executable (scripts only)
                                executable = category == "scripts"

                                # All command and memory templates are AI-aware
                                ai_aware = category in ["commands", "memory"]

                                template = GranularTemplate(
                                    name=template_name,
                                    template_path=f"{category}/{file_path.name}",
                                    target_path=target_path,
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

    def _determine_target_path(self, category: str, template_name: str) -> str:
        """Determine target path for template based on category and name"""
        # FIXME: HARDCODED - Target path patterns hardcoded
        # TODO: Move to TargetPathConfig configuration model
        if category == "commands":
            # AI-specific commands will be resolved during rendering based on context
            # template_name already includes .md extension from .md.j2 files
            return f".claude/commands/{template_name}"
        elif category == "scripts":
            # template_name already includes .py extension from .py.j2 files
            return f".specify/scripts/{template_name}"
        elif category == "memory":
            # template_name already includes .md extension from .md.j2 files
            return f".specify/memory/{template_name}"
        elif category == "runtime_templates":
            # runtime templates keep their .j2 extension in target path
            # but template_name from .md.j2 becomes .md, so we need to add .j2 back
            if not template_name.endswith(".j2"):
                template_name = f"{template_name}.j2"
            return f".specify/templates/{template_name}"
        else:
            return f".specify/{template_name}"

    def _get_ai_folder_mapping(self, ai_assistant: str) -> str:
        """Get AI-specific folder structure"""
        # FIXME: HARDCODED - AI assistant directory mappings hardcoded
        # TODO: Move to AIAssistantMapping configuration model
        ai_folder_mapping = {
            "claude": ".claude/commands",
            "gemini": ".gemini/commands",
            "copilot": ".github/copilot"
        }
        return ai_folder_mapping.get(ai_assistant, f".{ai_assistant}/commands")

    def _determine_ai_specific_target_path(
        self, category: str, template_name: str, ai_assistant: str
    ) -> str:
        """Determine AI-specific target path for template"""
        if category == "commands":
            # template_name already includes .md extension from .md.j2 files
            base_folder = self._get_ai_folder_mapping(ai_assistant)
            return f"{base_folder}/{template_name}"
        else:
            return self._determine_target_path(category, template_name)

    def discover_templates_by_category(self, category: str) -> List[GranularTemplate]:
        """Filter templates by category"""
        all_templates = self.discover_templates()
        return [t for t in all_templates if t.category == category]

    def load_template(self, template_name: str) -> GranularTemplate:
        """Load individual template object"""
        # Find template by name (with or without .j2 extension)
        search_name = template_name.replace(".j2", "")

        templates = self.discover_templates()
        template = next((t for t in templates if t.name == search_name), None)

        if not template:
            raise FileNotFoundError(f"Template not found: {template_name}")

        # Load the Jinja2 template if not already loaded
        if template.state == TemplateState.DISCOVERED:
            try:
                # Load from package resources
                import specify_cli.init_templates as templates_pkg

                template_content = (
                    importlib.resources.files(templates_pkg) / template.template_path
                ).read_text()

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
                    target_path=loaded_template.target_path,
                    success=True,
                )
                results.append(result)

            except Exception as e:
                # Create error result
                template.mark_error(str(e))
                result = TemplateRenderResult(
                    template=template,
                    content="",
                    target_path=template.target_path,
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
                    "target_path": template.target_path,
                }
            )

            # Add branch pattern context if available
            if (
                hasattr(context, "branch_naming_config")
                and context.branch_naming_config
            ):
                patterns = context.branch_naming_config.patterns
                if patterns:
                    # Use first pattern as primary
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

        for mapping in folder_mappings:
            try:
                # Build target path with AI-specific logic for commands
                if mapping["source"] == "commands":
                    # Use centralized AI-specific folder structure
                    target = self._get_ai_folder_mapping(context.ai_assistant)
                else:
                    # Use standard pattern formatting for non-command folders
                    target = mapping["target_pattern"].format(
                        ai_assistant=context.ai_assistant, project_name=context.project_name
                    )
                target_path = context.project_path / target

                if verbose:
                    self._console.print(
                        f"[blue]Processing {mapping['source']} → {target}[/blue]"
                    )

                # Get source folder as Traversable
                source_traversable = self._template_root.joinpath(mapping["source"])

                # Ensure target directory exists
                target_path.mkdir(parents=True, exist_ok=True)

                # Process files based on render flag
                if mapping["render"]:
                    self._render_templates_from_traversable(
                        source_traversable,
                        target_path,
                        context,
                        mapping["executable_extensions"],
                        result,
                        verbose,
                    )
                else:
                    self._copy_templates_from_traversable(
                        source_traversable, target_path, result, verbose
                    )

            except Exception as e:
                error_msg = f"Error processing {mapping['source']}: {str(e)}"
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
    ) -> None:
        """Render .j2 templates from a Traversable resource"""
        try:
            # Iterate through items in the traversable
            for item in source_traversable.iterdir():
                # Skip files matching skip patterns
                if any(pattern in item.name for pattern in self.skip_patterns):
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
                    )
                elif item.name.endswith(".j2"):
                    try:
                        # Read template content
                        template_content = item.read_text(encoding="utf-8")
                        template = Template(template_content)

                        # Output file: remove .j2 extension
                        output_name = item.name[:-3]
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

                        # Set executable if needed
                        if any(
                            str(output_file).endswith(ext)
                            for ext in executable_extensions
                        ):
                            output_file.chmod(0o755)
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
                # Skip files matching skip patterns
                if any(pattern in item.name for pattern in self.skip_patterns):
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

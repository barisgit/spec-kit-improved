"""
Template Rendering Service - focused on Jinja2 template rendering operations.

This service handles:
- Template rendering with context variables
- Bulk template processing from various sources
- File system and package resource template rendering
- Platform-specific context injection
- Rendering error handling and reporting
"""

import logging
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateRuntimeError,
    TemplateSyntaxError,
)
from rich.console import Console

from specify_cli.core.constants import CONSTANTS
from specify_cli.models.defaults.path_defaults import PATH_DEFAULTS
from specify_cli.models.project import TemplateContext
from specify_cli.services.template_registry import TEMPLATE_REGISTRY
from specify_cli.utils.security import TemplateSecurityError, TemplateSecurityValidator

from .models import RenderResult
from .template_context_processor import TemplateContextProcessor

logger = logging.getLogger(__name__)


class TemplateRenderResult:
    """Result of rendering a single template."""

    def __init__(
        self, template_name: str, success: bool, content: str = "", error: str = ""
    ):
        self.template_name = template_name
        self.success = success
        self.content = content
        self.error = error


class TemplateRenderer:
    """Service focused on template rendering operations."""

    def __init__(self):
        """Initialize template renderer."""
        self._console = Console()
        self._security_validator = TemplateSecurityValidator()
        self._context_processor = TemplateContextProcessor()

    def render_template(
        self, template: Template, context: TemplateContext, template_name: str = ""
    ) -> TemplateRenderResult:
        """Render a specific template with given context.

        Args:
            template: Jinja2 template to render
            context: Template context variables
            template_name: Name of template for error reporting

        Returns:
            TemplateRenderResult with success status and content/error

        Raises:
            ValueError: If template or context is None
            RuntimeError: If template fails to render
        """
        if template is None:
            raise ValueError("Template cannot be None")

        if context is None:
            raise ValueError(CONSTANTS.ERRORS.TEMPLATE_CONTEXT_NONE)

        # Prepare context dictionary
        context_dict = self._prepare_context(context)

        try:
            # Security validation before rendering
            try:
                # Get template source for validation
                template_source = getattr(template, "source", "")
                if hasattr(template, "environment") and hasattr(
                    template.environment, "get_template"
                ):
                    # For templates loaded from environment, we can't easily get source
                    # So we'll validate the context only
                    sanitized_context = (
                        self._security_validator.sanitizer.sanitize_context_dict(
                            context_dict
                        )
                    )
                else:
                    # For direct template strings, validate both template and context
                    sanitized_context = (
                        self._security_validator.sanitizer.sanitize_context_dict(
                            context_dict
                        )
                    )
                    if template_source:
                        self._security_validator.sanitizer.validate_template_complexity(
                            template_source
                        )

            except TemplateSecurityError as e:
                error_msg = f"Security validation failed for {template_name}: {str(e)}"
                logger.warning(error_msg)
                return TemplateRenderResult(
                    template_name=template_name, success=False, error=error_msg
                )

            # Render the template with sanitized context
            rendered_content = template.render(sanitized_context)
            return TemplateRenderResult(
                template_name=template_name, success=True, content=rendered_content
            )

        except TemplateSyntaxError as e:
            error_msg = CONSTANTS.ERRORS.TEMPLATE_SYNTAX_ERROR.format(
                template_name=template_name, error=str(e)
            )
            return TemplateRenderResult(
                template_name=template_name, success=False, error=error_msg
            )

        except TemplateRuntimeError as e:
            error_msg = CONSTANTS.ERRORS.FAILED_RENDER_TEMPLATE.format(
                template_name=template_name, error=str(e)
            )
            return TemplateRenderResult(
                template_name=template_name, success=False, error=error_msg
            )

        except Exception as e:
            error_msg = CONSTANTS.ERRORS.UNEXPECTED_TEMPLATE_ERROR.format(
                template_name=template_name, error=str(e)
            )
            return TemplateRenderResult(
                template_name=template_name, success=False, error=error_msg
            )

    def render_multiple_templates(
        self, templates: List[tuple[Template, str]], context: TemplateContext
    ) -> List[TemplateRenderResult]:
        """Render multiple templates with the same context.

        Args:
            templates: List of (template, name) tuples
            context: Template context variables

        Returns:
            List of render results
        """
        results = []
        for template, name in templates:
            result = self.render_template(template, context, name)
            results.append(result)
        return results

    def _prepare_context(self, context: TemplateContext) -> Dict[str, Any]:
        """Prepare template context with platform-specific information.

        Args:
            context: Template context to enhance

        Returns:
            Enhanced context dictionary
        """
        # Use the context processor for consistent context preparation
        context_dict = self._context_processor.prepare_context(context)

        # Add platform-specific variables
        context_dict.update(self._get_platform_context())

        # Add any additional context enhancements
        context_dict = self._enhance_context(context_dict, context)

        return context_dict

    def _extract_context_attributes(self, context: TemplateContext) -> Dict[str, Any]:
        """Extract attributes from TemplateContext object.

        Args:
            context: Template context object

        Returns:
            Dictionary of context attributes
        """
        context_dict = {}

        # Extract all non-private attributes from the context object
        for attr_name in dir(context):
            if not attr_name.startswith("_"):
                attr_value = getattr(context, attr_name)
                # Only include simple types, not methods
                if not callable(attr_value):
                    context_dict[attr_name] = attr_value

        return context_dict

    def _get_platform_context(self) -> Dict[str, Any]:
        """Get platform-specific context variables.

        Returns:
            Dictionary of platform-specific variables
        """
        system = platform.system().lower()

        if system == "windows":
            return {
                "platform_system": "windows",
                "platform_python_version": platform.python_version(),
                "path_separator": "\\",
                "script_extension": CONSTANTS.FILE.BATCH_EXTENSION,
            }
        else:
            return {
                "platform_system": system,
                "platform_python_version": platform.python_version(),
                "path_separator": "/",
                "script_extension": CONSTANTS.FILE.SHELL_EXTENSION,
            }

    def _enhance_context(
        self, context_dict: Dict[str, Any], context: TemplateContext
    ) -> Dict[str, Any]:
        """Enhance context with additional computed values.

        Args:
            context_dict: Base context dictionary
            context: Original template context

        Returns:
            Enhanced context dictionary
        """
        # Add any computed or derived values here

        # Example: Add assistant-specific context
        if hasattr(context, "ai_assistant") and context.ai_assistant:
            context_dict["assistant_name"] = context.ai_assistant
            context_dict["assistant_config_dir"] = f".{context.ai_assistant}"

        # Add project-specific context
        if hasattr(context, "project_name") and context.project_name:
            context_dict["project_slug"] = context.project_name.lower().replace(
                " ", "-"
            )

        return context_dict

    def render_templates_from_traversable(
        self,
        source_traversable,
        target_path: Path,
        context: TemplateContext,
        executable_extensions: List[str],
        result: RenderResult,
        verbose: bool = False,
        category: str = "",
        skip_patterns: Optional[List[str]] = None,
        determine_output_filename_callback=None,
    ) -> None:
        """Render .j2 templates from a Traversable resource.

        Args:
            source_traversable: Traversable source containing templates
            target_path: Target directory for rendered files
            context: Template context for rendering
            executable_extensions: List of extensions to make executable
            result: RenderResult to accumulate results
            verbose: Whether to print verbose output
            category: Template category for filtering
            skip_patterns: File patterns to skip
            determine_output_filename_callback: Callback to determine output filename
        """
        skip_patterns = skip_patterns or CONSTANTS.PATTERNS.SKIP_PATTERNS

        try:
            for item in source_traversable.iterdir():
                if any(Path(item.name).match(pattern) for pattern in skip_patterns):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self.render_templates_from_traversable(
                        item,
                        sub_target,
                        context,
                        executable_extensions,
                        result,
                        verbose,
                        category,
                        skip_patterns,
                        determine_output_filename_callback,
                    )
                elif item.name.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
                    if category == "agent-prompts" and hasattr(
                        context, "selected_agents"
                    ):
                        agent_name = item.name.replace(
                            CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX, ""
                        )
                        if not TEMPLATE_REGISTRY.should_include_template(
                            category, agent_name, context.selected_agents or []
                        ):
                            if verbose:
                                self._console.print(
                                    f"[yellow]Skipped agent:[/yellow] {agent_name} (not selected)"
                                )
                            continue

                    try:
                        template_content = item.read_text(encoding="utf-8")
                        template = Template(template_content)

                        # Determine output filename
                        if determine_output_filename_callback:
                            output_name = determine_output_filename_callback(
                                item.name, context.ai_assistant, category
                            )
                        else:
                            output_name = item.name
                            if output_name.endswith(
                                CONSTANTS.FILE.TEMPLATE_J2_EXTENSION
                            ):
                                output_name = output_name[
                                    : -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)
                                ]

                        # Security validation for file operations
                        try:
                            safe_output_name = self._security_validator.path_validator.sanitize_filename(
                                output_name
                            )
                            output_file = target_path / safe_output_name

                            if not self._security_validator.path_validator.validate_safe_path(
                                target_path.parent, output_file
                            ):
                                error_msg = (
                                    f"Unsafe output path for {item.name}: {output_file}"
                                )
                                result.errors.append(error_msg)
                                if verbose:
                                    self._console.print(
                                        f"[red]Security Error:[/red] {error_msg}"
                                    )
                                continue

                            if safe_output_name != output_name and verbose:
                                self._console.print(
                                    f"[yellow]Filename sanitized:[/yellow] {output_name} → {safe_output_name}"
                                )

                        except TemplateSecurityError as e:
                            error_msg = f"Path security validation failed for {item.name}: {str(e)}"
                            result.errors.append(error_msg)
                            if verbose:
                                self._console.print(
                                    f"[red]Security Error:[/red] {error_msg}"
                                )
                            continue

                        if verbose:
                            self._console.print(
                                f"[green]Rendering:[/green] {item.name} → {output_name}"
                            )

                        # Secure template rendering
                        try:
                            render_context = self._prepare_context(context)
                            sanitized_context = (
                                self._security_validator.validate_template_render(
                                    template_content,
                                    render_context,
                                    output_file,
                                    target_path,
                                )
                            )
                            rendered = template.render(**sanitized_context)
                        except TemplateSecurityError as e:
                            error_msg = (
                                f"Security validation failed for {item.name}: {str(e)}"
                            )
                            result.errors.append(error_msg)
                            if verbose:
                                self._console.print(
                                    f"[red]Security Error:[/red] {error_msg}"
                                )
                            continue

                        if output_name and output_name not in result.rendered_files:
                            output_file.write_text(rendered, encoding="utf-8")

                        if TEMPLATE_REGISTRY.should_be_executable(output_file):
                            output_file.chmod(CONSTANTS.FILE.EXECUTABLE_PERMISSIONS)
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

    def copy_templates_from_traversable(
        self,
        source_traversable,
        target_path: Path,
        result: RenderResult,
        verbose: bool = False,
        context: Optional[TemplateContext] = None,
        category: str = "",
        skip_patterns: Optional[List[str]] = None,
    ) -> None:
        """Copy templates as-is from a Traversable resource.

        Args:
            source_traversable: Traversable source containing templates
            target_path: Target directory for copied files
            result: RenderResult to accumulate results
            verbose: Whether to print verbose output
            context: Optional template context for filtering
            category: Template category for filtering
            skip_patterns: File patterns to skip
        """
        skip_patterns = skip_patterns or CONSTANTS.PATTERNS.SKIP_PATTERNS

        try:
            for item in source_traversable.iterdir():
                if any(Path(item.name).match(pattern) for pattern in skip_patterns):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self.copy_templates_from_traversable(
                        item,
                        sub_target,
                        result,
                        verbose,
                        context,
                        category,
                        skip_patterns,
                    )
                else:
                    if (
                        category == "agent-templates"
                        and context
                        and hasattr(context, "selected_agents")
                    ):
                        agent_name = item.name.replace(
                            CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX, ""
                        )

                        if not TEMPLATE_REGISTRY.should_include_template(
                            category, agent_name, context.selected_agents or []
                        ):
                            if verbose:
                                self._console.print(
                                    f"[yellow]Skipped agent template:[/yellow] {agent_name} (not selected, not utility)"
                                )
                            continue

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

    def render_templates_from_path(
        self,
        source_path: Path,
        target_path: Path,
        context: TemplateContext,
        executable_extensions: List[str],
        result: RenderResult,
        verbose: bool = False,
        category: str = "",
    ) -> None:
        """Render .j2 templates from a filesystem Path.

        Args:
            source_path: Source directory containing templates
            target_path: Target directory for rendered files
            context: Template context for rendering
            executable_extensions: List of extensions to make executable
            result: RenderResult to accumulate results
            verbose: Whether to print verbose output
            category: Template category for filtering
        """
        try:
            for item in source_path.iterdir():
                if PATH_DEFAULTS.should_skip_file(item):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self.render_templates_from_path(
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
                        if item.name.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
                            output_name = item.name[
                                : -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)
                            ]
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
                                output_file.chmod(CONSTANTS.FILE.EXECUTABLE_PERMISSIONS)
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

    def copy_templates_from_path(
        self,
        source_path: Path,
        target_path: Path,
        result: RenderResult,
        verbose: bool = False,
    ) -> None:
        """Copy templates as-is from a filesystem Path.

        Args:
            source_path: Source directory containing templates
            target_path: Target directory for copied files
            result: RenderResult to accumulate results
            verbose: Whether to print verbose output
        """
        try:
            for item in source_path.iterdir():
                if PATH_DEFAULTS.should_skip_file(item):
                    if verbose:
                        self._console.print(f"[yellow]Skipped:[/yellow] {item.name}")
                    continue

                if item.is_dir():
                    sub_target = target_path / item.name
                    sub_target.mkdir(parents=True, exist_ok=True)
                    self.copy_templates_from_path(item, sub_target, result, verbose)
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

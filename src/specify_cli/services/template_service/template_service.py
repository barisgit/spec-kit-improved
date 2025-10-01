"""
Template service for rendering Jinja2 templates in spec-kit

This module provides the main template service implementation that coordinates
all template operations by delegating to specialized service modules.
"""

import importlib.resources
import logging
import re
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union, cast

from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateNotFound,
    TemplateSyntaxError,
)
from rich.console import Console

from specify_cli.assistants import get_all_assistants, get_assistant
from specify_cli.core.constants import CONSTANTS
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.defaults.path_defaults import PATH_DEFAULTS
from specify_cli.models.project import TemplateContext, TemplateFile
from specify_cli.models.template import (
    GranularTemplate,
    TemplatePackage,
    TemplateState,
)
from specify_cli.services.template_registry import TEMPLATE_REGISTRY

# Import the specialized service modules
from .interfaces import TemplateService
from .models import (
    RenderResult,
    TemplateDiff,
    TemplateFolderMapping,
    TemplateRenderResult,
)
from .template_comparator import TemplateComparator
from .template_context_processor import TemplateContextProcessor
from .template_discovery import TemplateDiscovery
from .template_file_operations import TemplateFileOperations
from .template_loader import TemplateLoader
from .template_renderer import TemplateRenderer
from .template_validator import TemplateValidator


class JinjaTemplateService(TemplateService):
    """Jinja2-based template service implementation that delegates to specialized modules"""

    def __init__(self, skip_patterns: Optional[List[str]] = None):
        # Initialize core service state
        self._template_dir: Optional[Path] = None
        self._custom_template_dir: Optional[Path] = None
        self._ai_assistant: Optional[str] = None
        self._environment: Optional[Environment] = None
        self._use_filesystem: bool = False
        self._filesystem_root: Optional[Path] = None

        # Initialize specialized service modules
        self.skip_patterns = skip_patterns or TEMPLATE_REGISTRY.get_skip_patterns()
        self._loader = TemplateLoader(self.skip_patterns)
        self._renderer = TemplateRenderer()
        self._validator = TemplateValidator()
        self._comparator = TemplateComparator()
        self._discovery = TemplateDiscovery(self.skip_patterns)
        self._context_processor = TemplateContextProcessor()
        self._file_operations = TemplateFileOperations()

        # Get template root from package resources using Traversable API
        self._template_root = importlib.resources.files("specify_cli").joinpath(
            "templates"
        )
        self._console = Console()

    def load_template_package(self, ai_assistant: str, template_dir: Path) -> bool:
        """Load template package for specified AI assistant"""
        try:
            if not template_dir.exists() or not template_dir.is_dir():
                logging.warning("Template directory does not exist: %s", template_dir)
                return False

            # Check if directory contains template files
            has_templates = any(
                template_dir.glob(f"*{CONSTANTS.FILE.TEMPLATE_J2_EXTENSION}")
            )
            if not has_templates:
                # Also check for plain files if policy permits
                has_templates = any(
                    f.is_file() and not f.name.startswith(".")
                    for f in template_dir.iterdir()
                )
            if not has_templates:
                logging.warning("No templates found in %s", template_dir)
                return False

            self._template_dir = template_dir
            self._ai_assistant = ai_assistant
            self._environment = Environment(
                loader=FileSystemLoader(str(template_dir)),
                keep_trailing_newline=True,
            )

            # Add custom filters
            def regex_replace(value: str, pattern: str, replacement: str = "") -> str:
                return self._regex_replace_filter(value, pattern, replacement)

            self._environment.filters["regex_replace"] = cast(
                Callable[..., Any], regex_replace
            )

            # Also delegate to loader module
            return self._loader.load_template_package(ai_assistant, template_dir)

        except Exception:
            logging.exception(
                "Failed to load template package for %s from %s",
                ai_assistant,
                template_dir,
            )
            return False

    def render_template(
        self,
        template_name: Union[str, GranularTemplate],
        context: Optional[TemplateContext],
    ) -> str:
        """Render a specific template with given context"""
        # Validate inputs
        if context is None:
            raise ValueError(CONSTANTS.ERRORS.TEMPLATE_CONTEXT_NONE)

        if not template_name:
            raise ValueError(CONSTANTS.ERRORS.TEMPLATE_NAME_EMPTY)

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
                    raise RuntimeError(CONSTANTS.ERRORS.FAILED_LOAD_ENVIRONMENT)

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
                            CONSTANTS.ERRORS.TEMPLATE_NOT_FOUND.format(
                                template_name=template_name
                            )
                        ) from te
                    except TemplateSyntaxError as tse:
                        raise RuntimeError(
                            CONSTANTS.ERRORS.TEMPLATE_SYNTAX_ERROR.format(
                                template_name=template_name, error=str(tse)
                            )
                        ) from tse
                    except Exception as re:
                        raise RuntimeError(
                            CONSTANTS.ERRORS.FAILED_RENDER_TEMPLATE.format(
                                template_name=template_name, error=str(re)
                            )
                        ) from re
                else:
                    raise FileNotFoundError(
                        CONSTANTS.ERRORS.TEMPLATE_NOT_FOUND.format(
                            template_name=template_name
                        )
                    ) from e

        except (ValueError, FileNotFoundError, RuntimeError):
            # Re-raise these specific exceptions as-is
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise RuntimeError(
                CONSTANTS.ERRORS.UNEXPECTED_TEMPLATE_ERROR.format(
                    template_name=template_name, error=str(e)
                )
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
                if output_filename.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
                    output_filename = output_filename[
                        : -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)
                    ]

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
        """Validate template syntax using validator module"""
        is_valid, error_msg = self._validator.validate_template_syntax(template_path)
        return is_valid, error_msg if error_msg else None

    def get_template_variables(self, template_path: Path) -> List[str]:
        """Extract variables used in template using validator module"""
        return self._validator.get_template_variables(template_path)

    def set_custom_template_dir(self, template_dir: Optional[Path]) -> bool:
        """Set custom template directory"""
        try:
            if template_dir is None:
                self._custom_template_dir = None
                return True

            if not template_dir.exists() or not template_dir.is_dir():
                return False

            self._custom_template_dir = template_dir
            # Also delegate to loader
            return self._loader.set_custom_template_dir(template_dir)

        except Exception:
            return False

    def discover_templates(self) -> List[GranularTemplate]:
        """Discover templates using discovery module"""
        # For now, use the fallback method since the discovery module needs
        # actual filesystem paths, but we're using importlib.resources
        return self._discover_templates_fallback()

    def discover_templates_by_category(self, category: str) -> List[GranularTemplate]:
        """Filter templates by category using discovery module"""
        # Use fallback method and filter by category
        all_templates = self._discover_templates_fallback()
        return [t for t in all_templates if t.category == category]

    def load_template(self, template_name: str) -> GranularTemplate:
        """Load individual template object"""
        # Use fallback implementation for now
        if template_name.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
            search_name = template_name[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]
        else:
            search_name = template_name
        templates = self.discover_templates()
        template = next((t for t in templates if t.name == search_name), None)

        if not template:
            raise FileNotFoundError(
                CONSTANTS.ERRORS.TEMPLATE_NOT_FOUND.format(template_name=template_name)
            )

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
            # Use renderer module for the actual rendering
            result = self._renderer.render_template(
                template.loaded_template, context, template.name
            )

            if not result.success:
                raise RuntimeError(result.error)

            return result.content

        except (ValueError, RuntimeError):
            # Re-raise validation and template errors as-is
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise RuntimeError(
                f"Unexpected error rendering template '{template.name}': {str(e)}"
            ) from e

    def enhance_context_with_platform_info(
        self, context: TemplateContext, platform_name: str
    ) -> TemplateContext:
        """Enhance template context with platform-specific information."""
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

    def compare_templates(
        self,
        project_path: Path,
        new_template_dir: Optional[Path] = None,
        selected_agents: Optional[List[str]] = None,
    ) -> TemplateDiff:
        """Compare current project files with templates using comparator module"""
        # Get new templates (built-in if new_template_dir is None)
        if new_template_dir is None:
            new_templates = self._get_builtin_template_contents()
        else:
            new_templates = self._get_directory_template_contents(new_template_dir)

        # Filter templates based on selected agents
        if selected_agents is not None:
            new_templates = self._filter_templates_by_agents(
                new_templates, selected_agents
            )

        # Get all AI assistants in project to determine what files to compare
        ai_directories = self._get_ai_directories(project_path)

        # Render new templates to get final file contents
        rendered_new_files = self._render_templates_for_comparison(
            new_templates, project_path, ai_directories
        )

        # Generate old templates dictionary from current project files
        old_templates = {}
        for file_path in sorted(rendered_new_files.keys()):
            current_file_path = project_path / file_path
            if current_file_path.exists():
                try:
                    old_templates[file_path] = current_file_path.read_text(
                        encoding="utf-8"
                    )
                except Exception:
                    continue

        # Use comparator module to compare template sets
        categories = {
            name: self._get_file_category(name) for name in rendered_new_files
        }
        diff = self._comparator.compare_template_sets(
            old_templates, rendered_new_files, categories
        )

        # Add skip information
        for change in diff.changes:
            change.should_skip = self._should_skip_file_update(
                change.template_name, project_path
            )

        return diff

    # Helper methods that support the main interface

    def _prepare_context(self, context: TemplateContext) -> dict:
        """Prepare context for template rendering"""
        return self._context_processor.prepare_context(context)

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
        # Use configurable executable extensions from template registry
        executable_extensions = set(CONSTANTS.PATTERNS.EXECUTABLE_EXTENSIONS)

        # Remove .j2 extension if present for checking
        check_name = template_path.name
        if check_name.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
            check_name = check_name[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]

        check_path = Path(check_name)
        if check_path.suffix in executable_extensions:
            return True

        # Check for shebang in content
        if content.startswith("#!"):
            return True

        # Check for specific executable patterns in filename
        executable_name_patterns = ["run", "start", "stop", "deploy", "build", "test"]
        return any(
            pattern in check_name.lower() for pattern in executable_name_patterns
        )

    def _discover_templates_fallback(self) -> List[GranularTemplate]:
        """Fallback template discovery method"""
        templates = []
        try:
            # Get reference to the templates package
            import specify_cli.templates as templates_pkg

            # Use configurable template categories from template registry
            categories = TEMPLATE_REGISTRY.get_category_names()

            for category in categories:
                try:
                    # Get files in this category directory
                    category_files = importlib.resources.files(templates_pkg) / category
                    if category_files.is_dir():
                        for file_path in category_files.iterdir():
                            if file_path.is_file() and file_path.name.endswith(
                                CONSTANTS.FILE.TEMPLATE_J2_EXTENSION
                            ):
                                filename_without_j2 = file_path.name[
                                    : -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)
                                ]
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
                    continue

        except Exception:
            pass

        return templates

    # Additional helper methods for comparison functionality
    def _get_builtin_template_contents(self) -> dict[str, str]:
        """Get contents of all built-in templates."""
        return self._comparator.get_builtin_template_contents()

    def _get_directory_template_contents(self, template_dir: Path) -> dict[str, str]:
        """Get contents of all templates in a directory."""
        return self._comparator.get_directory_template_contents(template_dir)

    def _filter_templates_by_agents(
        self, templates: dict[str, str], selected_agents: List[str]
    ) -> dict[str, str]:
        """Filter templates based on selected agents."""
        return self._comparator.filter_templates_by_agents(templates, selected_agents)

    def _get_ai_directories(self, project_path: Path) -> list[str]:
        """Get list of AI assistant directories in the project."""
        return self._file_operations.get_ai_directories(project_path)

    def _render_templates_for_comparison(
        self, templates: dict[str, str], project_path: Path, ai_assistants: list[str]
    ) -> dict[str, str]:
        """Render templates to get final file contents for comparison."""
        rendered_files = {}

        for ai_assistant in ai_assistants:
            context = self._create_comparison_context(project_path, ai_assistant)

            for template_path, template_content in templates.items():
                try:
                    category = (
                        template_path.split("/")[0] if "/" in template_path else None
                    )

                    should_render = (
                        TEMPLATE_REGISTRY.should_render_category(category)
                        if category
                        else True
                    )

                    if should_render:
                        env = Environment(keep_trailing_newline=True)
                        template = env.from_string(template_content)
                        rendered_content = template.render(
                            **self._prepare_context(context)
                        )
                    else:
                        rendered_content = template_content

                    output_path = self._determine_output_path_for_ai(
                        template_path, ai_assistant, project_path
                    )

                    if output_path:
                        rendered_files[output_path] = rendered_content

                except Exception:
                    continue

        return rendered_files

    def _create_comparison_context(
        self, project_path: Path, ai_assistant: str
    ) -> TemplateContext:
        """Create a basic template context for comparison rendering."""
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
        project_path: Path,
    ) -> Optional[str]:
        _ = project_path

        """Determine where a template would be rendered for a specific AI assistant."""
        if "/" not in template_path:
            return None

        category = template_path.split("/")[0]
        should_render = TEMPLATE_REGISTRY.should_render_category(category)

        if should_render and template_path.endswith(
            CONSTANTS.FILE.TEMPLATE_J2_EXTENSION
        ):
            base_path = template_path[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]
        else:
            base_path = template_path

        if "/" not in base_path:
            return None

        category, filename = base_path.split("/", 1)

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
            return f"{CONSTANTS.DIRECTORY.SPECIFY_SCRIPTS_DIR}/{filename}"
        elif category == "memory":
            return f"{CONSTANTS.DIRECTORY.SPECIFY_MEMORY_DIR}/{filename}"
        elif category == "agent-prompts" or category == "agent-templates":
            cat_info = TEMPLATE_REGISTRY.get_category(category)
            if cat_info:
                base_path = cat_info.resolve_target(ai_assistant)
                if base_path:
                    return f"{base_path}/{filename}"
                return None

        return None

    def _should_skip_file_update(self, file_path: str, project_path: Path) -> bool:
        """Determine if a file should be skipped during updates."""
        if self._is_context_file(file_path, project_path):
            return True

        return file_path.startswith(f"{CONSTANTS.DIRECTORY.SPECIFY_MEMORY_DIR}/")

    def _is_context_file(self, file_path: str, project_path: Path) -> bool:
        """Check if a file is a context file."""
        _ = project_path

        assistants = get_all_assistants()
        for assistant in assistants:
            if file_path == assistant.config.context_file.file:
                return True
        return False

    def _get_file_category(self, file_path: str) -> str:
        """Get category for a project file."""
        if file_path.startswith(f"{CONSTANTS.DIRECTORY.SPECIFY_DIR}/"):
            if "scripts" in file_path:
                return "scripts"
            elif "memory" in file_path:
                return "memory"
            return "config"
        elif file_path.startswith("."):
            return "assistant"
        elif "/" not in file_path:
            return "root"
        else:
            return "other"

    # Additional methods to maintain compatibility with the existing interface

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
                    target = self._get_ai_folder_mapping(context.ai_assistant)
                    logging.debug(f"Commands target: {target}")
                elif mapping.source == "context":
                    target = self._get_ai_context_folder_mapping(context.ai_assistant)
                    logging.debug(f"Context target: {target}")
                else:
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

                    target_path.mkdir(parents=True, exist_ok=True)

                    if mapping.render:
                        self._render_templates_from_path(
                            source_path,
                            target_path,
                            context,
                            mapping.executable_extensions,
                            result,
                            verbose,
                            mapping.source,
                        )
                    else:
                        self._copy_templates_from_path(
                            source_path, target_path, result, verbose
                        )
                else:
                    source_traversable = self._template_root.joinpath(mapping.source)
                    target_path.mkdir(parents=True, exist_ok=True)

                    if mapping.render:
                        self._render_templates_from_traversable(
                            source_traversable,
                            target_path,
                            context,
                            mapping.executable_extensions,
                            result,
                            verbose,
                            mapping.source,
                        )
                    else:
                        self._copy_templates_from_traversable(
                            source_traversable,
                            target_path,
                            result,
                            verbose,
                            context,
                            mapping.source,
                        )

            except Exception as e:
                error_msg = f"Error processing {mapping.source}: {str(e)}"
                result.errors.append(error_msg)
                if verbose:
                    self._console.print(f"[red]Error:[/red] {error_msg}")

        return result

    def _get_ai_folder_mapping(self, ai_assistant: str) -> str:
        """Get AI-specific folder structure"""
        return self._file_operations.get_ai_folder_mapping(ai_assistant)

    def _get_ai_context_folder_mapping(self, ai_assistant: str) -> str:
        """Get AI-specific context file directory"""
        return self._file_operations.get_ai_context_folder_mapping(ai_assistant)

    def _render_templates_from_traversable(
        self,
        source_traversable,
        target_path: Path,
        context: TemplateContext,
        executable_extensions: List[str],
        result: RenderResult,
        verbose: bool = False,
        category: str = "",
    ) -> None:
        """Render .j2 templates from a Traversable resource"""
        self._renderer.render_templates_from_traversable(
            source_traversable,
            target_path,
            context,
            executable_extensions,
            result,
            verbose,
            category,
            self.skip_patterns,
            self._determine_output_filename,
        )

    def _copy_templates_from_traversable(
        self,
        source_traversable,
        target_path: Path,
        result: RenderResult,
        verbose: bool = False,
        context: Optional[TemplateContext] = None,
        category: str = "",
    ) -> None:
        """Copy templates as-is from a Traversable resource"""
        self._renderer.copy_templates_from_traversable(
            source_traversable,
            target_path,
            result,
            verbose,
            context,
            category,
            self.skip_patterns,
        )

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
        self._renderer.render_templates_from_path(
            source_path,
            target_path,
            context,
            executable_extensions,
            result,
            verbose,
            category,
        )

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

    def _determine_output_filename(
        self, template_name: str, ai_assistant: str, category: str
    ) -> str:
        """Determine output filename based on template, assistant, and category."""
        return self._file_operations.determine_output_filename(
            template_name, ai_assistant, category
        )

    def render_templates(
        self,
        templates_path: Path,
        destination_path: Path,
        ai_assistants: List[str],
        project_name: str,
        branch_pattern: str,
        selected_agents: Optional[List[str]] = None,
    ) -> RenderResult:
        """Render templates from a given path for multiple AI assistants"""
        from specify_cli.services.project_manager import ProjectManager

        _ = branch_pattern

        manager = ProjectManager()

        original_filesystem_root = self._filesystem_root
        original_use_filesystem = self._use_filesystem

        all_errors = []

        try:
            self._filesystem_root = templates_path
            self._use_filesystem = True

            for ai_assistant in ai_assistants:
                context = TemplateContext(
                    project_name=project_name,
                    ai_assistant=ai_assistant,
                    project_path=destination_path,
                    branch_naming_config=BranchNamingConfig(),
                    selected_agents=selected_agents or [],
                )

                # Filter agent-specific templates if selected_agents provided
                if selected_agents:
                    folder_mappings = [
                        mapping
                        for mapping in manager._get_default_folder_mappings(
                            ai_assistant
                        )
                        if mapping.source not in ["agent-prompts", "agent-templates"]
                        or any(agent in mapping.source for agent in selected_agents)
                    ]
                else:
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
            self._filesystem_root = original_filesystem_root
            self._use_filesystem = original_use_filesystem

        return RenderResult(errors=all_errors)


def get_template_service() -> JinjaTemplateService:
    """Factory function to create a JinjaTemplateService instance"""
    return JinjaTemplateService()

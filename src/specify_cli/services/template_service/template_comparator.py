"""
Template Comparison Service - focused on template difference detection and comparison.

This service handles:
- Template content comparison
- Change detection between template versions
- Diff generation and analysis
- Update recommendation logic
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment

from specify_cli.core.constants import CONSTANTS
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.project import TemplateContext
from specify_cli.services.template_registry import TEMPLATE_REGISTRY

from .models import TemplateChange, TemplateChangeType, TemplateDiff

logger = logging.getLogger(__name__)


class TemplateComparator:
    """Service focused on template comparison and change detection."""

    def __init__(self):
        """Initialize template comparator."""
        pass

    def compare_template_content(
        self,
        template_name: str,
        old_content: str,
        new_content: str,
        category: Optional[str] = None,
    ) -> TemplateChange:
        """Compare two versions of template content.

        Args:
            template_name: Name of the template
            old_content: Original template content
            new_content: New template content
            category: Template category

        Returns:
            TemplateChange representing the differences
        """
        if old_content == new_content:
            return TemplateChange(
                template_name=template_name,
                change_type=TemplateChangeType.UNCHANGED,
                old_content=old_content,
                new_content=new_content,
                category=category,
            )

        change = TemplateChange(
            template_name=template_name,
            change_type=TemplateChangeType.MODIFIED,
            old_content=old_content,
            new_content=new_content,
            category=category,
        )
        change.calculate_line_changes()
        return change

    def compare_template_sets(
        self,
        old_templates: Dict[str, str],
        new_templates: Dict[str, str],
        categories: Optional[Dict[str, str]] = None,
    ) -> TemplateDiff:
        """Compare two sets of templates.

        Args:
            old_templates: Dictionary of old template name -> content
            new_templates: Dictionary of new template name -> content
            categories: Optional mapping of template name -> category

        Returns:
            TemplateDiff with all detected changes
        """
        changes = []
        categories = categories or {}

        all_template_names = set(old_templates.keys()) | set(new_templates.keys())

        for template_name in all_template_names:
            old_content = old_templates.get(template_name)
            new_content = new_templates.get(template_name)
            category = categories.get(template_name)

            if old_content is None and new_content is not None:
                # Template was added
                change = TemplateChange(
                    template_name=template_name,
                    change_type=TemplateChangeType.ADDED,
                    new_content=new_content,
                    category=category,
                )
            elif old_content is not None and new_content is None:
                # Template was deleted
                change = TemplateChange(
                    template_name=template_name,
                    change_type=TemplateChangeType.DELETED,
                    old_content=old_content,
                    category=category,
                )
            else:
                # Template might be modified (both contents exist)
                # Type narrowing: if we're here, both are not None
                assert old_content is not None and new_content is not None
                change = self.compare_template_content(
                    template_name, old_content, new_content, category
                )

            changes.append(change)

        return TemplateDiff(changes=changes)

    def compare_template_directories(
        self, old_dir: Path, new_dir: Path, file_extension: str = ".j2"
    ) -> TemplateDiff:
        """Compare templates in two directories.

        Args:
            old_dir: Directory with old templates
            new_dir: Directory with new templates
            file_extension: File extension to filter templates

        Returns:
            TemplateDiff with detected changes
        """
        old_templates = self._load_templates_from_directory(old_dir, file_extension)
        new_templates = self._load_templates_from_directory(new_dir, file_extension)

        # Generate categories based on directory structure
        categories = {}
        for template_name in old_templates.keys() | new_templates.keys():
            categories[template_name] = self._determine_category_from_path(
                template_name, old_dir, new_dir
            )

        return self.compare_template_sets(old_templates, new_templates, categories)

    def generate_change_summary(self, diff: TemplateDiff) -> str:
        """Generate a human-readable summary of changes.

        Args:
            diff: Template diff to summarize

        Returns:
            Summary string
        """
        if not diff.has_changes:
            return "No changes detected."

        summary_lines = []

        if diff.added_count > 0:
            summary_lines.append(f"Added: {diff.added_count} templates")

        if diff.modified_count > 0:
            summary_lines.append(f"Modified: {diff.modified_count} templates")

        if diff.deleted_count > 0:
            summary_lines.append(f"Deleted: {diff.deleted_count} templates")

        # Add detailed breakdown
        for change in diff.changes:
            if change.change_type != TemplateChangeType.UNCHANGED:
                detail = f"  - {change.template_name} ({change.change_type.value})"
                if change.lines_added > 0 or change.lines_removed > 0:
                    detail += f" [+{change.lines_added}/-{change.lines_removed}]"
                summary_lines.append(detail)

        return "\n".join(summary_lines)

    def should_update_template(self, change: TemplateChange) -> bool:
        """Determine if a template should be updated.

        Args:
            change: Template change to evaluate

        Returns:
            True if template should be updated
        """
        # Skip files that should not be updated
        if change.should_skip:
            return False

        # Always update additions and modifications, don't update deletions by default
        return change.change_type in [
            TemplateChangeType.ADDED,
            TemplateChangeType.MODIFIED,
        ]

    def _load_templates_from_directory(
        self, directory: Path, file_extension: str
    ) -> Dict[str, str]:
        """Load all templates from a directory.

        Args:
            directory: Directory to load from
            file_extension: File extension filter

        Returns:
            Dictionary of template name -> content
        """
        templates = {}

        if not directory.exists():
            return templates

        try:
            for template_file in directory.rglob(f"*{file_extension}"):
                if template_file.is_file():
                    try:
                        content = template_file.read_text(encoding="utf-8")
                        # Use relative path as template name
                        relative_path = template_file.relative_to(directory)
                        templates[str(relative_path)] = content
                    except Exception as e:
                        logger.warning(f"Failed to read template {template_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to load templates from {directory}: {e}")

        return templates

    def _determine_category_from_path(
        self, template_name: str, _old_dir: Path, _new_dir: Path
    ) -> str:
        """Determine template category from its path.

        Args:
            template_name: Name of the template
            old_dir: Old directory path
            new_dir: New directory path

        Returns:
            Template category
        """
        # Simple category determination based on path components
        path_parts = Path(template_name).parts
        if len(path_parts) > 1:
            return path_parts[0]  # Use first directory as category
        return "unknown"

    def get_builtin_template_contents(self) -> dict[str, str]:
        """Get contents of all built-in templates.

        Returns:
            Dictionary mapping template path -> content
        """
        templates = {}
        try:
            import importlib.resources

            import specify_cli.templates as templates_pkg

            categories = TEMPLATE_REGISTRY.get_category_names()

            for category in categories:
                try:
                    category_files = importlib.resources.files(templates_pkg) / category
                    if category_files.is_dir():
                        for file_path in category_files.iterdir():
                            if file_path.is_file() and file_path.name.endswith(
                                CONSTANTS.FILE.TEMPLATE_J2_EXTENSION
                            ):
                                content = file_path.read_text(encoding="utf-8")
                                template_key = f"{category}/{file_path.name}"
                                templates[template_key] = content
                except Exception:
                    continue
        except Exception:
            pass

        return templates

    def get_directory_template_contents(self, template_dir: Path) -> dict[str, str]:
        """Get contents of all templates in a directory.

        Args:
            template_dir: Directory containing templates

        Returns:
            Dictionary mapping template path -> content
        """
        templates = {}

        if not template_dir.exists() or not template_dir.is_dir():
            return templates

        try:
            for template_file in template_dir.rglob(
                f"*{CONSTANTS.FILE.TEMPLATE_J2_EXTENSION}"
            ):
                if any(
                    template_file.match(pattern)
                    for pattern in TEMPLATE_REGISTRY.get_skip_patterns()
                ):
                    continue

                try:
                    content = template_file.read_text(encoding="utf-8")
                    relative_path = template_file.relative_to(template_dir)
                    templates[str(relative_path)] = content
                except Exception:
                    continue
        except Exception:
            pass

        return templates

    def filter_templates_by_agents(
        self, templates: dict[str, str], selected_agents: List[str]
    ) -> dict[str, str]:
        """Filter templates based on selected agents.

        Args:
            templates: Dictionary of template path -> content
            selected_agents: List of agent names to include

        Returns:
            Filtered dictionary of template path -> content
        """
        filtered = {}
        utility_templates = ["context", "generic-agent"]

        for template_key, content in templates.items():
            if "/" in template_key:
                category, filename = template_key.split("/", 1)

                if category in ["agent-prompts", "agent-templates"]:
                    agent_name = filename.replace(".md.j2", "")
                    if agent_name in selected_agents or agent_name in utility_templates:
                        filtered[template_key] = content
                else:
                    filtered[template_key] = content
            else:
                filtered[template_key] = content

        return filtered

    def render_templates_for_comparison(
        self,
        templates: dict[str, str],
        project_path: Path,
        ai_assistants: list[str],
        prepare_context_callback=None,
    ) -> dict[str, str]:
        """Render templates to get final file contents for comparison.

        Args:
            templates: Dictionary of template path -> content
            project_path: Path to project root
            ai_assistants: List of AI assistant names
            prepare_context_callback: Optional callback to prepare context

        Returns:
            Dictionary mapping output path -> rendered content
        """
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

                        # Use callback if provided, otherwise use basic dict
                        if prepare_context_callback:
                            render_context = prepare_context_callback(context)
                        else:
                            render_context = (
                                context.to_dict()
                                if hasattr(context, "to_dict")
                                else context.__dict__
                            )

                        rendered_content = template.render(**render_context)
                    else:
                        rendered_content = template_content

                    # For comparison, we need to determine output path
                    # This would be passed from the calling service
                    rendered_files[template_path] = rendered_content

                except Exception:
                    continue

        return rendered_files

    def create_comparison_context(
        self, project_path: Path, ai_assistant: str
    ) -> TemplateContext:
        """Create a basic template context for comparison rendering.

        Args:
            project_path: Path to project root
            ai_assistant: AI assistant name

        Returns:
            Template context for comparison
        """
        return TemplateContext(
            project_name=project_path.name,
            ai_assistant=ai_assistant,
            project_path=project_path,
            branch_naming_config=BranchNamingConfig(),
        )

    def _create_comparison_context(
        self, project_path: Path, ai_assistant: str
    ) -> TemplateContext:
        """Create a basic template context for comparison rendering.

        Args:
            project_path: Path to project root
            ai_assistant: AI assistant name

        Returns:
            Template context for comparison
        """
        return self.create_comparison_context(project_path, ai_assistant)

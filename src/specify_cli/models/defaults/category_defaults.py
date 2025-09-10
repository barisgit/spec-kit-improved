"""
Category mapping defaults for SpecifyX template system

This module provides type-safe category configurations that eliminate hardcoding
of template categories, their sources, targets, and rendering behavior.
"""

from dataclasses import dataclass, field
from typing import Final, List


@dataclass(frozen=True)
class CategoryMapping:
    """Single category configuration for template processing"""

    name: str  # Category name (e.g., "commands", "scripts")
    source: str  # Source directory in template package
    target_pattern: str  # Target pattern with variables (e.g., "{ai_dir}/commands")
    render_templates: bool  # Whether to render .j2 files or copy as-is
    is_ai_specific: bool  # Whether this category uses AI-specific directories
    description: str = ""

    def __post_init__(self):
        """Validate category mapping"""
        if not self.name or not self.source or not self.target_pattern:
            raise ValueError("Name, source, and target_pattern must be non-empty")

    def resolve_target(self, ai_assistant: str, project_name: str = "") -> str:
        """Resolve target path with variable substitution

        Args:
            ai_assistant: AI assistant name
            project_name: Project name (if needed in pattern)

        Returns:
            Resolved target path
        """
        variables = {
            "ai_dir": f".{ai_assistant}",
            "project_name": project_name,
            "category": self.name,
        }

        return self.target_pattern.format(**variables)


@dataclass(frozen=True)
class FolderMappingResult:
    """Type-safe result for folder mapping operations"""

    category: str
    source_path: str
    target_path: str
    should_render: bool
    is_ai_specific: bool


@dataclass(frozen=True)
class CategoryDefaults:
    """Developer defaults for template categories - packaged with SpecifyX

    This provides centralized, type-safe category configurations that eliminate
    hardcoding throughout the template processing system.
    """

    # Template category configurations
    CATEGORIES: Final[List[CategoryMapping]] = field(
        default_factory=lambda: [
            CategoryMapping(
                name="commands",
                source="commands",
                target_pattern="{ai_dir}/commands",
                render_templates=True,
                is_ai_specific=True,
                description="AI assistant command templates",
            ),
            CategoryMapping(
                name="scripts",
                source="scripts",
                target_pattern=".specify/scripts",
                render_templates=True,
                is_ai_specific=False,
                description="Python utility scripts",
            ),
            CategoryMapping(
                name="memory",
                source="memory",
                target_pattern=".specify/memory",
                render_templates=True,
                is_ai_specific=False,
                description="AI assistant memory/constitution files",
            ),
            CategoryMapping(
                name="runtime_templates",
                source="runtime_templates",
                target_pattern=".specify/templates",
                render_templates=False,  # These are templates for runtime use, not rendered
                is_ai_specific=False,
                description="Runtime template files for project use",
            ),
        ]
    )

    def get_category_by_name(self, name: str) -> CategoryMapping:
        """Get category configuration by name

        Args:
            name: Category name

        Returns:
            CategoryMapping for the specified category

        Raises:
            ValueError: If category not found
        """
        for category in self.CATEGORIES:
            if category.name == name:
                return category
        raise ValueError(f"Unknown category: {name}")

    def get_folder_mappings(
        self, ai_assistant: str, project_name: str = ""
    ) -> List[FolderMappingResult]:
        """Get all folder mappings for the given AI assistant

        Args:
            ai_assistant: AI assistant name
            project_name: Project name (optional)

        Returns:
            List of FolderMappingResult objects
        """
        results = []
        for category in self.CATEGORIES:
            result = FolderMappingResult(
                category=category.name,
                source_path=category.source,
                target_path=category.resolve_target(ai_assistant, project_name),
                should_render=category.render_templates,
                is_ai_specific=category.is_ai_specific,
            )
            results.append(result)

        return results

    def get_ai_specific_categories(self) -> List[str]:
        """Get list of categories that are AI-specific

        Returns:
            List of AI-specific category names
        """
        return [cat.name for cat in self.CATEGORIES if cat.is_ai_specific]

    def get_renderable_categories(self) -> List[str]:
        """Get list of categories that should render templates

        Returns:
            List of renderable category names
        """
        return [cat.name for cat in self.CATEGORIES if cat.render_templates]

    def should_render_category(self, category_name: str) -> bool:
        """Check if category should render templates

        Args:
            category_name: Name of category to check

        Returns:
            True if templates should be rendered, False if copied as-is
        """
        try:
            category = self.get_category_by_name(category_name)
            return category.render_templates
        except ValueError:
            # Default to rendering for unknown categories
            return True

    def resolve_target_for_category(
        self, category_name: str, ai_assistant: str, project_name: str = ""
    ) -> str:
        """Resolve target path for specific category and AI assistant

        Args:
            category_name: Category name
            ai_assistant: AI assistant name
            project_name: Project name (optional)

        Returns:
            Resolved target path

        Raises:
            ValueError: If category not found
        """
        category = self.get_category_by_name(category_name)
        return category.resolve_target(ai_assistant, project_name)


# Module-level singleton for easy access
CATEGORY_DEFAULTS = CategoryDefaults()

"""
Template Discovery Service - focused on finding and categorizing templates.

This service handles:
- Template discovery from various sources
- Template categorization and classification
- Template metadata extraction
- Template filtering and selection
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from specify_cli.core.constants import CONSTANTS
from specify_cli.models.template import GranularTemplate, TemplateState
from specify_cli.services.template_registry import TEMPLATE_REGISTRY

logger = logging.getLogger(__name__)


class TemplateDiscovery:
    """Service focused on template discovery and categorization."""

    def __init__(self, skip_patterns: Optional[List[str]] = None):
        """Initialize template discovery service.

        Args:
            skip_patterns: List of file patterns to skip during discovery
        """
        self.skip_patterns = skip_patterns or CONSTANTS.PATTERNS.SKIP_PATTERNS

    def discover_all_templates(
        self, search_paths: List[Path]
    ) -> List[GranularTemplate]:
        """Discover all templates from multiple search paths.

        Args:
            search_paths: List of paths to search for templates

        Returns:
            List of discovered templates
        """
        templates = []

        for search_path in search_paths:
            templates.extend(self.discover_templates_in_path(search_path))

        # Remove duplicates based on name and category
        return self._deduplicate_templates(templates)

    def discover_templates_in_path(self, search_path: Path) -> List[GranularTemplate]:
        """Discover templates in a specific path.

        Args:
            search_path: Path to search for templates

        Returns:
            List of discovered templates
        """
        templates = []

        if not search_path.exists():
            return templates

        try:
            # Search for template files
            for template_file in search_path.rglob(
                f"*{CONSTANTS.FILE.TEMPLATE_J2_EXTENSION}"
            ):
                if self._should_skip_file(template_file):
                    continue

                template = self._create_template_from_file(template_file, search_path)
                if template:
                    templates.append(template)

        except Exception as e:
            logger.error(f"Failed to discover templates in {search_path}: {e}")

        return templates

    def discover_templates_by_category(
        self, search_paths: List[Path], category: str
    ) -> List[GranularTemplate]:
        """Discover templates for a specific category.

        Args:
            search_paths: List of paths to search
            category: Category to filter by

        Returns:
            List of templates in the specified category
        """
        all_templates = self.discover_all_templates(search_paths)
        return [t for t in all_templates if t.category == category]

    def discover_agent_templates(
        self, search_paths: List[Path], selected_agents: Optional[List[str]] = None
    ) -> List[GranularTemplate]:
        """Discover agent-specific templates.

        Args:
            search_paths: List of paths to search
            selected_agents: Optional list of specific agents to include

        Returns:
            List of agent templates
        """
        agent_templates = self.discover_templates_by_category(
            search_paths, "agent-prompts"
        )

        if selected_agents:
            # Filter to only include selected agents
            filtered_templates = []
            for template in agent_templates:
                agent_name = self._extract_agent_name_from_template(template)
                if agent_name in selected_agents:
                    filtered_templates.append(template)
            return filtered_templates

        return agent_templates

    def categorize_template(
        self, template_path: Path, base_path: Optional[Path] = None
    ) -> str:
        """Determine the category of a template based on its path.

        Args:
            template_path: Path to the template file
            base_path: Base path for relative categorization

        Returns:
            Template category
        """
        if base_path:
            try:
                relative_path = template_path.relative_to(base_path)
                path_str = str(relative_path)
            except ValueError:
                path_str = str(template_path)
        else:
            path_str = str(template_path)

        # Check against known categories
        for category in CONSTANTS.PATTERNS.TEMPLATE_CATEGORIES:
            if category in path_str:
                return category

        # Special handling for agent templates
        if template_path.name.endswith(CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX):
            return "agent-prompts"

        # Fallback category determination
        return self._determine_category_from_path_structure(path_str)

    def filter_templates_by_criteria(
        self, templates: List[GranularTemplate], criteria: Dict[str, Any]
    ) -> List[GranularTemplate]:
        """Filter templates based on various criteria.

        Args:
            templates: List of templates to filter
            criteria: Dictionary of filter criteria

        Returns:
            Filtered list of templates
        """
        filtered = templates.copy()

        # Filter by category
        if "category" in criteria:
            category = criteria["category"]
            filtered = [t for t in filtered if t.category == category]

        # Filter by name pattern
        if "name_pattern" in criteria:
            pattern = criteria["name_pattern"]
            filtered = [t for t in filtered if pattern in t.name]

        # Filter by state
        if "state" in criteria:
            state = criteria["state"]
            filtered = [t for t in filtered if t.state == state]

        # Filter by agent selection (for agent templates)
        if "selected_agents" in criteria and criteria["selected_agents"]:
            selected_agents = set(criteria["selected_agents"])
            agent_filtered = []
            for template in filtered:
                if template.category == "agent-prompts":
                    agent_name = self._extract_agent_name_from_template(template)
                    if agent_name in selected_agents:
                        agent_filtered.append(template)
                else:
                    # Include non-agent templates
                    agent_filtered.append(template)
            filtered = agent_filtered

        return filtered

    def group_templates_by_category(
        self, templates: List[GranularTemplate]
    ) -> Dict[str, List[GranularTemplate]]:
        """Group templates by their category.

        Args:
            templates: List of templates to group

        Returns:
            Dictionary mapping category -> list of templates
        """
        groups = {}
        for template in templates:
            category = template.category
            if category not in groups:
                groups[category] = []
            groups[category].append(template)
        return groups

    def get_template_metadata(self, template_path: Path) -> Dict[str, Any]:
        """Extract metadata from a template file.

        Args:
            template_path: Path to the template file

        Returns:
            Dictionary of template metadata
        """
        metadata = {
            "name": template_path.stem,
            "file_path": str(template_path),
            "size": template_path.stat().st_size if template_path.exists() else 0,
            "extension": template_path.suffix,
        }

        # Add category
        metadata["category"] = self.categorize_template(template_path)

        # Add agent name if it's an agent template
        if metadata["category"] == "agent-prompts":
            metadata["agent_name"] = self._extract_agent_name_from_filename(
                template_path.name
            )

        # Add additional metadata from template registry
        try:
            metadata.update(
                self._get_registry_metadata(template_path, metadata["category"])
            )
        except Exception as e:
            logger.debug(f"Failed to get registry metadata for {template_path}: {e}")

        return metadata

    def _create_template_from_file(
        self, template_file: Path, base_path: Optional[Path] = None
    ) -> Optional[GranularTemplate]:
        """Create a GranularTemplate object from a file.

        Args:
            template_file: Path to template file
            base_path: Base path for relative naming

        Returns:
            GranularTemplate object or None if creation failed
        """
        try:
            # Determine template name
            if base_path:
                try:
                    relative_path = template_file.relative_to(base_path)
                    name = str(relative_path.with_suffix(""))  # Remove extension
                except ValueError:
                    name = template_file.stem
            else:
                name = template_file.stem

            # Remove .j2 extension if present
            if name.endswith(".j2"):
                name = name[:-3]

            # Determine category
            category = self.categorize_template(template_file, base_path)

            # Create template object
            template = GranularTemplate(
                name=name,
                template_path=str(template_file),
                category=category,
                state=TemplateState.DISCOVERED,
            )

            return template

        except Exception as e:
            logger.error(f"Failed to create template from {template_file}: {e}")
            return None

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during discovery.

        Args:
            file_path: Path to check

        Returns:
            True if file should be skipped
        """
        return any(file_path.match(pattern) for pattern in self.skip_patterns)

    def _deduplicate_templates(
        self, templates: List[GranularTemplate]
    ) -> List[GranularTemplate]:
        """Remove duplicate templates based on name and category.

        Args:
            templates: List of templates to deduplicate

        Returns:
            List of unique templates
        """
        seen = set()
        unique_templates = []

        for template in templates:
            key = (template.name, template.category)
            if key not in seen:
                seen.add(key)
                unique_templates.append(template)

        return unique_templates

    def _extract_agent_name_from_template(self, template: GranularTemplate) -> str:
        """Extract agent name from a template.

        Args:
            template: Template to extract agent name from

        Returns:
            Agent name
        """
        if template.category == "agent-prompts":
            return self._extract_agent_name_from_filename(
                Path(template.template_path).name
            )
        return ""

    def _extract_agent_name_from_filename(self, filename: str) -> str:
        """Extract agent name from filename.

        Args:
            filename: Template filename

        Returns:
            Agent name
        """
        if filename.endswith(CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX):
            return filename.replace(CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX, "")
        return filename

    def _determine_category_from_path_structure(self, path_str: str) -> str:
        """Determine category from path structure.

        Args:
            path_str: Path string to analyze

        Returns:
            Determined category
        """
        # Check for common path patterns
        if "command" in path_str:
            return "commands"
        elif "script" in path_str:
            return "scripts"
        elif "memory" in path_str:
            return "memory"
        elif "context" in path_str:
            return "context"
        elif "agent" in path_str:
            return "agent-prompts"

        return "unknown"

    def _get_registry_metadata(
        self, template_path: Path, category: str
    ) -> Dict[str, Any]:
        """Get additional metadata from template registry.

        Args:
            template_path: Template file path
            category: Template category

        Returns:
            Additional metadata dictionary
        """
        metadata = {}

        try:
            # Check if template should be executable
            metadata["should_be_executable"] = TEMPLATE_REGISTRY.should_be_executable(
                template_path
            )

            # Check if template should be rendered
            metadata["should_render"] = TEMPLATE_REGISTRY.should_render_category(
                category
            )

        except Exception as e:
            logger.debug(f"Failed to get registry metadata: {e}")

        return metadata

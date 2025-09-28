"""
Agent Name Extractor Service - centralized agent name parsing and extraction.

This service handles:
- Agent name extraction from filenames
- Agent template filename generation
- Agent name validation and normalization
- Agent path pattern matching
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from specify_cli.core.constants import CONSTANTS

logger = logging.getLogger(__name__)


class AgentNameExtractor:
    """Centralized service for agent name extraction and processing."""

    @staticmethod
    def extract_agent_name_from_filename(filename: str) -> Optional[str]:
        """Extract agent name from a template filename.

        Args:
            filename: Template filename (e.g., "code-reviewer.md.j2")

        Returns:
            Agent name or None if not an agent template
        """
        if filename.endswith(CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX):
            return filename.replace(CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX, "")

        # Handle other agent template patterns
        if filename.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
            base_name = filename[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]
            # Check if it looks like an agent name (kebab-case)
            if re.match(CONSTANTS.PATTERNS.AGENT_NAME_PATTERN, base_name):
                return base_name

        return None

    @staticmethod
    def extract_agent_name_from_path(file_path: str) -> Optional[str]:
        """Extract agent name from a file path.

        Args:
            file_path: Full file path

        Returns:
            Agent name or None if not an agent file
        """
        path = Path(file_path)

        # Check if it's in an agent-related directory
        if "agent" in str(path).lower():
            return AgentNameExtractor.extract_agent_name_from_filename(path.name)

        return None

    @staticmethod
    def generate_agent_template_filename(agent_name: str) -> str:
        """Generate template filename for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Template filename
        """
        return f"{agent_name}{CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX}"

    @staticmethod
    def generate_agent_output_filename(agent_name: str) -> str:
        """Generate output filename for a rendered agent template.

        Args:
            agent_name: Name of the agent

        Returns:
            Output filename
        """
        return f"{agent_name}{CONSTANTS.FILE.MARKDOWN_EXTENSION}"

    @staticmethod
    def normalize_agent_name(agent_name: str) -> str:
        """Normalize an agent name to follow conventions.

        Args:
            agent_name: Original agent name

        Returns:
            Normalized agent name
        """
        # Convert to lowercase
        normalized = agent_name.lower()

        # Replace spaces and underscores with hyphens
        normalized = re.sub(r"[_\s]+", "-", normalized)

        # Remove invalid characters
        normalized = re.sub(r"[^a-z0-9-]", "", normalized)

        # Remove leading/trailing hyphens
        normalized = normalized.strip("-")

        # Collapse multiple hyphens
        normalized = re.sub(r"-+", "-", normalized)

        return normalized

    @staticmethod
    def is_valid_agent_name(agent_name: str) -> bool:
        """Check if an agent name is valid.

        Args:
            agent_name: Agent name to validate

        Returns:
            True if agent name is valid
        """
        if not agent_name:
            return False

        return bool(re.match(CONSTANTS.PATTERNS.AGENT_NAME_PATTERN, agent_name))

    @staticmethod
    def extract_multiple_agent_names_from_directory(directory_path: str) -> List[str]:
        """Extract all agent names from templates in a directory.

        Args:
            directory_path: Directory to search

        Returns:
            List of agent names found
        """
        agent_names = []
        directory = Path(directory_path)

        if not directory.exists():
            return agent_names

        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    agent_name = AgentNameExtractor.extract_agent_name_from_filename(
                        file_path.name
                    )
                    if agent_name:
                        agent_names.append(agent_name)

        except Exception as e:
            logger.error(f"Failed to extract agent names from {directory_path}: {e}")

        return sorted(set(agent_names))  # Remove duplicates and sort

    @staticmethod
    def filter_agent_templates_by_names(
        template_files: List[str], selected_agents: List[str]
    ) -> List[str]:
        """Filter template files to only include selected agents.

        Args:
            template_files: List of template filenames
            selected_agents: List of agent names to include

        Returns:
            Filtered list of template files
        """
        if not selected_agents:
            return template_files

        selected_set = set(selected_agents)
        filtered_files = []

        for filename in template_files:
            agent_name = AgentNameExtractor.extract_agent_name_from_filename(filename)
            if agent_name and agent_name in selected_set:
                filtered_files.append(filename)
            elif not agent_name:
                # Include non-agent templates
                filtered_files.append(filename)

        return filtered_files

    @staticmethod
    def get_agent_display_name(agent_name: str) -> str:
        """Convert agent name to a human-readable display name.

        Args:
            agent_name: Agent name in kebab-case

        Returns:
            Human-readable display name
        """
        if not agent_name:
            return ""

        # Replace hyphens with spaces and title case
        display_name = agent_name.replace("-", " ").title()

        # Handle special cases
        special_cases = {
            "Ai": "AI",
            "Api": "API",
            "Url": "URL",
            "Json": "JSON",
            "Xml": "XML",
            "Html": "HTML",
            "Css": "CSS",
            "Js": "JavaScript",
            "Ts": "TypeScript",
            "Sql": "SQL",
            "Db": "Database",
        }

        for old, new in special_cases.items():
            display_name = display_name.replace(old, new)

        return display_name

    @staticmethod
    def get_agent_description_from_filename(filename: str) -> str:
        """Generate a description for an agent based on its filename.

        Args:
            filename: Agent template filename

        Returns:
            Agent description
        """
        agent_name = AgentNameExtractor.extract_agent_name_from_filename(filename)
        if not agent_name:
            return "Unknown agent"

        display_name = AgentNameExtractor.get_agent_display_name(agent_name)
        return f"Agent for {display_name}"

    @staticmethod
    def group_agents_by_category(agent_names: List[str]) -> dict[str, List[str]]:
        """Group agent names by category based on naming patterns.

        Args:
            agent_names: List of agent names

        Returns:
            Dictionary mapping category -> list of agent names
        """
        categories = {
            "code": [],
            "documentation": [],
            "testing": [],
            "deployment": [],
            "analysis": [],
            "utility": [],
            "other": [],
        }

        # Define patterns for categorization
        category_patterns = {
            "code": ["code", "review", "format", "lint", "refactor", "debug"],
            "documentation": ["doc", "docs", "readme", "guide", "spec"],
            "testing": ["test", "qa", "quality", "coverage", "mock"],
            "deployment": ["deploy", "build", "release", "ci", "cd", "pipeline"],
            "analysis": ["analyze", "audit", "metric", "performance", "security"],
            "utility": ["util", "helper", "tool", "convert", "transform"],
        }

        for agent_name in agent_names:
            categorized = False

            for category, patterns in category_patterns.items():
                if any(pattern in agent_name.lower() for pattern in patterns):
                    categories[category].append(agent_name)
                    categorized = True
                    break

            if not categorized:
                categories["other"].append(agent_name)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    @staticmethod
    def suggest_agent_names(base_name: str, existing_agents: List[str]) -> List[str]:
        """Suggest agent names based on a base name, avoiding conflicts.

        Args:
            base_name: Base name to suggest from
            existing_agents: List of existing agent names

        Returns:
            List of suggested agent names
        """
        normalized_base = AgentNameExtractor.normalize_agent_name(base_name)
        suggestions = []
        existing_set = set(existing_agents)

        # Primary suggestion
        if normalized_base not in existing_set:
            suggestions.append(normalized_base)

        # Variations
        variations = [
            f"{normalized_base}-agent",
            f"{normalized_base}-helper",
            f"{normalized_base}-tool",
            f"code-{normalized_base}",
            f"{normalized_base}-reviewer",
            f"{normalized_base}-analyzer",
        ]

        for variation in variations:
            if variation not in existing_set and len(suggestions) < 5:
                suggestions.append(variation)

        # Numbered variations
        counter = 2
        while len(suggestions) < 3:
            numbered = f"{normalized_base}-{counter}"
            if numbered not in existing_set:
                suggestions.append(numbered)
            counter += 1

        return suggestions[:5]  # Return top 5 suggestions

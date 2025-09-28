"""
Path Resolver Service - centralized path resolution logic.

This service handles:
- AI assistant directory resolution
- Template path resolution
- Project structure path mapping
- Category-based path determination
- Context file path resolution
"""

import logging
from pathlib import Path
from typing import List, Optional

from specify_cli.core.constants import CONSTANTS

logger = logging.getLogger(__name__)


class PathResolverService:
    """Centralized service for path resolution operations."""

    @staticmethod
    def resolve_ai_assistant_directory(ai_assistant: str) -> str:
        """Resolve the directory for an AI assistant.

        Args:
            ai_assistant: Name of the AI assistant

        Returns:
            Directory path for the assistant
        """
        return f".{ai_assistant}"

    @staticmethod
    def resolve_ai_commands_directory(ai_assistant: str) -> str:
        """Resolve the commands directory for an AI assistant.

        Args:
            ai_assistant: Name of the AI assistant

        Returns:
            Commands directory path for the assistant
        """
        return f"{PathResolverService.resolve_ai_assistant_directory(ai_assistant)}/commands"

    @staticmethod
    def resolve_ai_agents_directory(ai_assistant: str) -> str:
        """Resolve the agents directory for an AI assistant.

        Args:
            ai_assistant: Name of the AI assistant

        Returns:
            Agents directory path for the assistant
        """
        return (
            f"{PathResolverService.resolve_ai_assistant_directory(ai_assistant)}/agents"
        )

    @staticmethod
    def resolve_category_target_path(
        category: str, ai_assistant: str = "claude", _project_name: str = ""
    ) -> str:
        """Resolve target path for a template category.

        Args:
            category: Template category
            ai_assistant: AI assistant name
            project_name: Project name (if needed)

        Returns:
            Target path for the category
        """
        # Map categories to their target paths
        category_mappings = {
            "commands": PathResolverService.resolve_ai_commands_directory(ai_assistant),
            "scripts": CONSTANTS.DIRECTORY.SPECIFY_SCRIPTS_DIR,
            "memory": CONSTANTS.DIRECTORY.SPECIFY_MEMORY_DIR,
            "runtime_templates": CONSTANTS.DIRECTORY.SPECIFY_TEMPLATES_DIR,
            "context": PathResolverService.resolve_ai_assistant_directory(ai_assistant),
            "agent-prompts": PathResolverService.resolve_ai_agents_directory(
                ai_assistant
            ),
            "agent-templates": CONSTANTS.DIRECTORY.SPECIFY_AGENT_TEMPLATES_DIR,
        }

        return category_mappings.get(
            category, f"{CONSTANTS.DIRECTORY.SPECIFY_DIR}/{category}"
        )

    @staticmethod
    def resolve_template_output_path(
        template_name: str,
        category: str,
        ai_assistant: str = "claude",
        remove_j2_extension: bool = True,
    ) -> str:
        """Resolve the output path for a rendered template.

        Args:
            template_name: Name of the template
            category: Template category
            ai_assistant: AI assistant name
            remove_j2_extension: Whether to remove .j2 extension

        Returns:
            Full output path for the template
        """
        # Get base target directory
        target_dir = PathResolverService.resolve_category_target_path(
            category, ai_assistant
        )

        # Process template name
        filename = template_name
        if remove_j2_extension and filename.endswith(
            CONSTANTS.FILE.TEMPLATE_J2_EXTENSION
        ):
            filename = filename[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]

        return f"{target_dir}/{filename}"

    @staticmethod
    def resolve_agent_template_path(
        agent_name: str, ai_assistant: str = "claude"
    ) -> str:
        """Resolve path for an agent template.

        Args:
            agent_name: Name of the agent
            ai_assistant: AI assistant name

        Returns:
            Path to the agent template
        """
        agents_dir = PathResolverService.resolve_ai_agents_directory(ai_assistant)
        return f"{agents_dir}/{agent_name}{CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX}"

    @staticmethod
    def resolve_context_file_path(ai_assistant: str) -> str:
        """Resolve path for AI assistant context file.

        Args:
            ai_assistant: AI assistant name

        Returns:
            Path to the context file
        """
        # Different assistants have different context file names
        context_files = {
            "claude": "CLAUDE.md",
            "copilot": "COPILOT.md",
            "cursor": "CURSOR.md",
            "gemini": "GEMINI.md",
        }

        filename = context_files.get(ai_assistant, f"{ai_assistant.upper()}.md")
        ai_dir = PathResolverService.resolve_ai_assistant_directory(ai_assistant)

        # Some context files go in project root, others in AI directory
        if ai_assistant == "claude":
            return filename  # CLAUDE.md goes in project root
        else:
            return f"{ai_dir}/{filename}"

    @staticmethod
    def resolve_config_file_path() -> str:
        """Resolve path for the main SpecifyX config file.

        Returns:
            Path to the config file
        """
        return CONSTANTS.DIRECTORY.SPECIFY_CONFIG_FILE

    @staticmethod
    def resolve_project_structure_paths(ai_assistant: str = "claude") -> List[str]:
        """Resolve all directory paths that should exist in a project.

        Args:
            ai_assistant: AI assistant name

        Returns:
            List of directory paths
        """
        paths = [
            CONSTANTS.DIRECTORY.SPECIFY_DIR,
            CONSTANTS.DIRECTORY.SPECIFY_SCRIPTS_DIR,
            CONSTANTS.DIRECTORY.SPECIFY_TEMPLATES_DIR,
            CONSTANTS.DIRECTORY.SPECIFY_MEMORY_DIR,
            CONSTANTS.DIRECTORY.SPECIFY_AGENT_TEMPLATES_DIR,
        ]

        # Add AI-specific directories
        paths.extend(
            [
                PathResolverService.resolve_ai_assistant_directory(ai_assistant),
                PathResolverService.resolve_ai_commands_directory(ai_assistant),
                PathResolverService.resolve_ai_agents_directory(ai_assistant),
            ]
        )

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        return unique_paths

    @staticmethod
    def resolve_relative_template_path(template_path: Path, base_path: Path) -> str:
        """Resolve a relative template path from a base path.

        Args:
            template_path: Absolute template path
            base_path: Base path to make relative from

        Returns:
            Relative path string
        """
        try:
            return str(template_path.relative_to(base_path))
        except ValueError:
            # If can't make relative, return the name
            return template_path.name

    @staticmethod
    def resolve_template_category_from_path(
        template_path: Path, base_path: Optional[Path] = None
    ) -> str:
        """Determine template category from its file path.

        Args:
            template_path: Path to the template
            base_path: Optional base path for relative resolution

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

        # Check for known categories in path
        for category in CONSTANTS.PATTERNS.TEMPLATE_CATEGORIES:
            if category in path_str:
                return category

        # Special handling for agent templates
        if template_path.name.endswith(CONSTANTS.PATTERNS.AGENT_MD_J2_SUFFIX):
            return "agent-prompts"

        # Fallback based on path structure
        return PathResolverService._determine_category_from_structure(path_str)

    @staticmethod
    def resolve_output_filename_for_template(
        template_name: str, category: str, ai_assistant: str = "claude"
    ) -> str:
        """Resolve the output filename for a template.

        Args:
            template_name: Original template name
            category: Template category
            ai_assistant: AI assistant name

        Returns:
            Resolved output filename
        """
        # Remove .j2 extension
        base_name = template_name
        if base_name.endswith(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION):
            base_name = base_name[: -len(CONSTANTS.FILE.TEMPLATE_J2_EXTENSION)]

        # Category-specific filename handling
        if category == "agent-prompts":
            # Agent prompts keep their names but lose .j2
            return base_name

        elif category == "commands":
            # Commands might need assistant-specific naming
            return base_name

        elif category == "context":
            # Context files have specific naming rules
            if ai_assistant == "claude" and "CLAUDE" in base_name.upper():
                return "CLAUDE.md"
            elif "context" in base_name.lower():
                return f"{ai_assistant.upper()}.md"

        # Default: return base name
        return base_name

    @staticmethod
    def is_context_file(file_path: str) -> bool:
        """Check if a file is a context file.

        Args:
            file_path: Path to check

        Returns:
            True if file is a context file
        """
        context_files = ["CLAUDE.md", "COPILOT.md", "CURSOR.md", "GEMINI.md"]
        filename = Path(file_path).name
        return filename in context_files

    @staticmethod
    def should_skip_file_update(file_path: str) -> bool:
        """Check if a file should be skipped during updates.

        Args:
            file_path: Path to check

        Returns:
            True if file should be skipped
        """
        # Skip files in memory directory (user data)
        if file_path.startswith(f"{CONSTANTS.DIRECTORY.SPECIFY_MEMORY_DIR}/"):
            return True

        # Skip context files by default (they contain user customizations)
        return bool(PathResolverService.is_context_file(file_path))

    @staticmethod
    def get_file_category(file_path: str) -> str:
        """Get category for a project file.

        Args:
            file_path: Path to analyze

        Returns:
            File category
        """
        if file_path.startswith(f"{CONSTANTS.DIRECTORY.SPECIFY_DIR}/"):
            if "scripts" in file_path:
                return "scripts"
            elif "memory" in file_path:
                return "memory"
            elif "templates" in file_path:
                return "runtime_templates"
            elif "agent-templates" in file_path:
                return "agent-templates"

        # Check for AI assistant directories
        for ai_assistant in ["claude", "copilot", "cursor", "gemini"]:
            ai_dir = PathResolverService.resolve_ai_assistant_directory(ai_assistant)
            if file_path.startswith(f"{ai_dir}/"):
                if "commands" in file_path:
                    return "commands"
                elif "agents" in file_path:
                    return "agent-prompts"
                else:
                    return "context"

        return "unknown"

    @staticmethod
    def _determine_category_from_structure(path_str: str) -> str:
        """Determine category from path structure analysis.

        Args:
            path_str: Path string to analyze

        Returns:
            Determined category
        """
        # Check for common patterns
        if any(word in path_str.lower() for word in ["command", "cmd"]):
            return "commands"
        elif any(word in path_str.lower() for word in ["script", "scripts"]):
            return "scripts"
        elif any(word in path_str.lower() for word in ["memory", "constitution"]):
            return "memory"
        elif any(word in path_str.lower() for word in ["context", "config"]):
            return "context"
        elif any(word in path_str.lower() for word in ["agent", "agents"]):
            return "agent-prompts"

        return "unknown"

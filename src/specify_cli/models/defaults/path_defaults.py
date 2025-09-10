"""
Path and folder mapping defaults for SpecifyX template system

This unified module provides immutable developer defaults for:
- Template folder mappings (source -> target)
- Path pattern resolution using AI assistant configurations
- Project structure defaults
- Skip patterns for file processing

Replacing complex hardcoded path resolution logic with maintainable configuration
that dynamically uses AI assistant settings.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Final, List, Optional

from .ai_defaults import AI_DEFAULTS
from .category_defaults import CATEGORY_DEFAULTS, FolderMappingResult

# File permission constants
EXECUTABLE_PERMISSIONS = 0o755
REGULAR_FILE_PERMISSIONS = 0o644

# File extension constants
TEMPLATE_EXTENSION = ".j2"
PYTHON_EXTENSION = ".py"
PYTHON_CACHE_EXTENSION = ".pyc"
PYTHON_CACHE_DIR = "__pycache__"


@dataclass(frozen=True)
class ProjectDefaults:
    """Project-level defaults with proper typing"""

    date_format: str
    config_directory: str
    spec_type: str
    default_ai_assistant: str


@dataclass(frozen=True)
class ProjectContextVars:
    """Type-safe project context variables for template rendering"""

    project_name: str
    created_date: str
    ai_assistant: str
    config_directory: str
    spec_type: str


@dataclass(frozen=True)
class PathDefaults:
    """Developer defaults for path resolution and folder mappings - packaged with SpecifyX.

    This provides centralized, immutable configuration that works with AI_DEFAULTS
    to dynamically resolve paths based on the selected AI assistant.
    """

    # Template root - relative path within the package
    TEMPLATE_ROOT: Final[str] = "templates"

    # Template categories that exist in the template package
    TEMPLATE_CATEGORIES: Final[List[str]] = field(
        default_factory=lambda: ["commands", "scripts", "memory", "runtime_templates"]
    )

    # Files/directories to skip during project creation
    SKIP_PATTERNS: Final[List[str]] = field(
        default_factory=lambda: [
            PYTHON_CACHE_DIR,
            f"*{PYTHON_CACHE_EXTENSION}",
            ".DS_Store",
            "*.tmp",
            ".git",
            "__init__.py",  # Template package files
            "*.egg-info",
        ]
    )

    # Basic project structure to always create (AI-independent)
    BASIC_STRUCTURE: Final[List[str]] = field(
        default_factory=lambda: [
            ".specify",
            ".specify/scripts",
            ".specify/templates",
            ".specify/memory",
        ]
    )

    # Project-level defaults (using proper dataclass)
    PROJECT_DEFAULTS: Final[ProjectDefaults] = field(
        default_factory=lambda: ProjectDefaults(
            date_format="%Y-%m-%d",
            config_directory=".specify",
            spec_type="feature",
            default_ai_assistant=AI_DEFAULTS.DEFAULT_ASSISTANT,
        )
    )

    # Extensions that should be made executable (chmod 755)
    EXECUTABLE_EXTENSIONS: Final[List[str]] = field(
        default_factory=lambda: [
            ".py",  # Python scripts
            ".sh",  # Shell scripts (Unix/Linux)
            ".bat",  # Batch scripts (Windows)
            ".ps1",  # PowerShell scripts
        ]
    )

    # Path patterns that should be made executable
    EXECUTABLE_PATTERNS: Final[List[str]] = field(
        default_factory=lambda: [
            "**/scripts/**",  # Anything in scripts directories
            "**/bin/**",  # Anything in bin directories
        ]
    )

    # Filename patterns that should be made executable (based on name content)
    EXECUTABLE_NAME_PATTERNS: Final[List[str]] = field(
        default_factory=lambda: ["run", "start", "stop", "deploy", "build", "test"]
    )

    # File naming conventions
    NAMING_CONVENTIONS: Final[Dict[str, str]] = field(
        default_factory=lambda: {
            "remove_extensions": TEMPLATE_EXTENSION,  # Remove .j2 from template files
            "preserve_structure": "true",  # Keep directory structure
            "normalize_names": "true",  # Normalize file names
        }
    )

    def resolve_target_path(
        self,
        template_path: Path,
        category: str,
        ai_assistant: Optional[str] = None,
    ) -> Path:
        """Resolve target path for template file using AI assistant configuration.

        Args:
            template_path: Path to the template file
            category: Template category (commands, scripts, memory, runtime_templates)
            ai_assistant: Name of the AI assistant (defaults to PROJECT_DEFAULTS)

        Returns:
            Resolved target path for the template file
        """
        if not ai_assistant:
            ai_assistant = self.PROJECT_DEFAULTS.default_ai_assistant

        # Get the target directory from AI_DEFAULTS
        target_dir = AI_DEFAULTS.get_target_path_for_category(ai_assistant, category)

        # Normalize filename (remove .j2 extension)
        filename = self._normalize_filename(template_path.name)

        # Return the complete path
        return Path(target_dir) / filename

    def _normalize_filename(self, filename: str) -> str:
        """Normalize template filename for target.

        Args:
            filename: Original template filename

        Returns:
            Normalized filename with template extensions removed
        """
        # Remove template extension
        if filename.endswith(self.NAMING_CONVENTIONS["remove_extensions"]):
            filename = filename[: -len(self.NAMING_CONVENTIONS["remove_extensions"])]

        return filename

    def get_folder_mappings(
        self, ai_assistant: Optional[str] = None, project_name: str = ""
    ) -> List[FolderMappingResult]:
        """Get all folder mappings for the given AI assistant.

        Args:
            ai_assistant: Name of the AI assistant (defaults to PROJECT_DEFAULTS)
            project_name: Project name (optional)

        Returns:
            List of FolderMappingResult objects with type-safe mapping information
        """
        if not ai_assistant:
            ai_assistant = self.PROJECT_DEFAULTS.default_ai_assistant

        return CATEGORY_DEFAULTS.get_folder_mappings(ai_assistant, project_name)

    def get_project_structure_paths(
        self, ai_assistant: Optional[str] = None
    ) -> List[str]:
        """Get list of directories that should be created for project structure.

        Args:
            ai_assistant: Name of the AI assistant (defaults to PROJECT_DEFAULTS)

        Returns:
            List of directory paths to create
        """
        if not ai_assistant:
            ai_assistant = self.PROJECT_DEFAULTS.default_ai_assistant

        paths = list(self.BASIC_STRUCTURE)  # Start with basic structure

        # Add AI-specific directories from AI_DEFAULTS
        assistant = AI_DEFAULTS.get_assistant_by_name(ai_assistant)
        if assistant:
            # Add base directory
            paths.append(assistant.base_directory)

            # Add commands directory if it's different from base
            if assistant.commands_directory != assistant.base_directory:
                paths.append(assistant.commands_directory)
        else:
            # Fallback for unknown assistants
            paths.extend(
                [
                    f".{ai_assistant}",
                    f".{ai_assistant}/commands",
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

    def get_default_context_vars(
        self, project_name: str = "default"
    ) -> ProjectContextVars:
        """Get default context variables for template rendering.

        Args:
            project_name: Name of the project

        Returns:
            ProjectContextVars object with type-safe context variables
        """
        return ProjectContextVars(
            project_name=project_name,
            created_date=datetime.now().strftime(self.PROJECT_DEFAULTS.date_format),
            ai_assistant=self.PROJECT_DEFAULTS.default_ai_assistant,
            config_directory=self.PROJECT_DEFAULTS.config_directory,
            spec_type=self.PROJECT_DEFAULTS.spec_type,
        )

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during processing.

        Args:
            file_path: Path to check

        Returns:
            True if file should be skipped, False otherwise
        """
        return any(file_path.match(pattern) for pattern in self.SKIP_PATTERNS)

    def should_be_executable(self, file_path: Path) -> bool:
        """Check if a file should be made executable.

        Args:
            file_path: Path to check

        Returns:
            True if file should be executable, False otherwise
        """
        # Check extensions
        if file_path.suffix in self.EXECUTABLE_EXTENSIONS:
            return True

        # Check path patterns
        if any(file_path.match(pattern) for pattern in self.EXECUTABLE_PATTERNS):
            return True

        # Check filename patterns (based on name content)
        filename = file_path.name.lower()
        return any(pattern in filename for pattern in self.EXECUTABLE_NAME_PATTERNS)

    def validate_pattern_variables(
        self, pattern: str, variables: Dict[str, str]
    ) -> bool:
        """Validate that all pattern variables are provided.

        Args:
            pattern: Pattern string with {variable} placeholders
            variables: Dictionary of available variables

        Returns:
            True if all required variables are present
        """
        required_vars = re.findall(r"\{(\w+)\}", pattern)
        return all(var in variables for var in required_vars)


# Module-level singleton for easy access
PATH_DEFAULTS = PathDefaults()

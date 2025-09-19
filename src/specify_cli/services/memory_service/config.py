"""
Memory import configuration management.

This module provides services for loading and managing memory import
configurations with defaults and validation.
"""

from pathlib import Path

import tomli_w

from .types import MemoryCategory, MemoryFilePattern, MemoryImportConfig


class MemoryConfigManager:
    """Manager for memory import configurations."""

    def __init__(self, project_path: Path):
        """
        Initialize configuration manager.

        Args:
            project_path: Path to the project root
        """
        self.project_path = project_path
        self.config_path = project_path / ".specify" / "memory" / "config.toml"

    def load_config(self) -> MemoryImportConfig:
        """
        Load memory import configuration.

        Returns configuration from file if it exists, otherwise returns defaults.

        Returns:
            Memory import configuration
        """
        # For now, return defaults
        # TODO: Implement TOML loading when needed
        return self.get_default_config()

    def get_default_config(self) -> MemoryImportConfig:
        """
        Get the default memory import configuration.

        Returns:
            Default configuration with standard patterns
        """
        return MemoryImportConfig(
            enabled=True,
            extensions=[".md", ".txt"],
            patterns=[
                MemoryFilePattern(
                    filename_pattern="constitution.md",
                    category=MemoryCategory.CONSTITUTION,
                    priority=1,
                ),
                MemoryFilePattern(
                    filename_pattern="constitution.txt",
                    category=MemoryCategory.CONSTITUTION,
                    priority=1,
                ),
                MemoryFilePattern(
                    filename_pattern="principles.md",
                    category=MemoryCategory.PRINCIPLES,
                    priority=2,
                ),
                MemoryFilePattern(
                    filename_pattern="principles.txt",
                    category=MemoryCategory.PRINCIPLES,
                    priority=2,
                ),
                MemoryFilePattern(
                    filename_pattern="guidelines.md",
                    category=MemoryCategory.GUIDELINES,
                    priority=3,
                ),
                MemoryFilePattern(
                    filename_pattern="guidelines.txt",
                    category=MemoryCategory.GUIDELINES,
                    priority=3,
                ),
                MemoryFilePattern(
                    filename_pattern="standards.md",
                    category=MemoryCategory.STANDARDS,
                    priority=4,
                ),
                MemoryFilePattern(
                    filename_pattern="standards.txt",
                    category=MemoryCategory.STANDARDS,
                    priority=4,
                ),
                MemoryFilePattern(
                    filename_pattern="*.md",
                    category=MemoryCategory.DOCUMENTATION,
                    priority=10,
                ),
                MemoryFilePattern(
                    filename_pattern="*.txt",
                    category=MemoryCategory.DOCUMENTATION,
                    priority=10,
                ),
            ],
            max_files=10,
        )

    def save_config(self, config: MemoryImportConfig) -> bool:
        """
        Save memory import configuration to file.

        Args:
            config: Configuration to save

        Returns:
            True if saved successfully
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"memory": config.model_dump()}
            with self.config_path.open("wb") as config_file:
                tomli_w.dump(data, config_file)
            return True
        except (OSError, ValueError):
            return False

    def config_exists(self) -> bool:
        """
        Check if a configuration file exists.

        Returns:
            True if configuration file exists
        """
        return self.config_path.exists()

    def create_default_config_file(self) -> bool:
        """
        Create a default configuration file.

        Returns:
            True if created successfully
        """
        if self.config_exists():
            return True

        default_config = self.get_default_config()
        return self.save_config(default_config)

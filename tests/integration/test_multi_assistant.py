"""
Integration tests for multi-assistant project support.

Tests the ability to have multiple AI assistants in the same project,
configuration management, and template rendering with multiple assistants.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from specify_cli.assistants.injection_points import InjectionPoint
from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
)
from specify_cli.assistants.types import (
    TemplateConfig as AssistantTemplateConfig,
)
from specify_cli.models.config import BranchNamingConfig, ProjectConfig, TemplateConfig
from specify_cli.models.project import (
    ProjectInitOptions,
    TemplateContext,
)
from specify_cli.services import TomlConfigService
from specify_cli.services.project_manager import ProjectManager
from specify_cli.services.template_service import TemplateService


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for testing projects."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def config_service():
    """Create a config service for testing."""
    return TomlConfigService()


@pytest.fixture
def template_service():
    """Create a template service for testing."""
    return TemplateService()


@pytest.fixture
def mock_git_service():
    """Create a mock git service."""
    mock_git = Mock()
    mock_git.init_repository.return_value = True
    mock_git.is_git_repository.return_value = True
    mock_git.create_branch.return_value = True
    mock_git.get_current_branch.return_value = "main"
    return mock_git


@pytest.fixture
def project_manager(config_service, mock_git_service):
    """Create a project manager with mocked dependencies."""
    return ProjectManager(
        config_service=config_service,
        git_service=mock_git_service,
    )


@pytest.fixture
def claude_config():
    """Create a Claude assistant configuration."""
    return AssistantConfig(
        name="claude",
        display_name="Claude Code",
        description="Anthropic's AI assistant with code capabilities",
        base_directory=".claude",
        context_file=ContextFileConfig(
            file="CLAUDE.md", file_format=FileFormat.MARKDOWN
        ),
        command_files=AssistantTemplateConfig(
            directory=".claude/commands", file_format=FileFormat.MARKDOWN
        ),
        agent_files=AssistantTemplateConfig(
            directory=".claude/agents", file_format=FileFormat.MARKDOWN
        ),
    )


@pytest.fixture
def cursor_config():
    """Create a Cursor assistant configuration."""
    return AssistantConfig(
        name="cursor",
        display_name="Cursor IDE",
        description="AI-powered code editor with advanced features",
        base_directory=".cursor",
        context_file=ContextFileConfig(
            file=".cursor/cursor-rules.md", file_format=FileFormat.MARKDOWN
        ),
        command_files=AssistantTemplateConfig(
            directory=".cursor/commands", file_format=FileFormat.MARKDOWN
        ),
        agent_files=AssistantTemplateConfig(
            directory=".cursor/agents", file_format=FileFormat.MARKDOWN
        ),
    )


@pytest.fixture
def gemini_config():
    """Create a Gemini assistant configuration."""
    return AssistantConfig(
        name="gemini",
        display_name="Google Gemini",
        description="Google's advanced AI model for coding assistance",
        base_directory=".gemini",
        context_file=ContextFileConfig(
            file=".gemini/gemini-context.md", file_format=FileFormat.MARKDOWN
        ),
        command_files=AssistantTemplateConfig(
            directory=".gemini/commands", file_format=FileFormat.MARKDOWN
        ),
        agent_files=AssistantTemplateConfig(
            directory=".gemini/agents", file_format=FileFormat.MARKDOWN
        ),
    )


class TestMultiAssistantConfiguration:
    """Test configuration management with multiple assistants."""

    def test_template_config_multiple_assistants(self):
        """Test that TemplateConfig supports multiple AI assistants."""
        config = TemplateConfig(ai_assistants=["claude", "cursor", "gemini"])

        assert len(config.ai_assistants) == 3
        assert "claude" in config.ai_assistants
        assert "cursor" in config.ai_assistants
        assert "gemini" in config.ai_assistants
        assert config.primary_assistant == "claude"

    def test_add_assistant_to_config(self):
        """Test adding an assistant to existing configuration."""
        config = TemplateConfig(ai_assistants=["claude"])
        assert len(config.ai_assistants) == 1

        config.add_assistant("cursor")
        assert len(config.ai_assistants) == 2
        assert "cursor" in config.ai_assistants

        # Adding same assistant again should be idempotent
        config.add_assistant("cursor")
        assert len(config.ai_assistants) == 2

    def test_remove_assistant_from_config(self):
        """Test removing an assistant from configuration."""
        config = TemplateConfig(ai_assistants=["claude", "cursor", "gemini"])
        assert len(config.ai_assistants) == 3

        success = config.remove_assistant("cursor")
        assert success
        assert len(config.ai_assistants) == 2
        assert "cursor" not in config.ai_assistants

        # Removing non-existent assistant should return False
        success = config.remove_assistant("nonexistent")
        assert not success
        assert len(config.ai_assistants) == 2

    def test_has_assistant_check(self):
        """Test checking if configuration has a specific assistant."""
        config = TemplateConfig(ai_assistants=["claude", "cursor"])

        assert config.has_assistant("claude")
        assert config.has_assistant("cursor")
        assert not config.has_assistant("gemini")
        assert not config.has_assistant("nonexistent")

    def test_primary_assistant_logic(self):
        """Test primary assistant selection logic."""
        # Empty list should default to "claude"
        config = TemplateConfig(ai_assistants=[])
        assert config.primary_assistant == "claude"

        # First assistant should be primary
        config = TemplateConfig(ai_assistants=["cursor", "claude", "gemini"])
        assert config.primary_assistant == "cursor"

        config = TemplateConfig(ai_assistants=["gemini"])
        assert config.primary_assistant == "gemini"


class TestMultiAssistantProjectInitialization:
    """Test project initialization with multiple assistants."""

    def test_project_init_with_multiple_assistants(self):
        """Test initializing a project with multiple AI assistants."""
        ProjectInitOptions(
            project_name="multi-assistant-test",
            ai_assistants=["claude", "cursor"],
            use_current_dir=False,
        )

        with (
            patch(
                "specify_cli.assistants.get_all_assistants"
            ) as mock_get_all_assistants,
            patch("specify_cli.assistants.get_assistant") as mock_get_assistant,
        ):
            # Mock assistant providers
            claude_provider = Mock()
            claude_provider.config.name = "claude"
            claude_provider.get_injection_values.return_value = {
                InjectionPoint.COMMAND_PREFIX: "claude ",
                InjectionPoint.SETUP_INSTRUCTIONS: "Install Claude Code CLI and run 'claude auth'",
                InjectionPoint.CONTEXT_FILE_PATH: "CLAUDE.md",
            }

            cursor_provider = Mock()
            cursor_provider.config.name = "cursor"
            cursor_provider.get_injection_values.return_value = {
                InjectionPoint.COMMAND_PREFIX: "cursor ",
                InjectionPoint.SETUP_INSTRUCTIONS: "Open project in Cursor IDE",
                InjectionPoint.CONTEXT_FILE_PATH: ".cursor/cursor-rules.md",
            }

            mock_get_all_assistants.return_value = [claude_provider, cursor_provider]

            def mock_get_assistant_side_effect(name):
                if name == "claude":
                    return claude_provider
                elif name == "cursor":
                    return cursor_provider
                return None

            mock_get_assistant.side_effect = mock_get_assistant_side_effect

            # This test would need the actual template files to work completely
            # For now, we test the configuration creation part
            config = ProjectConfig(
                name="multi-assistant-test",
                template_settings=TemplateConfig(ai_assistants=["claude", "cursor"]),
                branch_naming=BranchNamingConfig(),
            )

            assert len(config.template_settings.ai_assistants) == 2
            assert "claude" in config.template_settings.ai_assistants
            assert "cursor" in config.template_settings.ai_assistants

    def test_single_assistant_backward_compatibility(self):
        """Test that single assistant initialization still works."""
        ProjectInitOptions(
            project_name="single-assistant-test",
            ai_assistants=["claude"],
            use_current_dir=False,
        )

        config = ProjectConfig(
            name="single-assistant-test",
            template_settings=TemplateConfig(ai_assistants=["claude"]),
            branch_naming=BranchNamingConfig(),
        )

        assert len(config.template_settings.ai_assistants) == 1
        assert config.template_settings.ai_assistants[0] == "claude"
        assert config.template_settings.primary_assistant == "claude"

    def test_project_init_options_validation(self):
        """Test validation of project initialization options."""
        # Valid options
        options = ProjectInitOptions(
            project_name="test-project",
            ai_assistants=["claude", "cursor", "gemini"],
        )
        assert len(options.ai_assistants) == 3

        # Empty assistants list should get default
        options = ProjectInitOptions(
            project_name="test-project",
            ai_assistants=[],
        )
        # The default factory should provide at least one assistant
        assert len(options.ai_assistants) >= 1


class TestMultiAssistantTemplateRendering:
    """Test template rendering with multiple assistants."""

    def test_template_context_with_multiple_assistants(self):
        """Test creating template context for multi-assistant setup."""
        context = TemplateContext(
            project_name="multi-test",
            ai_assistant="claude",  # Primary assistant
            branch_naming_config=BranchNamingConfig(),
        )

        # Template context should handle primary assistant
        context_dict = context.to_dict()
        assert context_dict["ai_assistant"] == "claude"

    def test_template_rendering_assistant_specific_content(self):
        """Test that templates render differently for different assistants."""
        # This is a conceptual test - actual template rendering would require template files

        claude_context = TemplateContext(
            project_name="test-project",
            ai_assistant="claude",
            branch_naming_config=BranchNamingConfig(),
        )

        cursor_context = TemplateContext(
            project_name="test-project",
            ai_assistant="cursor",
            branch_naming_config=BranchNamingConfig(),
        )

        # Contexts should be different
        claude_dict = claude_context.to_dict()
        cursor_dict = cursor_context.to_dict()

        assert claude_dict["ai_assistant"] == "claude"
        assert cursor_dict["ai_assistant"] == "cursor"

    @patch("specify_cli.assistants.get_assistant")
    def test_injection_values_for_multiple_assistants(self, mock_get_assistant):
        """Test getting injection values for multiple assistants."""
        # Mock different assistants with different injection values
        claude_provider = Mock()
        claude_provider.get_injection_values.return_value = {
            InjectionPoint.COMMAND_PREFIX: "claude ",
            InjectionPoint.SETUP_INSTRUCTIONS: "Install Claude Code CLI",
            InjectionPoint.CONTEXT_FILE_PATH: "CLAUDE.md",
            InjectionPoint.REVIEW_COMMAND: "claude review --comprehensive",
        }

        cursor_provider = Mock()
        cursor_provider.get_injection_values.return_value = {
            InjectionPoint.COMMAND_PREFIX: "cursor ",
            InjectionPoint.SETUP_INSTRUCTIONS: "Open project in Cursor IDE",
            InjectionPoint.CONTEXT_FILE_PATH: ".cursor/cursor-rules.md",
            InjectionPoint.CUSTOM_COMMANDS: "Cursor AI commands available in IDE",
        }

        def mock_get_assistant_side_effect(name):
            if name == "claude":
                return claude_provider
            elif name == "cursor":
                return cursor_provider
            return None

        mock_get_assistant.side_effect = mock_get_assistant_side_effect

        # Test that different assistants provide different values
        claude_assistant = mock_get_assistant("claude")
        cursor_assistant = mock_get_assistant("cursor")

        claude_values = claude_assistant.get_injection_values()
        cursor_values = cursor_assistant.get_injection_values()

        assert claude_values[InjectionPoint.COMMAND_PREFIX] == "claude "
        assert cursor_values[InjectionPoint.COMMAND_PREFIX] == "cursor "

        assert claude_values[InjectionPoint.CONTEXT_FILE_PATH] == "CLAUDE.md"
        assert (
            cursor_values[InjectionPoint.CONTEXT_FILE_PATH] == ".cursor/cursor-rules.md"
        )

        # Claude has review command, Cursor has custom commands
        assert InjectionPoint.REVIEW_COMMAND in claude_values
        assert InjectionPoint.CUSTOM_COMMANDS in cursor_values
        assert InjectionPoint.CUSTOM_COMMANDS not in claude_values
        assert InjectionPoint.REVIEW_COMMAND not in cursor_values


class TestMultiAssistantConfigPersistence:
    """Test configuration persistence with multiple assistants."""

    def test_save_and_load_multi_assistant_config(
        self, config_service, temp_project_dir
    ):
        """Test saving and loading configuration with multiple assistants."""
        # Create config with multiple assistants
        original_config = ProjectConfig(
            name="multi-assistant-project",
            template_settings=TemplateConfig(
                ai_assistants=["claude", "cursor", "gemini"]
            ),
            branch_naming=BranchNamingConfig(),
        )

        # Save config
        config_service.save_project_config(temp_project_dir, original_config)

        # Load config back
        loaded_config = config_service.load_project_config(temp_project_dir)

        assert loaded_config is not None
        assert loaded_config.name == "multi-assistant-project"
        assert len(loaded_config.template_settings.ai_assistants) == 3
        assert "claude" in loaded_config.template_settings.ai_assistants
        assert "cursor" in loaded_config.template_settings.ai_assistants
        assert "gemini" in loaded_config.template_settings.ai_assistants

    def test_config_backward_compatibility(self, config_service, temp_project_dir):
        """Test that old single-assistant configs are upgraded correctly."""
        # Simulate old config format by creating TOML manually
        config_file = temp_project_dir / ".specify" / "config.toml"
        config_file.parent.mkdir(exist_ok=True)

        # Old format with ai_assistant instead of ai_assistants
        old_config_content = """
[project]
name = "legacy-project"

[project.template_settings]
ai_assistant = "claude"
config_directory = ".specify"
template_cache_enabled = true
"""
        config_file.write_text(old_config_content)

        # Load config - should handle backward compatibility
        loaded_config = config_service.load_project_config(temp_project_dir)

        assert loaded_config is not None
        assert loaded_config.name == "legacy-project"
        assert len(loaded_config.template_settings.ai_assistants) == 1
        assert loaded_config.template_settings.ai_assistants[0] == "claude"

    def test_config_serialization_with_multiple_assistants(self):
        """Test TOML serialization with multiple assistants."""
        config = ProjectConfig(
            name="serialization-test",
            template_settings=TemplateConfig(
                ai_assistants=["claude", "cursor", "gemini"],
                config_directory=".specify",
            ),
            branch_naming=BranchNamingConfig(),
        )

        config_dict = config.to_dict()

        # Check structure
        assert "project" in config_dict
        project_data = config_dict["project"]

        assert "template_settings" in project_data
        template_settings = project_data["template_settings"]

        assert "ai_assistants" in template_settings
        assert template_settings["ai_assistants"] == ["claude", "cursor", "gemini"]

        # Should not contain old ai_assistant field
        assert "ai_assistant" not in template_settings


class TestMultiAssistantDirectoryStructure:
    """Test directory structure creation for multiple assistants."""

    def test_multi_assistant_directory_isolation(
        self, claude_config, cursor_config, gemini_config
    ):
        """Test that multiple assistants have isolated directory structures."""
        configs = [claude_config, cursor_config, gemini_config]

        # Get all paths for each assistant
        all_paths = set()
        for config in configs:
            assistant_paths = config.get_all_paths()

            # Check for conflicts with previously seen paths
            conflicts = all_paths & assistant_paths
            assert len(conflicts) == 0, f"Path conflicts found: {conflicts}"

            all_paths.update(assistant_paths)

        # Verify each assistant has its own base directory
        base_dirs = {config.base_directory for config in configs}
        assert len(base_dirs) == 3  # Should be unique
        assert base_dirs == {".claude", ".cursor", ".gemini"}

    def test_assistant_path_management(self, claude_config):
        """Test path management utilities for assistants."""
        # Test is_path_managed
        assert claude_config.is_path_managed(".claude/commands/test.md")
        assert claude_config.is_path_managed("CLAUDE.md")
        assert not claude_config.is_path_managed(".cursor/commands/test.md")
        assert not claude_config.is_path_managed("random/file.md")

        # Test get_all_paths
        all_paths = claude_config.get_all_paths()
        expected_paths = {
            ".claude",
            "CLAUDE.md",
            ".claude/commands",
            ".claude/agents",
        }
        assert all_paths == expected_paths

    def test_context_file_placement_flexibility(self):
        """Test that context files can be in project root or assistant directory."""
        # Context file in project root (like CLAUDE.md)
        root_config = AssistantConfig(
            name="root_context",
            display_name="Root Context Assistant",
            description="Assistant with context in root",
            base_directory=".root",
            context_file=ContextFileConfig(
                file="ROOT_CONTEXT.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=AssistantTemplateConfig(
                directory=".root/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=AssistantTemplateConfig(
                directory=".root/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        # Context file in assistant directory
        nested_config = AssistantConfig(
            name="nested_context",
            display_name="Nested Context Assistant",
            description="Assistant with context in subdirectory",
            base_directory=".nested",
            context_file=ContextFileConfig(
                file=".nested/nested-context.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=AssistantTemplateConfig(
                directory=".nested/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=AssistantTemplateConfig(
                directory=".nested/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        # Both should be valid
        assert root_config.context_file.file == "ROOT_CONTEXT.md"
        assert nested_config.context_file.file == ".nested/nested-context.md"


class TestMultiAssistantErrorHandling:
    """Test error handling with multiple assistants."""

    def test_invalid_assistant_in_list(self):
        """Test handling of invalid assistant names in configuration."""
        # This should work - configuration allows any string
        config = TemplateConfig(ai_assistants=["claude", "invalid_assistant", "cursor"])

        assert len(config.ai_assistants) == 3
        assert "invalid_assistant" in config.ai_assistants

    def test_empty_assistants_list_handling(self):
        """Test handling of empty assistants list."""
        config = TemplateConfig(ai_assistants=[])

        # Empty list should still work
        assert len(config.ai_assistants) == 0
        assert config.primary_assistant == "claude"  # Default fallback

    def test_duplicate_assistants_in_list(self):
        """Test handling of duplicate assistant names."""
        # Creating config with duplicates
        TemplateConfig(ai_assistants=["claude", "claude", "cursor"])

        # The add_assistant method should handle duplicates
        config_clean = TemplateConfig(ai_assistants=["claude"])
        config_clean.add_assistant("claude")  # Should be idempotent
        config_clean.add_assistant("cursor")

        assert len(config_clean.ai_assistants) == 2
        assert config_clean.ai_assistants.count("claude") == 1

    def test_config_validation_with_multiple_assistants(
        self, config_service, temp_project_dir
    ):
        """Test configuration validation with multiple assistants."""
        # Create a config that might have validation issues
        config = ProjectConfig(
            name="validation-test",
            template_settings=TemplateConfig(
                ai_assistants=["claude", "cursor", "nonexistent"],
            ),
            branch_naming=BranchNamingConfig(),
        )

        # Save and load should work even with unknown assistants
        config_service.save_project_config(temp_project_dir, config)
        loaded_config = config_service.load_project_config(temp_project_dir)

        assert loaded_config is not None
        assert len(loaded_config.template_settings.ai_assistants) == 3
        assert "nonexistent" in loaded_config.template_settings.ai_assistants

"""Test cross-field validation features according to spec task T029."""

import pytest
from pydantic import ValidationError

from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    TemplateConfig,
)
from specify_cli.models.config import ProjectConfig


class TestCrossFieldValidation:
    """Test cross-field validation between related model fields."""

    def test_assistant_config_path_consistency_validation(self):
        """Test that paths are consistent with base directory."""
        # Valid configuration where paths are under base directory
        valid_config = AssistantConfig(
            name="claude",
            display_name="Claude Assistant",
            description="AI assistant by Anthropic",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file=".claude/CLAUDE.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )
        assert valid_config.name == "claude"
        assert valid_config.base_directory == ".claude"

    def test_assistant_config_path_validation_cross_fields(self):
        """Test cross-field validation between base directory and file paths."""
        # Test that commands directory must be under base directory
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="claude",
                display_name="Claude Assistant",
                description="AI assistant by Anthropic",
                base_directory=".claude",
                context_file=ContextFileConfig(
                    file="CLAUDE.md",  # Valid: can be in project root
                    file_format=FileFormat.MARKDOWN,
                ),
                command_files=TemplateConfig(
                    directory=".cursor/commands",  # Invalid: not under base directory
                    file_format=FileFormat.MARKDOWN,
                ),
                agent_files=TemplateConfig(
                    directory=".claude/agents", file_format=FileFormat.MARKDOWN
                ),
            )

        error = exc_info.value
        assert len(error.errors()) > 0
        error_message = str(error)
        assert "commands" in error_message.lower()

    def test_assistant_config_context_file_flexibility(self):
        """Test that context file can be in project root or under base directory."""
        # Context file in project root (valid)
        config1 = AssistantConfig(
            name="claude",
            display_name="Claude Assistant",
            description="AI assistant by Anthropic",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file="CLAUDE.md",  # Project root
                file_format=FileFormat.MARKDOWN,
            ),
            command_files=TemplateConfig(
                directory=".claude/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )
        assert config1.context_file.file == "CLAUDE.md"

        # Context file under base directory (also valid)
        config2 = AssistantConfig(
            name="claude",
            display_name="Claude Assistant",
            description="AI assistant by Anthropic",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file=".claude/CLAUDE.md",  # Under base directory
                file_format=FileFormat.MARKDOWN,
            ),
            command_files=TemplateConfig(
                directory=".claude/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )
        assert config2.context_file.file == ".claude/CLAUDE.md"

    def test_assistant_config_agent_files_validation(self):
        """Test cross-field validation for agent files directory."""
        # Agent files directory must be under base directory
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="claude",
                display_name="Claude Assistant",
                description="AI assistant by Anthropic",
                base_directory=".claude",
                context_file=ContextFileConfig(
                    file="CLAUDE.md", file_format=FileFormat.MARKDOWN
                ),
                command_files=TemplateConfig(
                    directory=".claude/commands", file_format=FileFormat.MARKDOWN
                ),
                agent_files=TemplateConfig(
                    directory="outside/agents",  # Invalid: not under base directory
                    file_format=FileFormat.MARKDOWN,
                ),
            )

        error = exc_info.value
        assert len(error.errors()) > 0
        error_message = str(error)
        assert "agent" in error_message.lower()

    def test_project_config_assistant_consistency(self):
        """Test consistency between AI assistants and their configurations."""
        # Valid project config with assistants
        from specify_cli.models.config import TemplateConfig

        template_config = TemplateConfig(ai_assistants=["claude", "gemini"])
        project_config = ProjectConfig(
            name="test-project", template_settings=template_config
        )

        assert "claude" in project_config.template_settings.ai_assistants
        assert "gemini" in project_config.template_settings.ai_assistants

    def test_assistant_config_name_base_directory_relationship(self):
        """Test relationship between assistant name and base directory."""
        # Common pattern: base directory often relates to name
        claude_config = AssistantConfig(
            name="claude",
            display_name="Claude Assistant",
            description="AI assistant by Anthropic",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file="CLAUDE.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        # Names should match the pattern in base directory (common but not enforced)
        assert "claude" in claude_config.base_directory.lower()

    def test_assistant_config_all_paths_consistency(self):
        """Test get_all_paths method returns consistent results."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Assistant",
            description="AI assistant by Anthropic",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file=".claude/CLAUDE.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        all_paths = config.get_all_paths()

        # Should include base directory and all configured paths
        expected_paths = {
            config.base_directory,
            config.context_file.file,
            config.command_files.directory,
            config.agent_files.directory,
        }
        assert all_paths == expected_paths

        # Should be a set of strings
        assert isinstance(all_paths, set)
        for path in all_paths:
            assert isinstance(path, str)

    def test_assistant_config_is_path_managed_consistency(self):
        """Test is_path_managed method works correctly with configured paths."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Assistant",
            description="AI assistant by Anthropic",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file=".claude/CLAUDE.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        # Should recognize files under managed paths
        assert config.is_path_managed(".claude/commands/specify.md")
        assert config.is_path_managed(".claude/agents/agent.md")
        assert config.is_path_managed(".claude/CLAUDE.md")

        # Should not recognize files outside managed paths
        assert not config.is_path_managed("some/other/path.md")
        assert not config.is_path_managed(".cursor/commands/file.md")

    def test_validation_error_context_preservation(self):
        """Test that cross-field validation errors preserve context for debugging."""
        try:
            AssistantConfig(
                name="claude",
                display_name="Claude Assistant",
                description="AI assistant by Anthropic",
                base_directory=".claude",
                context_file=ContextFileConfig(
                    file="/absolute/path/CLAUDE.md",  # Invalid: not under base or project root
                    file_format=FileFormat.MARKDOWN,
                ),
                command_files=TemplateConfig(
                    directory="not/under/base",  # Invalid: not under base directory
                    file_format=FileFormat.MARKDOWN,
                ),
                agent_files=TemplateConfig(
                    directory=".claude/agents", file_format=FileFormat.MARKDOWN
                ),
            )
        except ValidationError as e:
            # Should have meaningful error message
            error_message = str(e)
            assert len(error_message) > 0
            # Should mention the validation issue
            assert (
                "directory" in error_message.lower() or "path" in error_message.lower()
            )

    def test_field_format_consistency_validation(self):
        """Test that file format fields are consistent across configurations."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Assistant",
            description="AI assistant by Anthropic",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file="CLAUDE.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        # All file formats should be valid enum values
        assert isinstance(config.context_file.file_format, FileFormat)
        assert isinstance(config.command_files.file_format, FileFormat)
        assert isinstance(config.agent_files.file_format, FileFormat)

        # File formats should be consistent with file extensions
        if config.context_file.file.endswith(".md"):
            assert config.context_file.file_format == FileFormat.MARKDOWN

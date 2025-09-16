"""
Contract tests for AssistantConfig Pydantic model validation.

These tests validate the contract for AssistantConfig data structure,
ensuring runtime type safety and proper validation behavior.
"""

import pytest
from pydantic import ValidationError

from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    InjectionPoint,
    TemplateConfig
)


class TestAssistantConfigValidation:
    """Test Pydantic validation rules for AssistantConfig."""

    def test_valid_assistant_config_creation(self):
        """Test creation of valid AssistantConfig instance."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Anthropic's Claude Code AI assistant",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file=".claude/CLAUDE.md",
                file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands",
                file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents",
                file_format=FileFormat.MARKDOWN
            ),
        )

        assert config.name == "claude"
        assert config.display_name == "Claude Code"
        assert config.description == "Anthropic's Claude Code AI assistant"
        assert config.base_directory == ".claude"
        assert config.context_file.file == ".claude/CLAUDE.md"
        assert config.context_file.file_format == FileFormat.MARKDOWN
        assert config.command_files.directory == ".claude/commands"
        assert config.command_files.file_format == FileFormat.MARKDOWN
        assert config.agent_files.directory == ".claude/agents"
        assert config.agent_files.file_format == FileFormat.MARKDOWN

    def test_immutability_enforcement(self):
        """Test that AssistantConfig is immutable after creation."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Test description",
            base_directory=".claude",
            context_file=ContextFileConfig(
                file=".claude/CLAUDE.md",
                file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".claude/commands",
                file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".claude/agents",
                file_format=FileFormat.MARKDOWN
            ),
        )

        with pytest.raises(ValidationError):
            config.name = "modified"

    def test_name_validation_regex(self):
        """Test name field regex validation."""
        # Valid names
        valid_names = ["claude", "gemini", "cursor", "copilot", "claude-3", "gpt_4"]
        for name in valid_names:
            config = AssistantConfig(
                name=name,
                display_name="Test",
                description="Test description",
                base_directory=".test",
                context_file=ContextFileConfig(
                    file=".test/context.md",
                    file_format=FileFormat.MARKDOWN
                ),
                command_files=TemplateConfig(
                    directory=".test/commands",
                    file_format=FileFormat.MARKDOWN
                ),
                agent_files=TemplateConfig(
                    directory=".test/agents",
                    file_format=FileFormat.MARKDOWN
                ),
                memory_directory=".test/memory",
            )
            assert config.name == name

        # Invalid names
        invalid_names = ["Claude", "GEMINI", "123test", "test!", "test space", ""]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                AssistantConfig(
                    name=name,
                    display_name="Test",
                    description="Test description",
                    base_directory=".test",
                    context_file=".test/context.md",
                    commands_directory=".test/commands",
                    memory_directory=".test/memory",
                )

    def test_base_directory_validation_regex(self):
        """Test base_directory field regex validation (must be hidden directory)."""
        # Valid base directories
        valid_dirs = [
            ".claude",
            ".gemini",
            ".cursor",
            ".copilot",
            ".test-dir",
            ".test_dir",
        ]
        for base_dir in valid_dirs:
            config = AssistantConfig(
                name="test",
                display_name="Test",
                description="Test description",
                base_directory=base_dir,
                context_file=f"{base_dir}/context.md",
                commands_directory=f"{base_dir}/commands",
                memory_directory=f"{base_dir}/memory",
            )
            assert config.base_directory == base_dir

        # Invalid base directories (not hidden)
        invalid_dirs = ["claude", "CLAUDE", ".Claude", ".123test", ".", ""]
        for base_dir in invalid_dirs:
            with pytest.raises(ValidationError):
                AssistantConfig(
                    name="test",
                    display_name="Test",
                    description="Test description",
                    base_directory=base_dir,
                    context_file=f"{base_dir}/context.md",
                    commands_directory=f"{base_dir}/commands",
                    memory_directory=f"{base_dir}/memory",
                )

    def test_path_validation_under_base(self):
        """Test that all paths must be under the base directory."""
        base_dir = ".claude"

        # Valid paths under base directory
        valid_config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Test description",
            base_directory=base_dir,
            context_file=".claude/CLAUDE.md",
            commands_directory=".claude/commands",
            memory_directory=".claude/memory",
        )
        assert valid_config.context_file == ".claude/CLAUDE.md"

        # Invalid context file (outside base directory)
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="claude",
                display_name="Claude Code",
                description="Test description",
                base_directory=base_dir,
                context_file=".gemini/CLAUDE.md",  # Wrong base
                commands_directory=".claude/commands",
                memory_directory=".claude/memory",
            )

        # Invalid commands directory (outside base directory)
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="claude",
                display_name="Claude Code",
                description="Test description",
                base_directory=base_dir,
                context_file=".claude/CLAUDE.md",
                commands_directory=".gemini/commands",  # Wrong base
                memory_directory=".claude/memory",
            )

        # Invalid memory directory (outside base directory)
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="claude",
                display_name="Claude Code",
                description="Test description",
                base_directory=base_dir,
                context_file=".claude/CLAUDE.md",
                commands_directory=".claude/commands",
                memory_directory=".gemini/memory",  # Wrong base
            )

    def test_string_length_validation(self):
        """Test string length validation for all fields."""
        base_config = {
            "name": "claude",
            "display_name": "Claude Code",
            "description": "Test description",
            "base_directory": ".claude",
            "context_file": ".claude/CLAUDE.md",
            "commands_directory": ".claude/commands",
            "memory_directory": ".claude/memory",
        }

        # Test name length limits
        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "name": ""})  # Too short

        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "name": "a" * 51})  # Too long

        # Test display_name length limits
        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "display_name": ""})  # Too short

        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "display_name": "a" * 101})  # Too long

        # Test description length limits
        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "description": ""})  # Too short

        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "description": "a" * 201})  # Too long

    def test_whitespace_validation(self):
        """Test whitespace validation for display_name and description."""
        base_config = {
            "name": "claude",
            "display_name": "Claude Code",
            "description": "Test description",
            "base_directory": ".claude",
            "context_file": ".claude/CLAUDE.md",
            "commands_directory": ".claude/commands",
            "memory_directory": ".claude/memory",
        }

        # Whitespace-only display_name should fail
        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "display_name": "   "})

        # Whitespace-only description should fail
        with pytest.raises(ValidationError):
            AssistantConfig(**{**base_config, "description": "   "})

        # Leading/trailing whitespace should be stripped
        config = AssistantConfig(**{**base_config, "display_name": "  Claude Code  "})
        assert config.display_name == "Claude Code"

        config = AssistantConfig(
            **{**base_config, "description": "  Test description  "}
        )
        assert config.description == "Test description"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="claude",
                display_name="Claude Code",
                description="Test description",
                base_directory=".claude",
                context_file=".claude/CLAUDE.md",
                commands_directory=".claude/commands",
                memory_directory=".claude/memory",
                extra_field="not allowed",  # Should fail
            )

    def test_get_all_paths_method(self):
        """Test get_all_paths method returns correct paths."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Test description",
            base_directory=".claude",
            context_file=".claude/CLAUDE.md",
            commands_directory=".claude/commands",
            memory_directory=".claude/memory",
        )

        paths = config.get_all_paths()
        expected_paths = {
            ".claude",
            ".claude/CLAUDE.md",
            ".claude/commands",
            ".claude/memory",
        }
        assert paths == expected_paths

    def test_is_path_managed_method(self):
        """Test is_path_managed method correctly identifies managed paths."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Test description",
            base_directory=".claude",
            context_file=".claude/CLAUDE.md",
            commands_directory=".claude/commands",
            memory_directory=".claude/memory",
        )

        # Managed paths should return True
        assert config.is_path_managed(".claude")
        assert config.is_path_managed(".claude/CLAUDE.md")
        assert config.is_path_managed(".claude/commands")
        assert config.is_path_managed(".claude/commands/test.py")
        assert config.is_path_managed(".claude/memory")
        assert config.is_path_managed(".claude/memory/constitution.md")

        # Non-managed paths should return False
        assert not config.is_path_managed(".gemini")
        assert not config.is_path_managed(".gemini/context.md")
        assert not config.is_path_managed("README.md")
        assert not config.is_path_managed("src/main.py")

        # Invalid input types should return False
        assert not config.is_path_managed(None)
        assert not config.is_path_managed(123)


class TestInjectionPointEnum:
    """Test InjectionPoint enum validation and type safety."""

    def test_injection_point_enum_values(self):
        """Test that all expected injection points exist."""
        expected_points = {
            "assistant_command_prefix",
            "assistant_setup_instructions",
            "assistant_context_file_path",
            "assistant_memory_configuration",
            "assistant_review_command",
            "assistant_documentation_url",
            "assistant_workflow_integration",
            "assistant_custom_commands",
        }

        actual_points = {point.value for point in InjectionPoint}
        assert actual_points == expected_points

    def test_injection_point_string_behavior(self):
        """Test that InjectionPoint behaves as string enum."""
        point = InjectionPoint.COMMAND_PREFIX
        assert isinstance(point, str)
        assert point == "assistant_command_prefix"
        assert point.value == "assistant_command_prefix"
        # Note: str() returns the enum name, not the value for Enum classes

    def test_injection_point_iteration(self):
        """Test that InjectionPoint can be iterated."""
        points = list(InjectionPoint)
        assert len(points) == 8
        assert all(isinstance(point, InjectionPoint) for point in points)

    def test_injection_point_membership(self):
        """Test membership operations with InjectionPoint."""
        assert InjectionPoint.COMMAND_PREFIX in InjectionPoint
        assert InjectionPoint.COMMAND_PREFIX == "assistant_command_prefix"

        # Test with sets
        point_set = {InjectionPoint.COMMAND_PREFIX, InjectionPoint.SETUP_INSTRUCTIONS}
        assert InjectionPoint.COMMAND_PREFIX in point_set
        assert InjectionPoint.CONTEXT_FILE_PATH not in point_set


class TestAssistantConfigJSONSerialization:
    """Test JSON serialization capabilities of AssistantConfig."""

    def test_json_serialization(self):
        """Test that AssistantConfig can be serialized to JSON."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Anthropic's Claude Code AI assistant",
            base_directory=".claude",
            context_file=".claude/CLAUDE.md",
            commands_directory=".claude/commands",
            memory_directory=".claude/memory",
        )

        json_data = config.json()
        assert isinstance(json_data, str)

        # Should be valid JSON
        import json

        parsed = json.loads(json_data)
        assert parsed["name"] == "claude"
        assert parsed["display_name"] == "Claude Code"
        assert parsed["description"] == "Anthropic's Claude Code AI assistant"

    def test_dict_conversion(self):
        """Test that AssistantConfig can be converted to dict."""
        config = AssistantConfig(
            name="claude",
            display_name="Claude Code",
            description="Test description",
            base_directory=".claude",
            context_file=".claude/CLAUDE.md",
            commands_directory=".claude/commands",
            memory_directory=".claude/memory",
        )

        config_dict = config.dict()
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "claude"
        assert config_dict["display_name"] == "Claude Code"

    def test_from_dict_creation(self):
        """Test creating AssistantConfig from dictionary."""
        config_data = {
            "name": "claude",
            "display_name": "Claude Code",
            "description": "Test description",
            "base_directory": ".claude",
            "context_file": ".claude/CLAUDE.md",
            "commands_directory": ".claude/commands",
            "memory_directory": ".claude/memory",
        }

        config = AssistantConfig(**config_data)
        assert config.name == "claude"
        assert config.display_name == "Claude Code"

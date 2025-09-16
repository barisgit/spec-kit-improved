"""
Unit tests for Pydantic validation features in the assistant system.

These tests validate specific Pydantic features and edge cases for
type safety and validation behavior.
"""

import pytest
from pydantic import ValidationError

from specify_cli.assistants.types import (
    ALL_INJECTION_POINTS,
    OPTIONAL_INJECTION_POINTS,
    REQUIRED_INJECTION_POINTS,
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    InjectionPoint,
    InjectionValues,
    TemplateConfig,
)


class TestPydanticValidationBehavior:
    """Test specific Pydantic validation behaviors."""

    def test_field_validation_order(self):
        """Test that field validations happen in correct order."""
        # Test that regex validation happens before custom validators
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="Invalid Name",  # Should fail regex first
                display_name="Test",
                description="Test description",
                base_directory=".test",
                context_file=ContextFileConfig(
                    file=".different/context.md",  # Would fail path validation
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
            )

        # Should get regex error for name, not path validation error
        errors = exc_info.value.errors()
        name_errors = [err for err in errors if err["loc"] == ("name",)]
        assert len(name_errors) > 0
        assert "string does not match regex" in str(name_errors[0]["msg"]).lower()

    def test_validator_with_missing_dependencies(self):
        """Test validators when dependent fields are missing."""
        # When base_directory is missing, path validators should not run
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="test",
                display_name="Test",
                description="Test description",
                # base_directory missing
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
            )

        # Should get missing field error, not path validation error
        errors = exc_info.value.errors()
        base_dir_errors = [err for err in errors if err["loc"] == ("base_directory",)]
        assert len(base_dir_errors) > 0
        assert base_dir_errors[0]["type"] == "value_error.missing"

    def test_frozen_model_behavior(self):
        """Test that frozen=True prevents all modifications."""
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

        # Direct assignment should fail
        with pytest.raises(ValidationError):
            config.name = "modified"

        with pytest.raises(ValidationError):
            config.display_name = "Modified"

        # Dict-style access should also fail
        with pytest.raises(TypeError):
            config.__dict__["name"] = "modified"

    def test_extra_fields_forbidden_behavior(self):
        """Test extra='forbid' behavior in detail."""
        # Extra fields in constructor should fail
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="test",
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
                extra_field="not allowed",
            )

        errors = exc_info.value.errors()
        extra_errors = [err for err in errors if "extra_field" in str(err["loc"])]
        assert len(extra_errors) > 0
        assert "extra fields not permitted" in str(extra_errors[0]["msg"]).lower()

    def test_validation_error_details(self):
        """Test that validation errors provide detailed information."""
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="",  # Too short
                display_name="",  # Too short
                description="",  # Too short
                base_directory="invalid",  # Wrong regex
                context_file=ContextFileConfig(
                    file="",  # Too short
                    file_format=FileFormat.MARKDOWN
                ),
                command_files=TemplateConfig(
                    directory="",  # Too short
                    file_format=FileFormat.MARKDOWN
                ),
                agent_files=TemplateConfig(
                    directory="",  # Too short
                    file_format=FileFormat.MARKDOWN
                ),
            )

        errors = exc_info.value.errors()

        # Should have errors for all fields
        error_fields = {tuple(err["loc"]) for err in errors}
        expected_fields = {
            ("name",),
            ("display_name",),
            ("description",),
            ("base_directory",),
            ("context_file", "file"),
            ("command_files", "directory"),
            ("agent_files", "directory"),
        }

        # All fields should have validation errors
        for field in expected_fields:
            assert field in error_fields

    def test_json_schema_generation(self):
        """Test that JSON schema is properly generated."""
        schema = AssistantConfig.schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # All fields should be in properties
        expected_fields = {
            "name",
            "display_name",
            "description",
            "base_directory",
            "context_file",
            "command_files",
            "agent_files",
        }
        assert set(schema["properties"].keys()) == expected_fields

        # All fields should be required
        assert set(schema["required"]) == expected_fields

        # Check specific field constraints
        name_schema = schema["properties"]["name"]
        assert name_schema["type"] == "string"
        assert name_schema["minLength"] == 1
        assert name_schema["maxLength"] == 50
        assert "pattern" in name_schema  # Regex should be present

    def test_schema_extra_example(self):
        """Test that schema_extra example is included."""
        schema = AssistantConfig.schema()

        assert "example" in schema
        example = schema["example"]

        # Example should be a valid AssistantConfig
        config = AssistantConfig(**example)
        assert config.name == example["name"]
        assert config.display_name == example["display_name"]


class TestInjectionPointValidation:
    """Test InjectionPoint enum validation and type behavior."""

    def test_injection_point_string_enum_behavior(self):
        """Test that InjectionPoint behaves as string enum correctly."""
        point = InjectionPoint.COMMAND_PREFIX

        # Should be string-like
        assert isinstance(point, str)
        assert point == "assistant_command_prefix"
        assert str(point) == "assistant_command_prefix"
        assert repr(point).startswith("<InjectionPoint.")

        # Should work in string operations
        assert point.startswith("assistant_")
        assert point.endswith("_prefix")
        assert "command" in point

    def test_injection_point_enum_membership(self):
        """Test enum membership and iteration."""
        # Test iteration
        all_points = list(InjectionPoint)
        assert len(all_points) == 8

        # Test membership
        assert InjectionPoint.COMMAND_PREFIX in InjectionPoint

        # Test set operations
        point_set = set(InjectionPoint)
        assert len(point_set) == 8
        assert InjectionPoint.COMMAND_PREFIX in point_set

    def test_injection_point_comparison(self):
        """Test comparison operations with InjectionPoint."""
        point1 = InjectionPoint.COMMAND_PREFIX
        point2 = InjectionPoint.COMMAND_PREFIX
        point3 = InjectionPoint.SETUP_INSTRUCTIONS

        # Identity and equality
        assert point1 == point2
        assert point1 is point2  # Enum members are singletons
        assert point1 != point3

        # String comparison
        assert point1 == "assistant_command_prefix"
        assert point1 != "assistant_setup_instructions"

    def test_injection_point_constants_validation(self):
        """Test that injection point constants are correctly defined."""
        # Check that constants are proper sets
        assert isinstance(REQUIRED_INJECTION_POINTS, set)
        assert isinstance(OPTIONAL_INJECTION_POINTS, set)
        assert isinstance(ALL_INJECTION_POINTS, set)

        # Check that all elements are InjectionPoint instances
        for point in REQUIRED_INJECTION_POINTS:
            assert isinstance(point, InjectionPoint)

        for point in OPTIONAL_INJECTION_POINTS:
            assert isinstance(point, InjectionPoint)

        # Check relationships
        assert REQUIRED_INJECTION_POINTS.issubset(ALL_INJECTION_POINTS)
        assert OPTIONAL_INJECTION_POINTS.issubset(ALL_INJECTION_POINTS)
        assert (
            REQUIRED_INJECTION_POINTS.union(OPTIONAL_INJECTION_POINTS)
            == ALL_INJECTION_POINTS
        )
        assert (
            REQUIRED_INJECTION_POINTS.intersection(OPTIONAL_INJECTION_POINTS) == set()
        )

    def test_injection_values_type_alias(self):
        """Test InjectionValues type alias behavior."""
        # Should be Dict[InjectionPoint, str]
        injection_values: InjectionValues = {
            InjectionPoint.COMMAND_PREFIX: "claude:",
            InjectionPoint.SETUP_INSTRUCTIONS: "Setup Claude",
            InjectionPoint.CONTEXT_FILE_PATH: ".claude/CLAUDE.md",
        }

        assert isinstance(injection_values, dict)

        for key, value in injection_values.items():
            assert isinstance(key, InjectionPoint)
            assert isinstance(value, str)


class TestAssistantConfigEdgeCases:
    """Test edge cases and boundary conditions for AssistantConfig."""

    def test_path_validation_edge_cases(self):
        """Test edge cases in path validation."""
        # Test with relative path components
        config = AssistantConfig(
            name="test",
            display_name="Test",
            description="Test description",
            base_directory=".test",
            context_file=".test/../.test/context.md",  # Should normalize but still be valid
            commands_directory=".test/commands",
            memory_directory=".test/memory",
        )
        assert config.context_file == ".test/../.test/context.md"

        # Test with trailing slashes
        config = AssistantConfig(
            name="test",
            display_name="Test",
            description="Test description",
            base_directory=".test",
            context_file=".test/context.md",
            commands_directory=".test/commands/",  # Trailing slash
            memory_directory=".test/memory/",  # Trailing slash
        )
        assert config.commands_directory == ".test/commands/"

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        # Unicode in display name and description should work
        config = AssistantConfig(
            name="test",
            display_name="Test Αssistant 🤖",  # Unicode and emoji
            description="Tést description with spéciål characters",
            base_directory=".test",
            context_file=".test/context.md",
            commands_directory=".test/commands",
            memory_directory=".test/memory",
        )
        assert "🤖" in config.display_name
        assert "spéciål" in config.description

        # Unicode in name should fail (regex restriction)
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="tést",  # Unicode not allowed in name
                display_name="Test",
                description="Test description",
                base_directory=".test",
                context_file=".test/context.md",
                commands_directory=".test/commands",
                memory_directory=".test/memory",
            )

    def test_path_case_sensitivity(self):
        """Test path case sensitivity handling."""
        # Case should be preserved
        config = AssistantConfig(
            name="test",
            display_name="Test",
            description="Test description",
            base_directory=".Test",  # Different case
            context_file=".Test/CONTEXT.md",
            commands_directory=".Test/Commands",
            memory_directory=".Test/Memory",
        )
        assert config.base_directory == ".Test"
        assert config.context_file == ".Test/CONTEXT.md"

    def test_minimum_and_maximum_lengths(self):
        """Test exact minimum and maximum length boundaries."""
        # Test minimum lengths (should work)
        config = AssistantConfig(
            name="a",  # 1 char (minimum)
            display_name="A",  # 1 char (minimum)
            description="A",  # 1 char (minimum)
            base_directory=".a",
            context_file=".a/c",  # Minimum length
            commands_directory=".a/d",  # Minimum length
            memory_directory=".a/m",  # Minimum length
        )
        assert config.name == "a"

        # Test maximum lengths (should work)
        config = AssistantConfig(
            name="a" * 50,  # 50 chars (maximum)
            display_name="A" * 100,  # 100 chars (maximum)
            description="D" * 200,  # 200 chars (maximum)
            base_directory=".test",
            context_file=".test/context.md",
            commands_directory=".test/commands",
            memory_directory=".test/memory",
        )
        assert len(config.name) == 50
        assert len(config.display_name) == 100
        assert len(config.description) == 200

    def test_is_path_managed_edge_cases(self):
        """Test edge cases for is_path_managed method."""
        config = AssistantConfig(
            name="test",
            display_name="Test",
            description="Test description",
            base_directory=".test",
            context_file=".test/context.md",
            commands_directory=".test/commands",
            memory_directory=".test/memory",
        )

        # Test with Path objects
        from pathlib import Path

        assert config.is_path_managed(str(Path(".test/context.md")))

        # Test with empty string
        assert not config.is_path_managed("")

        # Test with None
        assert not config.is_path_managed(None)

        # Test with non-string types
        assert not config.is_path_managed(123)
        assert not config.is_path_managed([".test"])
        assert not config.is_path_managed({".test": "value"})

        # Test case sensitivity
        if config.is_path_managed(".test"):
            # If platform is case-sensitive, different case should not match
            # This behavior may vary by platform
            pass

    def test_get_all_paths_immutability(self):
        """Test that get_all_paths returns immutable results."""
        config = AssistantConfig(
            name="test",
            display_name="Test",
            description="Test description",
            base_directory=".test",
            context_file=".test/context.md",
            commands_directory=".test/commands",
            memory_directory=".test/memory",
        )

        paths1 = config.get_all_paths()
        paths2 = config.get_all_paths()

        # Should return equivalent sets
        assert paths1 == paths2

        # But potentially different objects (implementation detail)
        # Modifying one shouldn't affect the other or the config
        paths1.add("extra_path")
        paths2_after = config.get_all_paths()
        assert "extra_path" not in paths2_after

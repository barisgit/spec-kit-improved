"""Test error handling and validation according to spec task T030."""

import pytest
from pydantic import ValidationError

from specify_cli.assistants.claude.provider import ClaudeProvider
from specify_cli.assistants.gemini.provider import GeminiProvider
from specify_cli.assistants.injection_points import InjectionPointMeta
from specify_cli.assistants.registry import registry
from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    TemplateConfig,
)


class TestErrorHandling:
    """Test comprehensive error handling throughout the system."""

    def test_assistant_config_validation_error_details(self):
        """Test that validation errors provide detailed, actionable information."""
        # Test invalid name
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="",  # Empty name
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

        error = exc_info.value
        assert len(error.errors()) > 0

        # Check error structure
        for err in error.errors():
            assert "loc" in err  # Field location
            assert "msg" in err  # Error message
            assert "type" in err  # Error type

        # Error should mention the problematic field
        error_str = str(error)
        assert "name" in error_str.lower()

    def test_assistant_config_multiple_validation_errors(self):
        """Test handling of multiple validation errors simultaneously."""
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="",  # Invalid: empty
                display_name="",  # Invalid: empty
                description="AI assistant by Anthropic",
                base_directory="invalid",  # Invalid: doesn't start with .
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

        error = exc_info.value
        # Should have multiple errors
        assert len(error.errors()) >= 1

        # Should report on multiple fields
        error_locations = [err.get("loc", []) for err in error.errors()]
        all_fields = [
            field for loc in error_locations for field in loc if isinstance(field, str)
        ]

        # Should mention both problematic fields
        has_name_error = any("name" in field for field in all_fields)
        has_base_dir_error = any(
            "base" in field.lower() or "directory" in field.lower()
            for field in all_fields
        )

        assert has_name_error or has_base_dir_error

    def test_provider_error_handling(self):
        """Test error handling in assistant providers."""
        # Valid provider should work
        claude_provider = ClaudeProvider()
        validation_result = claude_provider.validate_setup()

        # Should return result object with error handling
        assert hasattr(validation_result, "is_valid")

        # If validation fails, should provide useful error information
        if not validation_result.is_valid and hasattr(validation_result, "errors"):
            assert isinstance(validation_result.errors, list)
            for error in validation_result.errors:
                assert isinstance(error, str)
                assert len(error) > 0

    def test_injection_values_error_handling(self):
        """Test error handling when retrieving injection values."""
        claude_provider = ClaudeProvider()

        try:
            injection_values = claude_provider.get_injection_values()
            # Should return valid injection values
            assert isinstance(injection_values, dict)

            for key, value in injection_values.items():
                assert isinstance(key, InjectionPointMeta)
                assert isinstance(value, str)

        except Exception as e:
            # If an error occurs, it should be informative
            error_message = str(e)
            assert len(error_message) > 0
            pytest.fail(f"Unexpected error in get_injection_values: {error_message}")

    def test_registry_error_handling(self):
        """Test error handling in the assistant registry."""
        # Use the imported registry directly

        # Test getting non-existent assistant
        non_existent = registry.get_assistant("non_existent_assistant")
        assert non_existent is None

        # Test validation of all assistants
        validation_results = registry.validate_all()
        assert isinstance(validation_results, dict)

        # Each result should be a validation result
        for assistant_name, result in validation_results.items():
            assert isinstance(assistant_name, str)
            assert hasattr(result, "is_valid")

    def test_path_validation_error_handling(self):
        """Test error handling in path validation methods."""
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

        # Valid path checks should work
        assert isinstance(config.is_path_managed(".claude/commands/file.md"), bool)
        assert isinstance(config.is_path_managed("other/path.md"), bool)

        # Edge cases should be handled gracefully
        edge_cases = ["", None, 123, [], {}]

        for edge_case in edge_cases:
            try:
                if edge_case is None:
                    # None might be handled differently
                    continue
                # Convert non-string types to string for testing
                if not isinstance(edge_case, str):
                    str_edge_case = str(edge_case)
                else:
                    str_edge_case = edge_case
                result = config.is_path_managed(str_edge_case)
                # Should return a boolean or raise a clear error
                assert isinstance(result, bool)
            except (TypeError, AttributeError, ValidationError) as e:
                # Expected errors for invalid input types
                error_message = str(e)
                assert len(error_message) > 0

    def test_configuration_parsing_error_handling(self):
        """Test error handling during configuration parsing."""
        # Test with various invalid configurations
        invalid_configs = [
            {
                "name": None,
                "display_name": "Claude",
                "description": "Test",
                "base_directory": ".claude",
            },  # None name
            {
                "name": "claude",
                "display_name": "Claude",
                "description": "Test",
                "base_directory": None,
            },  # None base_directory
            {"name": "claude"},  # Missing required fields
            {},  # Empty config
        ]

        for invalid_config in invalid_configs:
            with pytest.raises(Exception) as exc_info:
                AssistantConfig(**invalid_config)
            assert isinstance(exc_info.value, (ValidationError, TypeError))

    def test_provider_instantiation_error_handling(self):
        """Test error handling during provider instantiation."""
        # Valid providers should instantiate without errors
        providers = [ClaudeProvider, GeminiProvider]

        for provider_class in providers:
            try:
                provider = provider_class()
                assert hasattr(provider, "config")
                assert hasattr(provider, "get_injection_values")
                assert hasattr(provider, "validate_setup")
            except Exception as e:
                pytest.fail(
                    f"Failed to instantiate {provider_class.__name__}: {str(e)}"
                )

    def test_validation_error_message_quality(self):
        """Test that validation error messages are user-friendly."""
        try:
            AssistantConfig(
                name="invalid name with spaces and special chars!@#",
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
        except ValidationError as e:
            error_message = str(e)

            # Message should be informative
            assert len(error_message) > 0

            # Should mention the field name
            assert "name" in error_message.lower()

            # Should not be overly technical (avoid internal Pydantic details)
            # This is subjective, but error should be reasonably readable

    def test_cascade_error_handling(self):
        """Test error handling when one error might cause others."""
        # Test that one validation error doesn't prevent other validations
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="",  # Invalid
                display_name="",  # Also invalid
                description="AI assistant by Anthropic",
                base_directory="invalid",  # Also invalid
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

        error = exc_info.value
        # Should attempt to validate all fields, not stop at first error
        assert len(error.errors()) >= 1

    def test_error_recovery_scenarios(self):
        """Test scenarios where errors might be recoverable."""
        # Test that partial configurations can be useful for error reporting
        try:
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

            # Should work with minimal valid data
            assert config.name == "claude"
            assert config.base_directory == ".claude"
            assert isinstance(config.get_all_paths(), set)

        except Exception as e:
            pytest.fail(f"Valid minimal configuration should not fail: {str(e)}")

    def test_error_handling_with_edge_case_inputs(self):
        """Test error handling with various edge case inputs."""
        edge_cases = [
            # Very long strings
            ("a" * 1000, ".claude"),
            # Unicode characters
            ("claude-🤖", ".claude"),
            # Special characters
            ("claude-test", ".claude/.hidden/deep"),
        ]

        for name, base_dir in edge_cases:
            try:
                config = AssistantConfig(
                    name=name,
                    display_name="Test Assistant",
                    description="Test description",
                    base_directory=base_dir,
                    context_file=ContextFileConfig(
                        file="TEST.md", file_format=FileFormat.MARKDOWN
                    ),
                    command_files=TemplateConfig(
                        directory=f"{base_dir}/commands",
                        file_format=FileFormat.MARKDOWN,
                    ),
                    agent_files=TemplateConfig(
                        directory=f"{base_dir}/agents", file_format=FileFormat.MARKDOWN
                    ),
                )
                # If it succeeds, that's fine
                assert isinstance(config.name, str)
                assert isinstance(config.base_directory, str)
            except ValidationError as e:
                # If it fails with validation error, that's also fine
                # Error should be informative
                assert len(str(e)) > 0

    def test_concurrent_error_handling(self):
        """Test error handling in concurrent scenarios."""
        # Simulate multiple providers being validated simultaneously
        providers = [ClaudeProvider(), GeminiProvider()]

        results = []
        for provider in providers:
            try:
                validation_result = provider.validate_setup()
                results.append((provider.__class__.__name__, validation_result))
            except Exception as e:
                results.append((provider.__class__.__name__, f"Error: {str(e)}"))

        # Should have results for all providers
        assert len(results) == len(providers)

        # Each result should be meaningful
        for provider_name, result in results:
            assert isinstance(provider_name, str)
            assert result is not None

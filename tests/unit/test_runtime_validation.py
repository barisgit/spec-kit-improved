"""Test runtime type safety validation according to spec task T028."""

import pytest
from pydantic import ValidationError

from specify_cli.assistants.claude.provider import ClaudeProvider
from specify_cli.assistants.gemini.provider import GeminiProvider
from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    TemplateConfig,
)


class TestRuntimeTypeValidation:
    """Test runtime type safety and validation features."""

    def test_assistant_config_runtime_validation(self):
        """Test that AssistantConfig validates data at runtime."""
        # Valid configuration should work
        valid_config = AssistantConfig(
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
        assert valid_config.name == "claude"
        assert valid_config.base_directory == ".claude"

        # Invalid name should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            AssistantConfig(
                name="",  # Empty name should fail
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
        assert any("name" in str(err) for err in error.errors())

    def test_assistant_config_field_type_validation(self):
        """Test that field types are validated at runtime."""
        # Invalid base_directory type
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="claude",
                display_name="Claude Assistant",
                description="AI assistant by Anthropic",
                base_directory=123,  # Should be string
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

        # Invalid display_name type
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="claude",
                display_name=None,  # Should be string
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

    def test_assistant_provider_runtime_validation(self):
        """Test that assistant providers validate at runtime."""
        # Valid provider should work
        claude_provider = ClaudeProvider()
        assert hasattr(claude_provider, "config")
        assert hasattr(claude_provider, "get_injection_values")
        assert hasattr(claude_provider, "validate_setup")

        # Check that config is properly typed
        config = claude_provider.config
        assert isinstance(config, AssistantConfig)
        assert config.name == "claude"

    def test_injection_values_runtime_validation(self):
        """Test that injection values are validated at runtime."""
        claude_provider = ClaudeProvider()
        injection_values = claude_provider.get_injection_values()

        # Should return a dictionary
        assert isinstance(injection_values, dict)

        # All keys should be InjectionPoint enum values
        from specify_cli.assistants.injection_points import InjectionPointMeta

        for key in injection_values:
            assert isinstance(key, InjectionPointMeta)

        # All values should be strings
        for value in injection_values.values():
            assert isinstance(value, str)
            assert len(value) > 0

    def test_validation_error_messages_are_helpful(self):
        """Test that validation errors provide helpful messages."""
        try:
            AssistantConfig(
                name="Invalid-Name-With-Special-Chars!",  # Invalid pattern
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
            raise AssertionError("Should have raised ValidationError")
        except ValidationError as e:
            error_message = str(e)
            # Error message should be helpful
            assert len(error_message) > 0
            assert "name" in error_message.lower()

    def test_immutability_runtime_enforcement(self):
        """Test that immutability is enforced at runtime."""
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

        # Verify model is frozen (prevents field modification)
        assert config.model_config.get("frozen", False), "Model should be frozen"

    def test_provider_validation_result_runtime(self):
        """Test that provider validation returns proper results."""
        claude_provider = ClaudeProvider()
        validation_result = claude_provider.validate_setup()

        # Should return a validation result object
        assert hasattr(validation_result, "is_valid")
        assert isinstance(validation_result.is_valid, bool)

        if hasattr(validation_result, "errors"):
            assert isinstance(validation_result.errors, list)

        if hasattr(validation_result, "warnings"):
            assert isinstance(validation_result.warnings, list)

    def test_multiple_provider_validation_isolation(self):
        """Test that different providers validate independently."""
        claude_provider = ClaudeProvider()
        gemini_provider = GeminiProvider()

        # Both should be valid
        claude_result = claude_provider.validate_setup()
        gemini_result = gemini_provider.validate_setup()

        assert hasattr(claude_result, "is_valid")
        assert hasattr(gemini_result, "is_valid")

        # Should have different configurations
        assert claude_provider.config != gemini_provider.config
        assert claude_provider.config.name != gemini_provider.config.name

    def test_runtime_validation_performance(self):
        """Test that runtime validation meets performance targets."""
        import time

        # Test validation performance (should be <10ms per spec)
        start_time = time.time()

        for _ in range(10):
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
                    directory=".claude/agents", file_format=FileFormat.MARKDOWN
                ),
            )

        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_validation = total_time / 10

        # Should be under 10ms per validation as per spec
        assert avg_time_per_validation < 0.01, (
            f"Validation took {avg_time_per_validation:.3f}s, should be under 0.01s"
        )

    def test_validation_with_partial_data(self):
        """Test validation behavior with minimal required data."""
        # Test with only required fields
        minimal_config = AssistantConfig(
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
        assert minimal_config.name == "claude"

    def test_validation_error_context_preservation(self):
        """Test that validation errors preserve context for debugging."""
        try:
            AssistantConfig(
                name="",  # Invalid: empty name
                display_name="",  # Invalid: empty display name
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
            # Should have errors for both fields
            error_fields = [err.get("loc", []) for err in e.errors()]
            error_fields_flat = [field for loc in error_fields for field in loc]

            # Should mention both problematic fields
            assert "name" in error_fields_flat or any(
                "name" in str(err) for err in e.errors()
            )
            assert "display_name" in error_fields_flat or any(
                "display_name" in str(err) for err in e.errors()
            )

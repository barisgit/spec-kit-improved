"""
Unit tests for the StaticAssistantRegistry business logic.

Tests registry functionality, validation rules, and assistant management.
Focuses on business requirements, not framework behavior.
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from specify_cli.assistants.assistant_registry import StaticAssistantRegistry
from specify_cli.assistants.interfaces import AssistantProvider, ValidationResult
from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    TemplateConfig,
)


@pytest.fixture
def mock_assistant_config():
    """Create a mock assistant configuration."""
    return AssistantConfig(
        name="test_assistant",
        display_name="Test Assistant",
        description="A test AI assistant",
        base_directory=".test",
        context_file=ContextFileConfig(
            file=".test/TEST.md", file_format=FileFormat.MARKDOWN
        ),
        command_files=TemplateConfig(
            directory=".test/commands", file_format=FileFormat.MARKDOWN
        ),
        agent_files=TemplateConfig(
            directory=".test/agents", file_format=FileFormat.MARKDOWN
        ),
    )


@pytest.fixture
def mock_assistant_provider(mock_assistant_config):
    """Create a mock assistant provider."""
    provider = Mock(spec=AssistantProvider)
    provider.config = mock_assistant_config
    provider.get_injection_values.return_value = {
        "assistant_command_prefix": "test ",
        "assistant_setup_instructions": "Install test CLI",
        "assistant_context_file_path": ".test/TEST.md",
    }
    provider.validate_setup.return_value = ValidationResult(is_valid=True)
    provider.get_setup_instructions.return_value = ["Step 1", "Step 2"]
    provider.imports_supported = False
    provider.format_import.return_value = ""
    return provider


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return StaticAssistantRegistry()


class TestAssistantRegistryBusinessRules:
    """Test business rules and validation logic."""

    def test_assistant_registration_validation(self, registry):
        """Test business rules for assistant registration."""
        # Business rule: Must implement AssistantProvider interface
        with pytest.raises(
            TypeError, match="Assistant must implement AssistantProvider"
        ):
            registry.register_assistant("not_an_assistant")

        with pytest.raises(
            TypeError, match="Assistant must implement AssistantProvider"
        ):
            registry.register_assistant(None)

    def test_assistant_name_validation(self, registry):
        """Test business rules for assistant naming."""
        # Test 1: Empty name should raise ValidationError during config creation
        with pytest.raises(ValidationError):
            AssistantConfig(
                name="",  # Empty name violates Pydantic validation
                display_name="Test Assistant",
                description="A test AI assistant",
                base_directory=".test",
                context_file=ContextFileConfig(
                    file=".test/TEST.md", file_format=FileFormat.MARKDOWN
                ),
                command_files=TemplateConfig(
                    directory=".test/commands", file_format=FileFormat.MARKDOWN
                ),
                agent_files=TemplateConfig(
                    directory=".test/agents", file_format=FileFormat.MARKDOWN
                ),
            )

        # Test 2: Valid config creation should work
        valid_config = AssistantConfig(
            name="test_assistant",
            display_name="Test Assistant",
            description="A test AI assistant",
            base_directory=".test",
            context_file=ContextFileConfig(
                file=".test/TEST.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".test/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".test/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        provider = Mock(spec=AssistantProvider)
        provider.config = valid_config

        # Should be able to register valid assistant
        registry.register_assistant(provider)

    def test_duplicate_assistant_prevention(self, registry, mock_assistant_provider):
        """Test business rule preventing duplicate assistant names."""
        registry.register_assistant(mock_assistant_provider)

        # Business rule: Assistant names must be unique
        duplicate_provider = Mock(spec=AssistantProvider)
        duplicate_provider.config = mock_assistant_provider.config

        with pytest.raises(
            ValueError, match="Assistant 'test_assistant' is already registered"
        ):
            registry.register_assistant(duplicate_provider)

    def test_assistant_unregistration_business_logic(
        self, registry, mock_assistant_provider
    ):
        """Test business logic for assistant removal."""
        # Register assistant
        registry.register_assistant(mock_assistant_provider)
        assert registry.is_registered("test_assistant")

        # Business rule: Unregistering existing assistant returns True
        result = registry.unregister_assistant("test_assistant")
        assert result is True
        assert not registry.is_registered("test_assistant")

        # Business rule: Unregistering non-existent assistant returns False
        result = registry.unregister_assistant("nonexistent")
        assert result is False


class TestAssistantValidationWorkflow:
    """Test assistant validation business workflow."""

    def test_validation_success_workflow(self, registry):
        """Test successful validation workflow."""
        config = AssistantConfig(
            name="valid_assistant",
            display_name="Valid Assistant",
            description="A valid assistant",
            base_directory=".valid",
            context_file=ContextFileConfig(
                file=".valid/VALID.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".valid/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".valid/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        provider = Mock(spec=AssistantProvider)
        provider.config = config
        provider.validate_setup.return_value = ValidationResult(is_valid=True)
        provider.get_injection_values.return_value = {}
        provider.get_setup_instructions.return_value = []
        provider.imports_supported = False
        provider.format_import.return_value = ""

        registry.register_assistant(provider)

        # Business requirement: Validation should succeed for valid assistants
        results = registry.validate_all()
        assert results["valid_assistant"].is_valid
        assert not results["valid_assistant"].has_errors

    def test_validation_error_workflow(self, registry):
        """Test validation error handling workflow."""
        config = AssistantConfig(
            name="invalid_assistant",
            display_name="Invalid Assistant",
            description="An invalid assistant",
            base_directory=".invalid",
            context_file=ContextFileConfig(
                file=".invalid/INVALID.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".invalid/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".invalid/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        provider = Mock(spec=AssistantProvider)
        provider.config = config
        provider.validate_setup.return_value = ValidationResult(
            is_valid=False,
            errors=["Configuration file missing"],
            warnings=["API key not configured"],
        )
        provider.get_injection_values.return_value = {}
        provider.get_setup_instructions.return_value = []
        provider.imports_supported = False
        provider.format_import.return_value = ""

        registry.register_assistant(provider)

        # Business requirement: Validation should capture errors
        results = registry.validate_all()
        result = results["invalid_assistant"]
        assert not result.is_valid
        assert result.has_errors
        assert "Configuration file missing" in result.errors
        assert "API key not configured" in result.warnings

    def test_validation_exception_handling(self, registry):
        """Test validation exception handling in business workflow."""
        config = AssistantConfig(
            name="error_assistant",
            display_name="Error Assistant",
            description="An assistant that throws errors",
            base_directory=".error",
            context_file=ContextFileConfig(
                file=".error/ERROR.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".error/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".error/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        provider = Mock(spec=AssistantProvider)
        provider.config = config
        provider.validate_setup.side_effect = ValueError("Validation crashed")
        provider.get_injection_values.return_value = {}
        provider.get_setup_instructions.return_value = []
        provider.imports_supported = False
        provider.format_import.return_value = ""

        registry.register_assistant(provider)

        # Business requirement: Exceptions should be captured as validation errors
        results = registry.validate_all()
        result = results["error_assistant"]
        assert not result.is_valid
        assert result.has_errors
        assert "Validation failed: Validation crashed" in result.errors


class TestAssistantLifecycleManagement:
    """Test complete assistant lifecycle management."""

    def test_assistant_lifecycle_workflow(self, registry):
        """Test complete assistant management lifecycle."""
        config = AssistantConfig(
            name="lifecycle_test",
            display_name="Lifecycle Test Assistant",
            description="Testing lifecycle",
            base_directory=".lifecycle",
            context_file=ContextFileConfig(
                file=".lifecycle/LIFECYCLE.md", file_format=FileFormat.MARKDOWN
            ),
            command_files=TemplateConfig(
                directory=".lifecycle/commands", file_format=FileFormat.MARKDOWN
            ),
            agent_files=TemplateConfig(
                directory=".lifecycle/agents", file_format=FileFormat.MARKDOWN
            ),
        )

        provider = Mock(spec=AssistantProvider)
        provider.config = config
        provider.get_injection_values.return_value = {
            "assistant_command_prefix": "lifecycle ",
            "assistant_setup_instructions": "No setup needed",
            "assistant_context_file_path": ".lifecycle/LIFECYCLE.md",
        }
        provider.validate_setup.return_value = ValidationResult(
            is_valid=True, warnings=["This is a test assistant"]
        )
        provider.get_setup_instructions.return_value = [
            "Install nothing",
            "Configure nothing",
        ]
        provider.imports_supported = True
        provider.format_import.return_value = "@file.md"

        # Business workflow: Register -> Validate -> Retrieve -> Unregister
        registry.register_assistant(provider)
        assert registry.is_registered("lifecycle_test")

        retrieved = registry.get_assistant("lifecycle_test")
        assert retrieved is provider
        assert retrieved.config.name == "lifecycle_test"

        results = registry.validate_all()
        assert results["lifecycle_test"].is_valid
        assert results["lifecycle_test"].has_warnings

        success = registry.unregister_assistant("lifecycle_test")
        assert success
        assert not registry.is_registered("lifecycle_test")

    def test_multi_assistant_management(self, registry):
        """Test managing multiple assistants simultaneously."""
        assistants = []
        for i in range(3):
            config = AssistantConfig(
                name=f"assistant_{i}",
                display_name=f"Assistant {i}",
                description=f"Test assistant {i}",
                base_directory=f".test{i}",
                context_file=ContextFileConfig(
                    file=f".test{i}/TEST{i}.md", file_format=FileFormat.MARKDOWN
                ),
                command_files=TemplateConfig(
                    directory=f".test{i}/commands", file_format=FileFormat.MARKDOWN
                ),
                agent_files=TemplateConfig(
                    directory=f".test{i}/agents", file_format=FileFormat.MARKDOWN
                ),
            )

            provider = Mock(spec=AssistantProvider)
            provider.config = config
            provider.get_injection_values.return_value = {}
            provider.validate_setup.return_value = ValidationResult(is_valid=True)
            provider.get_setup_instructions.return_value = []
            provider.imports_supported = False
            provider.format_import.return_value = ""

            assistants.append(provider)
            registry.register_assistant(provider)

        # Business requirement: All assistants should be accessible
        assert len(registry.get_all_assistants()) == 3
        assert set(registry.list_assistant_names()) == {
            "assistant_0",
            "assistant_1",
            "assistant_2",
        }

        # Business requirement: Each assistant should be retrievable
        for i, assistant in enumerate(assistants):
            retrieved = registry.get_assistant(f"assistant_{i}")
            assert retrieved is assistant

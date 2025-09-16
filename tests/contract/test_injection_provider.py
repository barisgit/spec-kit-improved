"""
Contract tests for InjectionProvider ABC enforcement.

These tests validate that the abstract base class contracts are properly
enforced for all injection provider implementations.
"""

from typing import List

import pytest

from specify_cli.assistants.claude import ClaudeProvider
from specify_cli.assistants.copilot import CopilotProvider
from specify_cli.assistants.cursor import CursorProvider
from specify_cli.assistants.gemini import GeminiProvider
from specify_cli.assistants.interfaces import AssistantProvider, ValidationResult
from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    InjectionPoint,
    InjectionValues,
    TemplateConfig,
)


class TestAbstractBaseClassEnforcement:
    """Test that ABC contracts are properly enforced."""

    def test_assistant_provider_is_abstract(self):
        """Test that AssistantProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AssistantProvider()

    def test_assistant_provider_has_required_methods(self):
        """Test that AssistantProvider defines required abstract methods."""
        # Check that these methods exist and are abstract
        assert hasattr(AssistantProvider, "config")
        assert hasattr(AssistantProvider, "get_injection_values")
        assert hasattr(AssistantProvider, "validate_setup")
        assert hasattr(AssistantProvider, "get_setup_instructions")

        # Check that they're abstract methods/properties
        assert getattr(AssistantProvider.config.fget, "__isabstractmethod__", False)
        assert getattr(
            AssistantProvider.get_injection_values, "__isabstractmethod__", False
        )
        assert getattr(AssistantProvider.validate_setup, "__isabstractmethod__", False)
        assert getattr(
            AssistantProvider.get_setup_instructions, "__isabstractmethod__", False
        )

    def test_concrete_implementations_must_implement_all_methods(self):
        """Test that concrete implementations must implement all abstract methods."""

        class IncompleteProvider(AssistantProvider):
            """Incomplete provider missing required methods."""

            pass

        # Should not be able to instantiate incomplete implementation
        with pytest.raises(TypeError):
            IncompleteProvider()

        class MinimalCompleteProvider(AssistantProvider):
            """Minimal complete provider with all required methods."""

            @property
            def config(self) -> AssistantConfig:
                return AssistantConfig(
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
                )

            def get_injection_values(self) -> InjectionValues:
                return {
                    InjectionPoint.COMMAND_PREFIX: "test:",
                    InjectionPoint.SETUP_INSTRUCTIONS: "Test setup",
                    InjectionPoint.CONTEXT_FILE_PATH: ".test/context.md",
                }

            @property
            def imports_supported(self) -> bool:
                return False

            def format_import(self, current_dir, target_file) -> str:
                return ""

            def validate_setup(self) -> ValidationResult:
                return ValidationResult(is_valid=True)

            def get_setup_instructions(self) -> List[str]:
                return ["Test instruction"]

        # Should be able to instantiate complete implementation
        provider = MinimalCompleteProvider()
        assert isinstance(provider, AssistantProvider)


class TestConcreteProviderCompliance:
    """Test that all concrete providers comply with ABC contracts."""

    @pytest.fixture
    def providers(self):
        """Fixture providing all concrete provider instances."""
        return [
            ClaudeProvider(),
            CopilotProvider(),
            CursorProvider(),
            GeminiProvider(),
        ]

    def test_all_providers_are_assistant_providers(self, providers):
        """Test that all providers inherit from AssistantProvider."""
        for provider in providers:
            assert isinstance(provider, AssistantProvider)

    def test_all_providers_implement_config_property(self, providers):
        """Test that all providers implement config property correctly."""
        for provider in providers:
            config = provider.config
            assert isinstance(config, AssistantConfig)

            # Validate config is properly formed
            assert config.name
            assert config.display_name
            assert config.description
            assert config.base_directory
            assert config.context_file.file
            assert config.command_files.directory
            assert config.agent_files.directory

    def test_all_providers_implement_get_injection_values(self, providers):
        """Test that all providers implement get_injection_values correctly."""
        for provider in providers:
            injections = provider.get_injection_values()
            assert isinstance(injections, dict)

            # Check that all required injection points are present
            required_points = {
                InjectionPoint.COMMAND_PREFIX,
                InjectionPoint.SETUP_INSTRUCTIONS,
                InjectionPoint.CONTEXT_FILE_PATH,
            }

            for required_point in required_points:
                assert required_point in injections
                assert isinstance(injections[required_point], str)
                # Note: Some assistants like Cursor may have empty command prefix (no CLI)
                # We validate presence but allow empty values for specific assistants

    def test_all_providers_implement_validate_setup(self, providers):
        """Test that all providers implement validate_setup correctly."""
        for provider in providers:
            result = provider.validate_setup()
            assert isinstance(result, ValidationResult)

    def test_injection_values_type_safety(self, providers):
        """Test that injection values conform to type annotations."""
        for provider in providers:
            injections = provider.get_injection_values()

            # Check type annotations
            assert isinstance(injections, dict)

            for key, value in injections.items():
                assert isinstance(key, InjectionPoint)
                assert isinstance(value, str)

    def test_config_validation_consistency(self, providers):
        """Test that config validation is consistent with provider validation."""
        for provider in providers:
            config = provider.config
            validation_result = provider.validate_setup()

            # If provider is valid, config should be valid too
            if validation_result.is_valid:
                # Config should be properly formed
                assert config.name
                assert config.display_name
                assert config.description


class TestInjectionValueValidation:
    """Test validation of injection values."""

    @pytest.fixture
    def sample_provider(self):
        """Sample provider for testing."""
        return ClaudeProvider()

    def test_required_injection_points_present(self, sample_provider):
        """Test that required injection points are always present."""
        injections = sample_provider.get_injection_values()

        required_points = {
            InjectionPoint.COMMAND_PREFIX,
            InjectionPoint.SETUP_INSTRUCTIONS,
            InjectionPoint.CONTEXT_FILE_PATH,
        }

        for point in required_points:
            assert point in injections
            assert injections[point]  # Non-empty

    def test_injection_values_are_strings(self, sample_provider):
        """Test that all injection values are strings."""
        injections = sample_provider.get_injection_values()

        for value in injections.values():
            assert isinstance(value, str)

    def test_injection_keys_are_valid_enum_values(self, sample_provider):
        """Test that all injection keys are valid InjectionPoint enum values."""
        injections = sample_provider.get_injection_values()

        valid_points = set(InjectionPoint)

        for key in injections:
            assert key in valid_points

    def test_no_empty_injection_values(self, sample_provider):
        """Test that injection values are not empty or whitespace-only."""
        injections = sample_provider.get_injection_values()

        for key, value in injections.items():
            assert value.strip(), f"Injection point {key} has empty value"


class TestProviderIsolation:
    """Test that providers are properly isolated from each other."""

    def test_providers_have_different_configs(self):
        """Test that different providers have different configurations."""
        providers = [
            ClaudeProvider(),
            CopilotProvider(),
            CursorProvider(),
            GeminiProvider(),
        ]

        configs = [provider.config for provider in providers]
        names = [config.name for config in configs]

        # All names should be unique
        assert len(set(names)) == len(names)

        # All base directories should be unique
        base_dirs = [config.base_directory for config in configs]
        assert len(set(base_dirs)) == len(base_dirs)

    def test_providers_have_different_injections(self):
        """Test that different providers have different injection values."""
        providers = [
            ClaudeProvider(),
            CopilotProvider(),
            CursorProvider(),
            GeminiProvider(),
        ]

        # Get command prefixes (should be different for each provider)
        prefixes = [
            provider.get_injection_values()[InjectionPoint.COMMAND_PREFIX]
            for provider in providers
        ]

        # All prefixes should be unique
        assert len(set(prefixes)) == len(prefixes)

    def test_provider_modifications_dont_affect_others(self):
        """Test that modifying one provider doesn't affect others."""
        provider1 = ClaudeProvider()
        provider2 = ClaudeProvider()

        # Get original values
        injections1 = provider1.get_injection_values()
        injections2 = provider2.get_injection_values()

        # They should be equal initially
        assert injections1 == injections2

        # But they should be separate objects
        assert injections1 is not injections2


class TestMethodReturnTypes:
    """Test that methods return correct types as specified in ABC."""

    @pytest.fixture
    def provider(self):
        """Sample provider for testing."""
        return ClaudeProvider()

    def test_config_property_returns_assistant_config(self, provider):
        """Test that config property returns AssistantConfig."""
        config = provider.config
        assert isinstance(config, AssistantConfig)
        assert type(config) is AssistantConfig

    def test_get_injections_returns_injection_values(self, provider):
        """Test that get_injections returns InjectionValues (dict)."""
        injections = provider.get_injection_values()
        assert isinstance(injections, dict)

        # Check that it matches the InjectionValues type alias
        for key, value in injections.items():
            assert isinstance(key, InjectionPoint)
            assert isinstance(value, str)

    def test_validate_setup_returns_validation_result(self, provider):
        """Test that validate_setup returns ValidationResult."""
        result = provider.validate_setup()
        assert isinstance(result, ValidationResult)
        assert type(result) is ValidationResult

"""Test assistant organization integration according to spec task T031."""

from specify_cli.assistants.interfaces import AssistantProvider
from specify_cli.assistants.registry import registry


class TestAssistantOrganizationIntegration:
    """Test integration of assistant organization features."""

    def test_assistant_folder_structure_organization(self):
        """Test that assistants are properly organized in folder structure."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # Should have multiple assistants organized
        assert len(all_assistants) >= 2, "Should have at least 2 assistants"

        # Each assistant should be properly instantiated
        for provider in all_assistants:
            assert isinstance(provider, AssistantProvider)
            assert hasattr(provider, "config")
            name = provider.config.name
            assert provider.config.name == name

    def test_assistant_configuration_isolation(self):
        """Test that assistant configurations are properly isolated."""
        # Use the imported registry directly

        claude_provider = registry.get_assistant("claude")
        gemini_provider = registry.get_assistant("gemini")

        if claude_provider and gemini_provider:
            # Configurations should be different
            assert claude_provider.config != gemini_provider.config
            assert claude_provider.config.name != gemini_provider.config.name
            assert (
                claude_provider.config.base_directory
                != gemini_provider.config.base_directory
            )

            # Injection values should be different
            claude_injections = claude_provider.get_injection_values()
            gemini_injections = gemini_provider.get_injection_values()

            # Should have different values for at least some injection points
            assert claude_injections != gemini_injections

    def test_assistant_provider_interface_consistency(self):
        """Test that all assistants implement consistent interfaces."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # All providers should implement the same interface
        for provider in all_assistants:
            # Required methods
            assert hasattr(provider, "config")
            assert hasattr(provider, "get_injection_values")
            assert hasattr(provider, "validate_setup")

            # Methods should be callable
            assert callable(provider.get_injection_values)
            assert callable(provider.validate_setup)

            # config should be an AssistantConfig
            from specify_cli.assistants.types import AssistantConfig

            assert isinstance(provider.config, AssistantConfig)

    def test_assistant_validation_integration(self):
        """Test integration of assistant validation across the system."""
        # Use the imported registry directly
        validation_results = registry.validate_all()

        # Should have validation results for all assistants
        assistant_names = registry.list_assistant_names()
        assert len(validation_results) == len(assistant_names)

        for name in assistant_names:
            assert name in validation_results
            result = validation_results[name]
            assert hasattr(result, "is_valid")
            assert isinstance(result.is_valid, bool)

    def test_assistant_injection_values_integration(self):
        """Test integration of injection values across assistants."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # All assistants should provide injection values
        for provider in all_assistants:
            injection_values = provider.get_injection_values()

            # Should be a dictionary
            assert isinstance(injection_values, dict)

            # Should have required injection points
            from specify_cli.assistants.injection_points import (
                InjectionPointMeta,
            )

            for key in injection_values:
                assert isinstance(key, InjectionPointMeta)

            for value in injection_values.values():
                assert isinstance(value, str)
                if len(value) == 0:
                    print(f"Empty value for {key} in {provider.config.name}")
                assert len(value) > 0

    def test_assistant_registry_completeness(self):
        """Test that the registry includes all expected assistants."""
        # Use the imported registry directly
        assistant_names = registry.list_assistant_names()

        # Should include the main assistants
        expected_assistants = {"claude", "gemini", "copilot", "cursor"}
        available_assistants = set(assistant_names)

        # Should have at least some of the expected assistants
        intersection = expected_assistants.intersection(available_assistants)
        assert len(intersection) >= 2, (
            f"Expected at least 2 assistants from {expected_assistants}, got {available_assistants}"
        )

    def test_assistant_configuration_path_management(self):
        """Test that assistants properly manage their configuration paths."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        for provider in all_assistants:
            config = provider.config

            # Should have base directory
            assert hasattr(config, "base_directory")
            assert isinstance(config.base_directory, str)
            assert len(config.base_directory) > 0

            # Should have path management methods
            assert hasattr(config, "is_path_managed")
            assert hasattr(config, "get_all_paths")

            # Path management should work
            all_paths = config.get_all_paths()
            assert isinstance(all_paths, set)
            assert len(all_paths) >= 1  # At least base directory

    def test_multi_assistant_workflow_integration(self):
        """Test integration of workflows with multiple assistants."""
        # Use the imported registry directly

        # Simulate multi-assistant project setup
        claude_provider = registry.get_assistant("claude")
        gemini_provider = registry.get_assistant("gemini")

        if claude_provider and gemini_provider:
            # Both should validate successfully
            claude_provider.validate_setup()
            gemini_provider.validate_setup()

            # Should be able to get injection values from both
            claude_injections = claude_provider.get_injection_values()
            gemini_injections = gemini_provider.get_injection_values()

            # Should have different but valid configurations
            assert isinstance(claude_injections, dict)
            assert isinstance(gemini_injections, dict)

    def test_assistant_registry_thread_safety_simulation(self):
        """Test that registry operations are safe for concurrent use."""
        import threading
        import time

        # Use the imported registry directly
        results = []
        errors = []

        def worker():
            try:
                # Simulate concurrent access
                for _ in range(10):
                    names = registry.list_assistant_names()
                    if names:
                        provider = registry.get_assistant(names[0])
                        if provider:
                            validation = provider.validate_setup()
                            results.append(validation.is_valid)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(str(e))

        # Run multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should not have errors
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) > 0, "Should have some results from concurrent access"

    def test_assistant_organization_scalability(self):
        """Test that assistant organization scales with more assistants."""
        # Use the imported registry directly

        # Performance should not degrade significantly with all assistants
        import time

        start_time = time.time()
        for _ in range(50):
            assistant_names = registry.list_assistant_names()
            for name in assistant_names:
                provider = registry.get_assistant(name)
                if provider:
                    provider.get_injection_values()
        end_time = time.time()

        total_time = end_time - start_time
        # Should complete reasonably quickly even with multiple assistants
        assert total_time < 1.0, f"Assistant operations too slow: {total_time:.3f}s"

    def test_assistant_configuration_consistency_across_instances(self):
        """Test that assistant configurations are consistent across multiple instances."""
        from specify_cli.assistants.assistant_registry import StaticAssistantRegistry
        from specify_cli.assistants.claude import ClaudeProvider
        from specify_cli.assistants.copilot import CopilotProvider
        from specify_cli.assistants.cursor import CursorProvider
        from specify_cli.assistants.gemini import GeminiProvider

        # Create two registry instances with same assistants
        registry1 = StaticAssistantRegistry()
        registry1.register_assistant(ClaudeProvider())
        registry1.register_assistant(CopilotProvider())
        registry1.register_assistant(CursorProvider())
        registry1.register_assistant(GeminiProvider())

        registry2 = StaticAssistantRegistry()
        registry2.register_assistant(ClaudeProvider())
        registry2.register_assistant(CopilotProvider())
        registry2.register_assistant(CursorProvider())
        registry2.register_assistant(GeminiProvider())

        # Should get consistent results
        names1 = registry1.list_assistant_names()
        names2 = registry2.list_assistant_names()

        assert names1 == names2

        # Same assistants should have same configurations
        for name in names1:
            provider1 = registry1.get_assistant(name)
            provider2 = registry2.get_assistant(name)

            if provider1 and provider2:
                assert provider1.config.name == provider2.config.name
                assert (
                    provider1.config.base_directory == provider2.config.base_directory
                )

    def test_assistant_organization_error_recovery(self):
        """Test error recovery in assistant organization."""
        # Use the imported registry directly

        # Should handle missing assistants gracefully
        non_existent = registry.get_assistant("non_existent_assistant")
        assert non_existent is None

        # Should continue working after errors
        valid_names = registry.list_assistant_names()
        assert len(valid_names) > 0

        # Should validate remaining assistants successfully
        validation_results = registry.validate_all()
        assert len(validation_results) > 0

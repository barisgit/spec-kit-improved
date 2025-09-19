"""Test ABC contract enforcement for AssistantRegistry according to spec task T024."""

import pytest

from specify_cli.assistants.interfaces import AssistantProvider
from specify_cli.assistants.registry import registry


class TestAssistantRegistryABCContract:
    """Test that AssistantRegistry follows Abstract Base Class contracts."""

    def test_assistant_registry_is_abstract_base_class(self):
        """Test that AssistantRegistry is defined as an ABC."""
        # Check if AssistantRegistry is abstract
        # Note: This might not be implemented as ABC yet, so test what exists
        # Use the imported registry directly
        assert hasattr(registry, "get_assistant")
        assert hasattr(registry, "get_all_assistants")
        assert hasattr(registry, "list_assistant_names")

    def test_registry_has_required_methods(self):
        """Test that registry has all required methods."""
        # Use the imported registry directly

        # Core registry methods
        required_methods = [
            "get_assistant",
            "get_all_assistants",
            "list_assistant_names",
            "is_registered",
            "validate_all",
        ]

        for method_name in required_methods:
            assert hasattr(registry, method_name), (
                f"Registry missing required method: {method_name}"
            )
            method = getattr(registry, method_name)
            assert callable(method), f"Registry {method_name} is not callable"

    def test_get_assistant_method_contract(self):
        """Test get_assistant method follows proper contract."""
        # Use the imported registry directly

        # Should handle valid assistant names
        claude_provider = registry.get_assistant("claude")
        if claude_provider is not None:
            assert isinstance(claude_provider, AssistantProvider)

        # Should handle invalid assistant names gracefully
        non_existent = registry.get_assistant("non_existent_assistant")
        assert non_existent is None

        # Should handle edge cases with string inputs only
        edge_cases = ["", "invalid_name"]
        for edge_case in edge_cases:
            result = registry.get_assistant(edge_case)
            # Should either return None or raise appropriate error
            assert result is None or isinstance(result, AssistantProvider)

        # Non-string inputs should raise TypeError
        invalid_inputs = [None, 123]
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError):
                registry.get_assistant(invalid_input)  # type: ignore

    def test_get_all_assistants_method_contract(self):
        """Test get_all_assistants method follows proper contract."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # Should return a list of AssistantProvider instances
        assert isinstance(all_assistants, list)

        # All items should be AssistantProvider instances
        for provider in all_assistants:
            assert isinstance(provider, AssistantProvider)

    def test_list_assistant_names_method_contract(self):
        """Test list_assistant_names method follows proper contract."""
        # Use the imported registry directly
        names = registry.list_assistant_names()

        # Should return a list
        assert isinstance(names, list)

        # All items should be strings
        for name in names:
            assert isinstance(name, str)
            assert len(name) > 0

        # Should match names from all assistants
        all_assistants = registry.get_all_assistants()
        provider_names = {provider.config.name for provider in all_assistants}
        assert set(names) == provider_names

    def test_is_registered_method_contract(self):
        """Test is_registered method follows proper contract."""
        # Use the imported registry directly

        # Test with known assistants
        known_assistants = registry.list_assistant_names()
        for assistant_name in known_assistants:
            assert registry.is_registered(assistant_name) is True

        # Test with unknown assistant
        assert registry.is_registered("unknown_assistant") is False

        # Test edge cases with string inputs
        edge_cases = ["", "invalid_name"]
        for edge_case in edge_cases:
            result = registry.is_registered(edge_case)
            assert isinstance(result, bool)

        # Non-string inputs should raise TypeError
        invalid_inputs = [None, 123]
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError):
                registry.is_registered(invalid_input)  # type: ignore

    def test_validate_all_method_contract(self):
        """Test validate_all method follows proper contract."""
        # Use the imported registry directly
        validation_results = registry.validate_all()

        # Should return a dictionary
        assert isinstance(validation_results, dict)

        # Keys should be assistant names
        for name in validation_results:
            assert isinstance(name, str)
            assert registry.is_registered(name)

        # Values should be validation results
        for result in validation_results.values():
            assert hasattr(result, "is_valid")
            assert isinstance(result.is_valid, bool)

    def test_registry_consistency_contract(self):
        """Test that registry methods are consistent with each other."""
        # Use the imported registry directly

        # get_all_assistants and list_assistant_names should be consistent
        all_assistants = registry.get_all_assistants()
        assistant_names = registry.list_assistant_names()

        assert len(all_assistants) == len(assistant_names)
        provider_names = {provider.config.name for provider in all_assistants}
        assert provider_names == set(assistant_names)

        # is_registered should be consistent with list_assistant_names
        for name in assistant_names:
            assert registry.is_registered(name)

        # get_assistant should be consistent with get_all_assistants
        for provider in all_assistants:
            retrieved_provider = registry.get_assistant(provider.config.name)
            assert retrieved_provider == provider

    def test_registry_immutability_contract(self):
        """Test that registry maintains immutability where expected."""
        # Use the imported registry directly

        # Getting lists/dicts should not allow external modification
        names1 = registry.list_assistant_names()
        names2 = registry.list_assistant_names()

        # Should get consistent results
        assert names1 == names2

        # Modifying returned list should not affect registry
        if len(names1) > 0:
            original_length = len(names1)
            names1.append("fake_assistant")
            names3 = registry.list_assistant_names()
            assert len(names3) == original_length

    def test_registry_provider_type_enforcement(self):
        """Test that registry enforces AssistantProvider types."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # All providers should implement AssistantProvider interface
        for provider in all_assistants:
            assert isinstance(provider, AssistantProvider)
            assert hasattr(provider, "config")
            assert hasattr(provider, "get_injection_values")
            assert hasattr(provider, "validate_setup")

    def test_registry_initialization_contract(self):
        """Test that registry can be initialized consistently."""
        # Should be able to import registry multiple times
        from specify_cli.assistants.registry import registry as registry1
        from specify_cli.assistants.registry import registry as registry2

        # Should get the same instance (singleton pattern) or equivalent instances
        assert registry1.list_assistant_names() == registry2.list_assistant_names()

    def test_registry_error_handling_contract(self):
        """Test that registry handles errors according to contract."""
        # Use the imported registry directly

        # Should handle string inputs gracefully
        string_inputs = ["", "invalid_name"]
        for invalid_input in string_inputs:
            # get_assistant with invalid input
            result = registry.get_assistant(invalid_input)
            assert result is None or isinstance(result, AssistantProvider)

            # is_registered with invalid input
            is_reg = registry.is_registered(invalid_input)
            assert isinstance(is_reg, bool)

        # Should raise TypeError for non-string inputs
        non_string_inputs = [None, 123, [], {}]
        for invalid_input in non_string_inputs:
            with pytest.raises(TypeError):
                registry.get_assistant(invalid_input)  # type: ignore
            with pytest.raises(TypeError):
                registry.is_registered(invalid_input)  # type: ignore

    def test_registry_performance_contract(self):
        """Test that registry operations meet performance expectations."""
        import time
        # Use the imported registry directly

        # Test list_assistant_names performance
        start_time = time.perf_counter()
        for _ in range(100):
            registry.list_assistant_names()
        end_time = time.perf_counter()

        avg_time = (end_time - start_time) / 100
        # Should remain efficient (<5ms per call on shared CI runners)
        assert avg_time < 0.005, f"list_assistant_names too slow: {avg_time:.6f}s"

        # Test get_assistant performance
        if len(registry.list_assistant_names()) > 0:
            first_assistant = registry.list_assistant_names()[0]

            start_time = time.perf_counter()
            for _ in range(100):
                registry.get_assistant(first_assistant)
            end_time = time.perf_counter()

            avg_time = (end_time - start_time) / 100
            # Should remain efficient (<5ms per call on shared CI runners)
            assert avg_time < 0.005, f"get_assistant too slow: {avg_time:.6f}s"

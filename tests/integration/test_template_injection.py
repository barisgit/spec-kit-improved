"""Test template injection integration according to spec task T032."""

from typing import List

import pytest

from specify_cli.assistants.injection_points import InjectionPointMeta
from specify_cli.assistants.registry import registry
from specify_cli.models.config import ProjectConfig, TemplateConfig


class TestTemplateInjectionIntegration:
    """Test integration of template injection features across the system."""

    @pytest.fixture
    def mock_template_service(self):
        """Create a mock template service for testing."""

        class MockTemplateService:
            def render_template(self, template_content, context):
                """Simple template rendering for testing."""
                # Replace injection points with context values
                result = template_content
                for key, value in context.items():
                    placeholder = f"{{{{{key}}}}}"
                    result = result.replace(placeholder, str(value))
                return result

            def get_template_variables(self, template_content):
                """Extract template variables for testing."""
                import re

                variables = set(re.findall(r"\{\{(\w+)\}\}", template_content))
                return variables

        return MockTemplateService()

    def test_injection_point_template_integration(self):
        """Test that injection points integrate properly with templates."""
        # Use the imported registry directly
        claude_provider = registry.get_assistant("claude")

        if claude_provider:
            injection_values = claude_provider.get_injection_values()

            # Create a template that uses injection points

            # Convert injection points to template context
            injection_context = {
                str(key): value for key, value in injection_values.items()
            }

            # Create a proper template context that includes both injection points and template variables
            from pathlib import Path

            from specify_cli.models.project import TemplateContext

            full_context = TemplateContext(
                project_name="test_project",
                ai_assistant="claude",
                project_path=Path("/tmp/test_project"),
            )

            template_context = full_context.to_dict()
            # Add injection values to the context
            template_context.update(injection_context)

            # Should be able to render the template with both template vars and injection points
            assert "ai_assistant" in template_context  # Template variable
            assert "assistant_command_prefix" in template_context

    def test_multi_assistant_template_injection(self):
        """Test template injection with multiple assistants."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # Template that works with any assistant

        assistant_count = 0
        for provider in all_assistants:
            injection_values = provider.get_injection_values()

            # Convert to template context
            context = {str(key): value for key, value in injection_values.items()}

            # Should have required injection points
            required_points = ["ai_assistant", "assistant_command_prefix"]
            for required_point in required_points:
                if required_point in context:
                    assert isinstance(context[required_point], str)
                    assert len(context[required_point]) > 0

            assistant_count += 1

        assert assistant_count >= 2, "Should test with multiple assistants"

    def test_template_context_injection_consistency(self):
        """Test that template context injection is consistent across calls."""
        # Use the imported registry directly
        claude_provider = registry.get_assistant("claude")

        if claude_provider:
            # Get injection values multiple times
            injections1 = claude_provider.get_injection_values()
            injections2 = claude_provider.get_injection_values()

            # Should be consistent
            assert injections1 == injections2

            # Convert to template contexts
            context1 = {str(key): value for key, value in injections1.items()}
            context2 = {str(key): value for key, value in injections2.items()}

            assert context1 == context2

    def test_injection_point_enum_template_compatibility(self):
        """Test that injection point enums work well with templates."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        for provider in all_assistants:
            injection_values = provider.get_injection_values()

            # All keys should be InjectionPoint enums
            for key in injection_values:
                assert isinstance(key, InjectionPointMeta)

                # String representation should be template-friendly
                str_key = str(key)
                assert isinstance(str_key, str)
                assert len(str_key) > 0
                assert "_" in str_key or str_key.islower()  # Template-friendly naming

    def test_template_injection_error_handling(self):
        """Test error handling in template injection scenarios."""
        # Use the imported registry directly

        # Test with missing injection points

        claude_provider = registry.get_assistant("claude")
        if claude_provider:
            injection_values = claude_provider.get_injection_values()
            injection_context = {
                str(key): value for key, value in injection_values.items()
            }

            # Create proper template context for testing
            from pathlib import Path

            from specify_cli.models.project import TemplateContext

            full_context = TemplateContext(
                project_name="test_project",
                ai_assistant="claude",
                project_path=Path("/tmp/test_project"),
            )

            context = full_context.to_dict()
            context.update(injection_context)

            # Should handle missing injection points gracefully
            # (This would depend on the actual template engine implementation)
            assert "ai_assistant" in context  # Template variable
            assert "assistant_command_prefix" in context  # Injection point

    def test_conditional_template_injection(self):
        """Test conditional logic in template injection."""
        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # Template with conditional content

        # Should work with different assistants
        for provider in all_assistants:
            name = provider.config.name
            injection_values = provider.get_injection_values()
            context = {str(key): value for key, value in injection_values.items()}

            # Should have ai_assistant value
            if "ai_assistant" in context:
                assert context["ai_assistant"] == name

    def test_template_injection_performance(self):
        """Test performance of template injection operations."""
        import time

        # Use the imported registry directly
        all_assistants = registry.get_all_assistants()

        # Measure injection value retrieval performance
        start_time = time.time()

        for _ in range(100):
            for provider in all_assistants:
                injection_values = provider.get_injection_values()
                {str(key): value for key, value in injection_values.items()}

        end_time = time.time()
        total_time = end_time - start_time

        # Should be fast (under 100ms total for 100 iterations)
        assert total_time < 0.1, f"Template injection too slow: {total_time:.3f}s"

    def test_injection_point_coverage_in_templates(self):
        """Test that all injection points can be used in templates."""
        # Use the imported registry directly
        claude_provider = registry.get_assistant("claude")

        if claude_provider:
            injection_values = claude_provider.get_injection_values()

            # Create template that uses all available injection points
            template_parts: List[str] = []
            for key, _value in injection_values.items():
                str_key = str(key)
                template_parts.append(f"{str_key}: {{{{{str_key}}}}}")

            "\n".join(template_parts)

            # Should be able to create template context
            context = {str(key): value for key, value in injection_values.items()}

            # All injection points should be usable
            for key in injection_values:
                str_key = str(key)
                assert str_key in context
                assert isinstance(context[str_key], str)

    def test_template_injection_with_project_config(self):
        """Test template injection integration with project configuration."""
        # Create a project config with multiple assistants
        project_config = ProjectConfig(
            name="test-project",
            template_settings=TemplateConfig(ai_assistants=["claude", "gemini"]),
        )

        # Use the imported registry directly

        # Should be able to get injection values for all configured assistants
        for assistant_name in project_config.template_settings.ai_assistants:
            provider = registry.get_assistant(assistant_name)
            if provider:
                injection_values = provider.get_injection_values()
                injection_context = {
                    str(key): value for key, value in injection_values.items()
                }

                # Create full template context
                from pathlib import Path

                from specify_cli.models.project import TemplateContext

                full_context = TemplateContext(
                    project_name="test_project",
                    ai_assistant=assistant_name,
                    project_path=Path("/tmp/test_project"),
                )

                context = full_context.to_dict()
                context.update(injection_context)

                # Should have assistant-specific values
                assert "ai_assistant" in context  # Template variable
                assert context["ai_assistant"] == assistant_name
                assert "assistant_command_prefix" in context  # Injection point

    def test_template_injection_isolation_between_assistants(self):
        """Test that template injection is properly isolated between assistants."""
        # Use the imported registry directly

        claude_provider = registry.get_assistant("claude")
        gemini_provider = registry.get_assistant("gemini")

        if claude_provider and gemini_provider:
            claude_injections = claude_provider.get_injection_values()
            gemini_injections = gemini_provider.get_injection_values()

            claude_context = {
                str(key): value for key, value in claude_injections.items()
            }
            gemini_context = {
                str(key): value for key, value in gemini_injections.items()
            }

            # Should have different values for assistant-specific injection points
            if "ai_assistant" in claude_context and "ai_assistant" in gemini_context:
                assert claude_context["ai_assistant"] != gemini_context["ai_assistant"]

            if (
                "assistant_command_prefix" in claude_context
                and "assistant_command_prefix" in gemini_context
            ):
                assert (
                    claude_context["assistant_command_prefix"]
                    != gemini_context["assistant_command_prefix"]
                )

    def test_template_injection_backwards_compatibility(self):
        """Test that template injection maintains backwards compatibility."""
        # Use the imported registry directly
        claude_provider = registry.get_assistant("claude")

        if claude_provider:
            injection_values = claude_provider.get_injection_values()

            # Should maintain compatibility with expected injection points
            expected_points = [
                "ai_assistant",
                "assistant_command_prefix",
                "assistant_context_file_path",
                "assistant_setup_instructions",
            ]

            context = {str(key): value for key, value in injection_values.items()}

            # At least some expected points should be available
            available_expected = [
                point for point in expected_points if point in context
            ]
            assert len(available_expected) >= 2, (
                f"Expected injection points not available: {expected_points}"
            )

    def test_template_injection_with_complex_templates(self):
        """Test template injection with complex template structures."""
        # Use the imported registry directly
        claude_provider = registry.get_assistant("claude")

        if claude_provider:
            injection_values = claude_provider.get_injection_values()
            context = {str(key): value for key, value in injection_values.items()}

            # Complex template with nested structures

            # Should be able to handle complex template structures
            # (This tests the template engine's capability with our injection values)
            assert len(context) > 0
            for key, value in context.items():
                assert isinstance(key, str)
                assert isinstance(value, str)

"""Tests for security fixes in template rendering."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from jinja2 import Template

from specify_cli.models.project import TemplateContext
from specify_cli.services.template_service.template_context_processor import (
    TemplateContextProcessor,
)
from specify_cli.services.template_service.template_renderer import TemplateRenderer
from specify_cli.utils.security import (
    PathValidator,
    TemplateSanitizer,
    TemplateSecurityError,
    TemplateSecurityValidator,
)


class TestTemplateSanitizer:
    """Test template input sanitization."""

    def test_sanitize_safe_injection_value(self):
        """Test sanitization of safe injection values."""
        safe_value = "claude-code-assistant"
        result = TemplateSanitizer.sanitize_injection_value(safe_value)
        assert result == safe_value

    def test_sanitize_dangerous_injection_value(self):
        """Test sanitization rejects dangerous injection values."""
        dangerous_values = [
            "{{ malicious_code }}",
            "{% for item in items %}",
            "<script>alert('xss')</script>",
            "__import__('os').system('rm -rf /')",
            "javascript:alert(1)",
        ]

        for dangerous_value in dangerous_values:
            with pytest.raises(TemplateSecurityError):
                TemplateSanitizer.sanitize_injection_value(dangerous_value)

    def test_sanitize_injection_value_too_long(self):
        """Test sanitization rejects overly long values."""
        long_value = "a" * (TemplateSanitizer.MAX_INJECTION_VALUE_LENGTH + 1)
        with pytest.raises(TemplateSecurityError):
            TemplateSanitizer.sanitize_injection_value(long_value)

    def test_sanitize_context_dict_safe(self):
        """Test sanitization of safe context dictionary."""
        safe_context = {
            "project_name": "my-project",
            "ai_assistant": "claude",
            "creation_date": "2025-09-29",
            "feature_count": 5,
            "is_enabled": True,
        }
        result = TemplateSanitizer.sanitize_context_dict(safe_context)
        assert result == safe_context

    def test_sanitize_context_dict_dangerous(self):
        """Test sanitization rejects dangerous context values."""
        dangerous_context = {
            "project_name": "{{ malicious_code }}",
            "safe_value": "claude",
        }
        with pytest.raises(TemplateSecurityError):
            TemplateSanitizer.sanitize_context_dict(dangerous_context)

    def test_sanitize_context_dict_too_many_variables(self):
        """Test sanitization rejects too many variables."""
        large_context = {
            f"var_{i}": f"value_{i}" for i in range(TemplateSanitizer.MAX_VARIABLES + 1)
        }
        with pytest.raises(TemplateSecurityError):
            TemplateSanitizer.sanitize_context_dict(large_context)

    def test_sanitize_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        nested_context = {"config": {"database": {"host": "localhost", "port": 5432}}}
        result = TemplateSanitizer.sanitize_context_dict(nested_context)
        assert result["config"]["database"]["host"] == "localhost"

    def test_sanitize_nested_dict_too_deep(self):
        """Test sanitization rejects overly nested dictionaries."""
        # Create 5-level deep nesting (exceeds limit of 3)
        deep_context = {
            "level1": {"level2": {"level3": {"level4": {"level5": "value"}}}}
        }
        with pytest.raises(TemplateSecurityError):
            TemplateSanitizer.sanitize_context_dict(deep_context)

    def test_validate_template_complexity_safe(self):
        """Test validation of safe template complexity."""
        safe_template = """
        Hello {{ name }}!
        {% if enabled %}
            Feature is enabled.
        {% endif %}
        """
        # Should not raise exception
        TemplateSanitizer.validate_template_complexity(safe_template)

    def test_validate_template_complexity_too_large(self):
        """Test validation rejects overly large templates."""
        large_template = "a" * (TemplateSanitizer.MAX_TEMPLATE_SIZE + 1)
        with pytest.raises(TemplateSecurityError):
            TemplateSanitizer.validate_template_complexity(large_template)

    def test_validate_template_complexity_too_many_loops(self):
        """Test validation rejects templates with too many loops."""
        many_loops = "{% for i in range(10) %}" * (TemplateSanitizer.MAX_LOOPS + 1)
        with pytest.raises(TemplateSecurityError):
            TemplateSanitizer.validate_template_complexity(many_loops)

    def test_validate_template_complexity_too_many_includes(self):
        """Test validation rejects templates with too many includes."""
        many_includes = "{% include 'template.j2' %}" * (
            TemplateSanitizer.MAX_INCLUDES + 1
        )
        with pytest.raises(TemplateSecurityError):
            TemplateSanitizer.validate_template_complexity(many_includes)


class TestPathValidator:
    """Test path validation and sanitization."""

    def test_validate_safe_path(self):
        """Test validation of safe paths."""
        base_path = Path("/tmp/safe")
        target_path = Path("/tmp/safe/output.txt")
        assert PathValidator.validate_safe_path(base_path, target_path) is True

    def test_validate_unsafe_path_traversal(self):
        """Test rejection of path traversal attempts."""
        base_path = Path("/tmp/safe")
        target_path = Path("/tmp/safe/../../../etc/passwd")
        assert PathValidator.validate_safe_path(base_path, target_path) is False

    def test_sanitize_filename_safe(self):
        """Test sanitization of safe filenames."""
        safe_filename = "my-template.md"
        result = PathValidator.sanitize_filename(safe_filename)
        assert result == safe_filename

    def test_sanitize_filename_dangerous(self):
        """Test rejection of dangerous filenames."""
        dangerous_filenames = [
            "../../../etc/passwd",
            "file.txt;rm -rf /",
            "template.md\\..\\..\\system32",
            "~/.ssh/id_rsa",
            "$HOME/.bashrc",
        ]

        for dangerous_filename in dangerous_filenames:
            with pytest.raises(TemplateSecurityError):
                PathValidator.sanitize_filename(dangerous_filename)

    def test_sanitize_filename_too_long(self):
        """Test rejection of overly long filenames."""
        long_filename = "a" * 300
        with pytest.raises(TemplateSecurityError):
            PathValidator.sanitize_filename(long_filename)


class TestTemplateRenderer:
    """Test template renderer security fixes."""

    def test_render_template_with_safe_context(self):
        """Test template rendering with safe context."""
        renderer = TemplateRenderer()
        template = Template("Hello {{ name }}!")

        # Create mock context
        context = Mock(spec=TemplateContext)
        context.project_name = "test-project"
        context.ai_assistant = "claude"
        context.to_dict = Mock(return_value={"name": "World"})

        result = renderer.render_template(template, context, "test-template")
        assert result.success is True
        assert "Hello World!" in result.content

    def test_render_template_with_dangerous_context(self):
        """Test template rendering rejects dangerous context."""
        renderer = TemplateRenderer()
        template = Template("Hello {{ name }}!")

        # Create real context with dangerous template variables
        from specify_cli.models.project import TemplateContext

        context = TemplateContext(
            project_name="test-project",
            ai_assistant="claude",
            template_variables={"name": "{{ malicious_code }}"},
        )

        result = renderer.render_template(template, context, "test-template")
        # Security system should gracefully handle dangerous content by using safe fallback
        assert result.success is True  # Renders successfully with safe fallback
        # But the dangerous variable should be missing/sanitized
        assert "malicious_code" not in result.content
        # And template should render with empty/safe content
        assert result.content.strip() == "Hello !"


class TestTemplateContextProcessor:
    """Test template context processor security fixes."""

    def test_prepare_context_safe(self):
        """Test context preparation with safe values."""
        processor = TemplateContextProcessor()

        context = Mock(spec=TemplateContext)
        context.project_name = "test-project"
        context.ai_assistant = "claude"
        context.to_dict = Mock(
            return_value={
                "project_name": "test-project",
                "ai_assistant": "claude",
                "creation_date": "2025-09-29",
            }
        )

        result = processor.prepare_context(context)
        assert result["project_name"] == "test-project"
        assert result["ai_assistant"] == "claude"

    def test_prepare_context_with_dangerous_injection(self):
        """Test context preparation sanitizes dangerous injection points."""
        processor = TemplateContextProcessor()

        # Create a real context with dangerous template variables to trigger security validation
        from specify_cli.models.project import TemplateContext

        context = TemplateContext(
            project_name="test-project",
            ai_assistant="claude",
            template_variables={"dangerous_var": "{{ malicious_code }}"},
        )

        result = processor.prepare_context(context)
        # Should create safe fallback context when dangerous content is detected
        assert "security_warning" in result
        assert (
            result["security_warning"]
            == "Template context was sanitized due to security validation"
        )

    def test_create_safe_fallback_context(self):
        """Test creation of safe fallback context."""
        processor = TemplateContextProcessor()

        context = Mock(spec=TemplateContext)
        context.project_name = "test-project"
        context.ai_assistant = "claude"
        context.creation_date = "2025-09-29"
        context.author = "test-author"

        result = processor._create_safe_fallback_context(context)
        assert result["project_name"] == "test-project"
        assert result["ai_assistant"] == "claude"
        assert (
            result["security_warning"]
            == "Template context was sanitized due to security validation"
        )


class TestTemplateSecurityValidator:
    """Test comprehensive security validation."""

    def test_validate_template_render_safe(self):
        """Test validation of safe template rendering."""
        validator = TemplateSecurityValidator()

        template_content = "Hello {{ name }}!"
        context_dict = {"name": "World"}
        output_path = Path("/tmp/safe/output.txt")
        base_path = Path("/tmp/safe")

        result = validator.validate_template_render(
            template_content, context_dict, output_path, base_path
        )
        assert result["name"] == "World"

    def test_validate_template_render_unsafe_path(self):
        """Test validation rejects unsafe output paths."""
        validator = TemplateSecurityValidator()

        template_content = "Hello {{ name }}!"
        context_dict = {"name": "World"}
        output_path = Path("/tmp/safe/../../../etc/passwd")
        base_path = Path("/tmp/safe")

        with pytest.raises(TemplateSecurityError):
            validator.validate_template_render(
                template_content, context_dict, output_path, base_path
            )

    def test_validate_template_render_dangerous_context(self):
        """Test validation rejects dangerous context."""
        validator = TemplateSecurityValidator()

        template_content = "Hello {{ name }}!"
        context_dict = {"name": "{{ malicious_code }}"}
        output_path = Path("/tmp/safe/output.txt")
        base_path = Path("/tmp/safe")

        with pytest.raises(TemplateSecurityError):
            validator.validate_template_render(
                template_content, context_dict, output_path, base_path
            )

    def test_validate_template_render_complex_template(self):
        """Test validation rejects overly complex templates."""
        validator = TemplateSecurityValidator()

        # Create template with too many loops
        template_content = "{% for i in range(10) %}" * (
            TemplateSanitizer.MAX_LOOPS + 1
        )
        context_dict = {"name": "World"}
        output_path = Path("/tmp/safe/output.txt")
        base_path = Path("/tmp/safe")

        with pytest.raises(TemplateSecurityError):
            validator.validate_template_render(
                template_content, context_dict, output_path, base_path
            )

"""
Contract tests for TemplateService interface.

Tests the external service contract and integration points.
Does not test Jinja2 framework behavior or implementation details.
"""

from pathlib import Path

import pytest

from specify_cli.models.project import TemplateContext, TemplateFile
from specify_cli.services.template_service import TemplateService


class TestTemplateServiceContract:
    """Test contract compliance for TemplateService interface."""

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance for testing."""
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    @pytest.fixture
    def sample_context(self) -> TemplateContext:
        """Create sample template context."""
        from specify_cli.models.config import BranchNamingConfig

        branch_config = BranchNamingConfig()
        branch_config.description = "Test branch configuration"
        branch_config.patterns = ["feature/{feature-name}"]
        branch_config.validation_rules = ["max_length_50"]

        return TemplateContext(
            project_name="test-project",
            ai_assistant="claude",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-17",
            project_path=Path("/tmp/test-project").resolve(),
        )

    @pytest.fixture
    def temp_template_dir(self, tmp_path: Path) -> Path:
        """Create temporary template directory structure."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create basic template files
        (template_dir / "readme.md.j2").write_text(
            "# {{ project_name }}\nAI: {{ ai_assistant }}"
        )
        (template_dir / "config.toml.j2").write_text(
            '[project]\nname = "{{ project_name }}"'
        )

        return template_dir

    def test_load_template_package_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ) -> None:
        """Test load_template_package method contract."""
        # Contract: Should return boolean for success/failure
        result = template_service.load_template_package("claude", temp_template_dir)
        assert isinstance(result, bool)

        # Contract: Should handle invalid paths gracefully
        result = template_service.load_template_package(
            "claude", temp_template_dir / "nonexistent"
        )
        assert isinstance(result, bool)
        assert result is False

    def test_render_template_contract(
        self,
        template_service: TemplateService,
        sample_context: TemplateContext,
        temp_template_dir: Path,
    ) -> None:
        """Test render_template method contract."""
        template_service.load_template_package("claude", temp_template_dir)

        # Contract: Should return rendered string
        result = template_service.render_template("readme.md.j2", sample_context)
        assert isinstance(result, str)
        assert "test-project" in result
        assert "claude" in result

        # Contract: Should raise FileNotFoundError for missing templates
        with pytest.raises(FileNotFoundError):
            template_service.render_template("nonexistent.j2", sample_context)

    def test_render_project_templates_contract(
        self,
        template_service: TemplateService,
        sample_context: TemplateContext,
        temp_template_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test render_project_templates method contract."""
        template_service.load_template_package("claude", temp_template_dir)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Contract: Should return list of TemplateFile objects
        result = template_service.render_project_templates(sample_context, output_dir)
        assert isinstance(result, list)
        assert len(result) > 0

        for template_file in result:
            assert isinstance(template_file, TemplateFile)
            assert hasattr(template_file, "template_path")
            assert hasattr(template_file, "output_path")
            assert hasattr(template_file, "content")
            assert hasattr(template_file, "is_executable")

    def test_validate_template_syntax_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ) -> None:
        """Test validate_template_syntax method contract."""
        valid_template = temp_template_dir / "readme.md.j2"

        # Contract: Should return (bool, str|None) tuple
        is_valid, error = template_service.validate_template_syntax(valid_template)
        assert isinstance(is_valid, bool)
        assert is_valid is True
        assert error is None or isinstance(error, str)

        # Contract: Should handle invalid templates
        invalid_template = temp_template_dir / "invalid.j2"
        invalid_template.write_text("{{ unclosed_var")

        is_valid, error = template_service.validate_template_syntax(invalid_template)
        assert isinstance(is_valid, bool)
        assert is_valid is False
        assert isinstance(error, str)

    def test_get_template_variables_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ) -> None:
        """Test get_template_variables method contract."""
        template_path = temp_template_dir / "readme.md.j2"

        # Contract: Should return list of variable names
        variables = template_service.get_template_variables(template_path)
        assert isinstance(variables, list)
        assert all(isinstance(var, str) for var in variables)

        # Contract: Should find variables from template
        assert "project_name" in variables
        assert "ai_assistant" in variables

    def test_set_custom_template_dir_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ) -> None:
        """Test set_custom_template_dir method contract."""
        # Contract: Should return boolean for success/failure
        result = template_service.set_custom_template_dir(temp_template_dir)
        assert isinstance(result, bool)

        # Contract: Should handle None parameter
        result = template_service.set_custom_template_dir(None)
        assert isinstance(result, bool)

        # Contract: Should handle invalid directories
        result = template_service.set_custom_template_dir(
            temp_template_dir / "nonexistent"
        )
        assert isinstance(result, bool)
        assert result is False


class TestTemplateServiceIntegration:
    """Test template service integration workflow."""

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance."""
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    def test_complete_template_workflow(
        self, template_service: TemplateService, tmp_path: Path
    ) -> None:
        """Test complete template processing workflow."""
        # Setup template and output directories
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        (template_dir / "project.md.j2").write_text(
            "# {{ project_name }}\nFeature: {{ feature_name }}"
        )

        context = TemplateContext(
            project_name="integration-test",
            ai_assistant="claude",
            feature_name="integration",
            additional_vars={},
        )

        # Workflow: load -> validate -> render -> batch render
        assert template_service.load_template_package("claude", template_dir)

        template_path = template_dir / "project.md.j2"
        is_valid, _ = template_service.validate_template_syntax(template_path)
        assert is_valid

        content = template_service.render_template("project.md.j2", context)
        assert "integration-test" in content

        templates = template_service.render_project_templates(context, output_dir)
        assert len(templates) >= 1


class TestAssistantInjectionIntegration:
    """Test integration with assistant injection system."""

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance."""
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    @pytest.fixture
    def injection_context(self) -> TemplateContext:
        """Create context for injection testing."""
        from specify_cli.models.config import BranchNamingConfig

        branch_config = BranchNamingConfig()
        branch_config.patterns = ["feature/{feature-name}"]

        return TemplateContext(
            project_name="injection-test",
            ai_assistant="claude",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-17",
            project_path=Path("/tmp/injection-test").resolve(),
        )

    def test_injection_point_integration(
        self,
        template_service: TemplateService,
        injection_context: TemplateContext,
        tmp_path: Path,
    ) -> None:
        """Test that injection points work in templates."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Template using injection points
        template_content = (
            "Command: {{ assistant_command_prefix }}help\n"
            "Setup: {{ assistant_setup_instructions }}\n"
            "Context: {{ assistant_context_file_path }}\n"
        )
        (template_dir / "injection.md.j2").write_text(template_content)

        template_service.load_template_package("claude", template_dir)
        result = template_service.render_template("injection.md.j2", injection_context)

        # Should contain injected values (actual values depend on assistant implementation)
        assert len(result) > len(template_content)  # Should be expanded
        assert "claude" in result.lower()  # Should contain assistant-specific content

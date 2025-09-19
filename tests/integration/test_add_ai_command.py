"""
Integration tests for the add-ai command end-to-end workflows.

Tests complete workflows involving multiple services and real file operations.
Does not use heavy mocking - focuses on actual integration behavior.
"""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli.core.app import app


class TestAddAiCommandIntegration:
    """Test add-ai command end-to-end integration workflows."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary SpecifyX project for integration testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            # Create basic SpecifyX project structure
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "config.toml").write_text("""
[project]
name = "test-project"

[project.template_settings]
ai_assistants = []
config_directory = ".specify"
""")
            yield project_path

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_add_ai_command_injection_points_display(self, runner):
        """Test that --injection-points displays information and exits cleanly."""
        result = runner.invoke(app, ["add-ai", "--injection-points"])

        assert result.exit_code == 0
        assert "Required Injection Points" in result.stdout
        assert "Optional Injection Points" in result.stdout

    def test_add_ai_command_list_status_in_project(self, runner, temp_project_dir):
        """Test --list flag shows assistant status in a SpecifyX project."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)
            result = runner.invoke(app, ["add-ai", "--list"])

            # Should succeed in project directory
            assert result.exit_code == 0
            # Should show a table with assistant information
            assert "Assistant" in result.stdout or "Status" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_add_ai_command_not_in_project(self, runner):
        """Test command behavior when not in a SpecifyX project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)  # Empty directory, not a SpecifyX project
                result = runner.invoke(app, ["add-ai", "claude"])

                assert result.exit_code == 1
                assert "not a SpecifyX project" in result.stdout
            finally:
                os.chdir(original_cwd)

    def test_add_ai_command_show_values_for_assistant(self, runner):
        """Test --show-values for a valid assistant."""
        result = runner.invoke(app, ["add-ai", "claude", "--show-values"])

        # Should succeed regardless of project status when showing values
        assert result.exit_code == 0
        # Should show injection point values for Claude
        assert "claude" in result.stdout.lower()

    def test_add_ai_command_unknown_assistant(self, runner):
        """Test behavior with unknown assistant name."""
        result = runner.invoke(
            app, ["add-ai", "nonexistent_assistant", "--show-values"]
        )

        assert result.exit_code == 1
        assert "Unknown assistant" in result.stdout

    def test_add_ai_command_dry_run_workflow(self, runner, temp_project_dir):
        """Test complete dry-run workflow in a project."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)
            result = runner.invoke(app, ["add-ai", "claude", "--dry-run"])

            # Should show what files would be created
            assert result.exit_code == 0
            assert (
                "would be created" in result.stdout
                or "Files that would be" in result.stdout
            )
        finally:
            os.chdir(original_cwd)


class TestAddAiCommandFileIntegration:
    """Test add-ai command integration with file system operations."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary SpecifyX project for file integration testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            # Create basic SpecifyX project structure
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "config.toml").write_text("""
[project]
name = "integration-test"

[project.template_settings]
ai_assistants = []
config_directory = ".specify"
""")
            yield project_path

    def test_assistant_status_detection_with_real_files(self, temp_project_dir):
        """Test status detection with actual file operations."""
        from rich.console import Console

        from specify_cli.services import (
            AssistantManagementService,
            CommandLineGitService,
            TomlConfigService,
        )
        from specify_cli.services.project_manager import ProjectManager

        # Create the service
        project_manager = ProjectManager(
            config_service=TomlConfigService(),
            git_service=CommandLineGitService(),
        )
        assistant_service = AssistantManagementService(
            project_manager=project_manager,
            console=Console(),
        )

        # Initially missing (no files exist)
        status = assistant_service.check_assistant_status(temp_project_dir, "claude")
        assert status == "missing"

        # Create partial structure
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir()
        status = assistant_service.check_assistant_status(temp_project_dir, "claude")
        assert status == "partial"

        # Create context file at the project root (CLAUDE.md, not .claude/CLAUDE.md)
        (temp_project_dir / "CLAUDE.md").write_text("# Claude Context")
        status = assistant_service.check_assistant_status(temp_project_dir, "claude")
        assert status == "partial"  # Still missing commands directory

        # Create commands directory
        (claude_dir / "commands").mkdir()
        status = assistant_service.check_assistant_status(temp_project_dir, "claude")
        assert status == "configured"

    def test_file_creation_paths_integration(self, temp_project_dir):
        """Test file path generation for different assistants."""
        from rich.console import Console

        from specify_cli.services import (
            AssistantManagementService,
            CommandLineGitService,
            TomlConfigService,
        )
        from specify_cli.services.project_manager import ProjectManager

        # Create the service
        project_manager = ProjectManager(
            config_service=TomlConfigService(),
            git_service=CommandLineGitService(),
        )
        assistant_service = AssistantManagementService(
            project_manager=project_manager,
            console=Console(),
        )

        files = assistant_service.get_files_to_create("claude", temp_project_dir)

        # Should return relative paths
        assert all(not str(file).startswith("/") for file in files)
        # Should include Claude-specific paths
        assert any(".claude" in str(file) for file in files)


class TestAddAiCommandServiceIntegration:
    """Test add-ai command integration with core services."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for service integration testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_assistant_registry_integration(self):
        """Test integration with assistant registry."""
        from specify_cli.assistants import get_assistant, list_assistant_names

        # Should be able to list available assistants
        assistants = list_assistant_names()
        assert isinstance(assistants, list)
        assert len(assistants) > 0

        # Should be able to load at least one assistant
        if assistants:
            assistant = get_assistant(assistants[0])
            assert assistant is not None
            assert hasattr(assistant, "config")

    def test_project_manager_integration(self, temp_project_dir):
        """Test integration with project manager."""
        from specify_cli.services.project_manager import ProjectManager

        # Should be able to create project manager
        manager = ProjectManager()
        assert manager is not None

        # Should detect project initialization status
        is_initialized = manager.is_project_initialized(temp_project_dir)
        assert isinstance(is_initialized, bool)

    def test_template_service_integration(self):
        """Test integration with template service."""
        from specify_cli.services.template_service import JinjaTemplateService

        # Should be able to create template service
        service = JinjaTemplateService()
        assert service is not None

        # Should have basic template operations available
        assert hasattr(service, "render_template")
        assert hasattr(service, "load_template_package")


class TestAddAiCommandWorkflowIntegration:
    """Test complete add-ai command workflows."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_help_and_documentation_workflow(self, runner):
        """Test help and documentation access workflow."""
        # Test main help
        result = runner.invoke(app, ["add-ai", "--help"])
        assert result.exit_code == 0
        assert "add-ai" in result.stdout

        # Test injection points info
        result = runner.invoke(app, ["add-ai", "--injection-points"])
        assert result.exit_code == 0
        assert "injection" in result.stdout.lower()

    def test_assistant_discovery_workflow(self, runner):
        """Test assistant discovery and information workflow."""
        # Test showing values for known assistant
        result = runner.invoke(app, ["add-ai", "claude", "--show-values"])
        assert result.exit_code == 0

        # Test error handling for unknown assistant
        result = runner.invoke(app, ["add-ai", "unknown", "--show-values"])
        assert result.exit_code == 1

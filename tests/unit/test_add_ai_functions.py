"""
Unit tests for AssistantManagementService.

Tests individual service methods with controlled inputs and mocked dependencies.
Focuses on business logic validation and error handling.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from specify_cli.assistants.injection_points import InjectionPoint
from specify_cli.assistants.types import (
    AssistantConfig,
    ContextFileConfig,
    FileFormat,
    TemplateConfig,
)
from specify_cli.services.assistant_management_service import AssistantManagementService


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
    provider = Mock()
    provider.config = mock_assistant_config
    provider.get_injection_values.return_value = {
        InjectionPoint.COMMAND_PREFIX: "test ",
        InjectionPoint.SETUP_INSTRUCTIONS: "Install test CLI and run 'test auth'",
        InjectionPoint.CONTEXT_FILE_PATH: ".test/TEST.md",
    }
    return provider


@pytest.fixture
def assistant_service():
    """Create an AssistantManagementService with mocked dependencies."""
    mock_project_manager = Mock()
    mock_config_service = Mock()
    console = Console()

    return AssistantManagementService(
        project_manager=mock_project_manager,
        config_service=mock_config_service,
        console=console,
    )


class TestStatusCheckingFunctions:
    """Test status checking business logic."""

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    def test_check_assistant_status_missing_assistant(
        self, mock_get_assistant, assistant_service
    ):
        """Test status when assistant doesn't exist."""
        mock_get_assistant.return_value = None

        status = assistant_service.check_assistant_status(Path("/tmp"), "nonexistent")
        assert status == "missing"

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    @patch("pathlib.Path.exists")
    def test_check_assistant_status_missing_files(
        self,
        mock_exists,
        mock_get_assistant,
        mock_assistant_provider,
        assistant_service,
    ):
        """Test status when assistant exists but files are missing."""
        mock_get_assistant.return_value = mock_assistant_provider
        mock_exists.return_value = False

        status = assistant_service.check_assistant_status(
            Path("/tmp"), "test_assistant"
        )
        assert status == "missing"

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    def test_check_assistant_status_partial_configuration(
        self, mock_get_assistant, mock_assistant_provider, assistant_service
    ):
        """Test status when some files exist but configuration is incomplete."""
        mock_get_assistant.return_value = mock_assistant_provider

        # Mock the path exists behavior to simulate partial configuration
        # Base directory exists, context file doesn't exist, commands directory exists
        with patch("pathlib.Path.exists") as mock_exists:
            # Return True for base and commands directory, False for context file
            call_count = [0]

            def side_effect():
                call_count[0] += 1
                if call_count[0] == 1:  # base directory
                    return True
                else:
                    return call_count[0] != 2  # context file

            mock_exists.side_effect = side_effect

            status = assistant_service.check_assistant_status(
                Path("/tmp"), "test_assistant"
            )
            assert status == "partial"

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    @patch("pathlib.Path.exists")
    def test_check_assistant_status_fully_configured(
        self,
        mock_exists,
        mock_get_assistant,
        mock_assistant_provider,
        assistant_service,
    ):
        """Test status when assistant is fully configured."""
        mock_get_assistant.return_value = mock_assistant_provider
        mock_exists.return_value = True

        status = assistant_service.check_assistant_status(
            Path("/tmp"), "test_assistant"
        )
        assert status == "configured"

    def test_get_status_text_configured(self, assistant_service):
        """Test status text for configured status."""
        result = assistant_service.get_status_text("configured")
        assert "[green]✓ Configured[/green]" in result

    def test_get_status_text_partial(self, assistant_service):
        """Test status text for partial status."""
        result = assistant_service.get_status_text("partial")
        assert "[yellow]⚠️  Partially configured[/yellow]" in result

    def test_get_status_text_missing(self, assistant_service):
        """Test status text for missing status."""
        result = assistant_service.get_status_text("missing")
        assert "[red]✗ Not configured[/red]" in result


class TestFileOperations:
    """Test file creation and management."""

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    def test_get_files_to_create_structure(
        self, mock_get_assistant, mock_assistant_provider, assistant_service
    ):
        """Test that get_files_to_create returns expected file structure."""
        mock_get_assistant.return_value = mock_assistant_provider

        files = assistant_service.get_files_to_create("test_assistant", Path("/tmp"))

        # Check that we get the expected files
        assert ".test/TEST.md" in files
        assert ".test/commands/" in files
        assert ".test/agents/" in files

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    def test_get_files_to_create_missing_assistant(
        self, mock_get_assistant, assistant_service
    ):
        """Test get_files_to_create with missing assistant."""
        mock_get_assistant.return_value = None

        files = assistant_service.get_files_to_create("nonexistent", Path("/tmp"))
        assert files == []


class TestAssistantCreation:
    """Test assistant file creation."""

    def test_create_assistant_files_basic_flow(self, assistant_service):
        """Test basic assistant file creation flow."""
        # Mock the private method to return success
        assistant_service._create_ai_only_files = Mock(return_value=True)

        result = assistant_service.create_assistant_files(
            Path("/tmp"), "test_assistant", force=False
        )

        assert result is True
        assistant_service._create_ai_only_files.assert_called_once()

    def test_create_assistant_files_handles_exception(self, assistant_service):
        """Test that create_assistant_files handles exceptions gracefully."""
        # Mock the private method to raise an exception
        assistant_service._create_ai_only_files = Mock(
            side_effect=Exception("Test error")
        )

        result = assistant_service.create_assistant_files(
            Path("/tmp"), "test_assistant", force=False
        )

        assert result is False


class TestInjectionPointDisplay:
    """Test injection point information display."""

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    def test_show_assistant_injection_values_missing_assistant(
        self, mock_get_assistant, assistant_service
    ):
        """Test showing injection values for missing assistant."""
        mock_get_assistant.return_value = None

        # This should not raise an exception
        assistant_service.show_assistant_injection_values("nonexistent")
        mock_get_assistant.assert_called_once_with("nonexistent")

    @patch(
        "specify_cli.services.assistant_management_service.assistant_management_service.get_assistant"
    )
    def test_show_assistant_injection_values_success(
        self, mock_get_assistant, mock_assistant_provider, assistant_service
    ):
        """Test successful display of injection values."""
        mock_get_assistant.return_value = mock_assistant_provider

        # This should not raise an exception
        assistant_service.show_assistant_injection_values("test_assistant")
        mock_get_assistant.assert_called_once_with("test_assistant")
        mock_assistant_provider.get_injection_values.assert_called_once()

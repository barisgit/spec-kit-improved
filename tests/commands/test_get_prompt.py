"""Tests for the get-prompt command."""

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from specify_cli.core.app import app


class TestGetPromptCommand:
    """Test cases for the get-prompt command."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_get_prompt_help(self):
        """Test that get-prompt help works."""
        result = self.runner.invoke(app, ["get-prompt", "--help"])
        assert result.exit_code == 0
        assert "Generate global system prompt for AI assistant" in result.stdout

    def test_get_prompt_success(self):
        """Test get-prompt command generates universal prompt."""
        result = self.runner.invoke(app, ["get-prompt"])
        assert result.exit_code == 0
        assert "SpecifyX Universal System Prompt Generated" in result.stdout
        assert "All AI Assistants" in result.stdout
        assert "Global (all projects)" in result.stdout

    def test_get_prompt_output_file(self):
        """Test get-prompt command with output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = self.runner.invoke(
                app,
                ["get-prompt", "--output", tmp_path],
            )
            assert result.exit_code == 0
            assert "System prompt saved to" in result.stdout

            # Verify file was created and has content
            output_path = Path(tmp_path)
            assert output_path.exists()
            content = output_path.read_text()
            assert "SpecifyX Workflow Integration" in content
            assert "SpecifyX Detection" in content
            assert "NEVER hardcode values" in content
            assert len(content) > 500  # Should be substantial content

        finally:
            # Cleanup
            Path(tmp_path).unlink(missing_ok=True)

    def test_get_prompt_content_includes_key_sections(self):
        """Test that generated prompt includes all key sections."""
        result = self.runner.invoke(app, ["get-prompt"])
        assert result.exit_code == 0

        # Check for key sections in the output
        assert "SpecifyX Detection" in result.stdout
        assert "SpecifyX Project Behavior" in result.stdout
        assert "Core Workflow" in result.stdout
        assert "NEVER hardcode values" in result.stdout
        assert "Non-SpecifyX Projects" in result.stdout
        assert "Global Guidelines" in result.stdout

    def test_get_prompt_emphasizes_no_hardcoding(self):
        """Test that the prompt strongly emphasizes no hardcoding."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = self.runner.invoke(app, ["get-prompt", "--output", tmp_path])
            assert result.exit_code == 0

            # Check the actual file content for all anti-hardcoding terms
            content = Path(tmp_path).read_text()
            assert "NEVER hardcode values" in content
            assert "configuration files" in content
            assert "environment variables" in content
            assert "named constants" in content

        finally:
            Path(tmp_path).unlink(missing_ok=True)

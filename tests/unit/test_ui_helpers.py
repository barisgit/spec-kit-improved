"""
Unit tests for ui_helpers module.

Tests the UI helper functions for interactive project initialization.
"""

from unittest.mock import Mock, patch

import pytest

from specify_cli.models.config import BranchNamingConfig
from specify_cli.utils.ui_helpers import (
    select_ai_assistant,
    select_branch_naming_pattern,
)


class TestSelectBranchNamingPattern:
    """Test the select_branch_naming_pattern function."""

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("rich.console.Console")
    @patch("specify_cli.utils.ui_helpers.BRANCH_DEFAULTS")
    def test_select_branch_naming_pattern_success(
        self, mock_branch_defaults, _mock_console, mock_ui_class
    ):
        """Test successful branch naming pattern selection."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.return_value = "feature-based"

        mock_pattern_options = {
            "feature-based": {
                "display": "Feature-based",
                "description": "Feature-based naming",
                "patterns": ["feature/{feature-name}", "hotfix/{bug-id}"],
                "validation_rules": ["max_length_50", "lowercase_only"],
            }
        }
        mock_branch_defaults.get_pattern_options_for_ui.return_value = (
            mock_pattern_options
        )
        mock_branch_defaults.DEFAULT_PATTERN_NAME = "feature-based"

        # Call function
        result = select_branch_naming_pattern()

        # Assertions
        assert isinstance(result, BranchNamingConfig)
        assert result.description == "Feature-based naming"
        assert result.patterns == ["feature/{feature-name}", "hotfix/{bug-id}"]
        assert result.validation_rules == ["max_length_50", "lowercase_only"]

        # Verify UI interactions
        mock_ui.select.assert_called_once()
        call_args = mock_ui.select.call_args
        assert "Select your preferred branch naming pattern:" in call_args[0][0]
        assert "feature-based" in call_args[1]["choices"]

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("rich.console.Console")
    @patch("specify_cli.utils.ui_helpers.BRANCH_DEFAULTS")
    def test_select_branch_naming_pattern_keyboard_interrupt(
        self, mock_branch_defaults, _mock_console, mock_ui_class
    ):
        """Test handling keyboard interrupt during selection."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.side_effect = KeyboardInterrupt()

        mock_pattern_options = {
            "feature-based": {
                "display": "Feature-based",
                "description": "Feature-based naming",
                "patterns": ["feature/{feature-name}"],
                "validation_rules": ["max_length_50"],
            }
        }
        mock_branch_defaults.get_pattern_options_for_ui.return_value = (
            mock_pattern_options
        )
        mock_branch_defaults.DEFAULT_PATTERN_NAME = "feature-based"

        # Call function and expect KeyboardInterrupt to be re-raised
        with pytest.raises(KeyboardInterrupt):
            select_branch_naming_pattern()

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("rich.console.Console")
    @patch("specify_cli.utils.ui_helpers.BRANCH_DEFAULTS")
    def test_select_branch_naming_pattern_multiple_options(
        self, mock_branch_defaults, _mock_console, mock_ui_class
    ):
        """Test selection with multiple branch naming options."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.return_value = "gitflow"

        mock_pattern_options = {
            "feature-based": {
                "display": "Feature-based",
                "description": "Feature-based naming",
                "patterns": ["feature/{feature-name}"],
                "validation_rules": ["max_length_50"],
            },
            "gitflow": {
                "display": "GitFlow",
                "description": "GitFlow naming convention",
                "patterns": [
                    "feature/{feature-name}",
                    "release/{version}",
                    "hotfix/{bug-id}",
                ],
                "validation_rules": ["max_length_50", "lowercase_only", "no_spaces"],
            },
            "simple": {
                "display": "Simple",
                "description": "Simple naming",
                "patterns": ["{feature-name}"],
                "validation_rules": ["max_length_30"],
            },
        }
        mock_branch_defaults.get_pattern_options_for_ui.return_value = (
            mock_pattern_options
        )
        mock_branch_defaults.DEFAULT_PATTERN_NAME = "feature-based"

        # Call function
        result = select_branch_naming_pattern()

        # Assertions
        assert isinstance(result, BranchNamingConfig)
        assert result.description == "GitFlow naming convention"
        assert result.patterns == [
            "feature/{feature-name}",
            "release/{version}",
            "hotfix/{bug-id}",
        ]
        assert result.validation_rules == [
            "max_length_50",
            "lowercase_only",
            "no_spaces",
        ]

        # Verify all options were presented
        call_args = mock_ui.select.call_args
        choices = call_args[1]["choices"]
        assert len(choices) == 3
        assert "feature-based" in choices
        assert "gitflow" in choices
        assert "simple" in choices

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("specify_cli.utils.ui_helpers.BRANCH_DEFAULTS")
    def test_select_branch_naming_pattern_ui_interaction(
        self, mock_branch_defaults, mock_ui_class
    ):
        """Test that UI interaction is properly configured."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.return_value = "feature-based"

        mock_pattern_options = {
            "feature-based": {
                "display": "Feature-based",
                "description": "Feature-based naming",
                "patterns": ["feature/{feature-name}"],
                "validation_rules": ["max_length_50"],
            }
        }
        mock_branch_defaults.get_pattern_options_for_ui.return_value = (
            mock_pattern_options
        )
        mock_branch_defaults.DEFAULT_PATTERN_NAME = "feature-based"

        # Call function
        result = select_branch_naming_pattern()

        # Verify UI interactions
        mock_ui_class.assert_called_once()
        mock_ui.select.assert_called_once()

        # Verify the select call arguments
        call_args = mock_ui.select.call_args
        assert call_args[0][0] == "Select your preferred branch naming pattern:"
        assert "feature-based" in call_args[1]["choices"]
        assert call_args[1]["default"] == "feature-based"
        assert "Choose how your project will name branches" in call_args[1]["header"]

        # Verify return value
        assert isinstance(result, BranchNamingConfig)
        assert result.description == "Feature-based naming"
        assert result.patterns == ["feature/{feature-name}"]
        assert result.validation_rules == ["max_length_50"]


class TestSelectAiAssistant:
    """Test the select_ai_assistant function."""

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("specify_cli.utils.ui_helpers.get_all_assistants")
    def test_select_ai_assistant_success(self, mock_get_assistants, mock_ui_class):
        """Test successful AI assistant selection."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.return_value = "claude"

        # Mock AI assistants
        mock_assistant1 = Mock()
        mock_assistant1.config.name = "claude"
        mock_assistant1.config.display_name = "Claude"
        mock_assistant1.config.description = "Anthropic's AI assistant"

        mock_assistant2 = Mock()
        mock_assistant2.config.name = "gemini"
        mock_assistant2.config.display_name = "Gemini"
        mock_assistant2.config.description = "Google's AI assistant"

        mock_get_assistants.return_value = [mock_assistant1, mock_assistant2]

        # Call function
        result = select_ai_assistant()

        # Assertions
        assert result == "claude"

        # Verify UI interactions
        mock_ui.select.assert_called_once()
        call_args = mock_ui.select.call_args
        assert "Choose your AI assistant:" in call_args[0][0]

        # Check choices
        choices = call_args[1]["choices"]
        assert "claude" in choices
        assert "gemini" in choices
        assert "Claude (Anthropic's AI assistant)" in choices["claude"]
        assert "Gemini (Google's AI assistant)" in choices["gemini"]

        # Check default
        assert call_args[1]["default"] == "claude"

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("specify_cli.utils.ui_helpers.get_all_assistants")
    def test_select_ai_assistant_keyboard_interrupt(
        self, mock_get_assistants, mock_ui_class
    ):
        """Test handling keyboard interrupt during AI assistant selection."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.side_effect = KeyboardInterrupt()

        # Mock AI assistants
        mock_assistant = Mock()
        mock_assistant.config.name = "claude"
        mock_assistant.config.display_name = "Claude"
        mock_assistant.config.description = "Anthropic's AI assistant"
        mock_get_assistants.return_value = [mock_assistant]

        # Call function and expect KeyboardInterrupt to be re-raised
        with pytest.raises(KeyboardInterrupt):
            select_ai_assistant()

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("specify_cli.utils.ui_helpers.get_all_assistants")
    def test_select_ai_assistant_multiple_options(
        self, mock_get_assistants, mock_ui_class
    ):
        """Test selection with multiple AI assistant options."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.return_value = "copilot"

        # Mock AI assistants
        mock_assistant1 = Mock()
        mock_assistant1.config.name = "claude"
        mock_assistant1.config.display_name = "Claude"
        mock_assistant1.config.description = "Anthropic's AI assistant"

        mock_assistant2 = Mock()
        mock_assistant2.config.name = "gemini"
        mock_assistant2.config.display_name = "Gemini"
        mock_assistant2.config.description = "Google's AI assistant"

        mock_assistant3 = Mock()
        mock_assistant3.config.name = "copilot"
        mock_assistant3.config.display_name = "GitHub Copilot"
        mock_assistant3.config.description = "GitHub's AI coding assistant"

        mock_get_assistants.return_value = [
            mock_assistant1,
            mock_assistant2,
            mock_assistant3,
        ]

        # Call function
        result = select_ai_assistant()

        # Assertions
        assert result == "copilot"

        # Verify all options were presented
        call_args = mock_ui.select.call_args
        choices = call_args[1]["choices"]
        assert len(choices) == 3
        assert "claude" in choices
        assert "gemini" in choices
        assert "copilot" in choices

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("specify_cli.utils.ui_helpers.get_all_assistants")
    def test_select_ai_assistant_empty_list(self, mock_get_assistants, mock_ui_class):
        """Test handling empty AI assistants list."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.return_value = None

        mock_get_assistants.return_value = []

        # Call function
        result = select_ai_assistant()

        # Assertions
        assert result is None

        # Verify UI was called with empty choices
        call_args = mock_ui.select.call_args
        choices = call_args[1]["choices"]
        assert choices == {}

    @patch("specify_cli.utils.ui_helpers.InteractiveUI")
    @patch("specify_cli.utils.ui_helpers.get_all_assistants")
    def test_select_ai_assistant_default_selection(
        self, mock_get_assistants, mock_ui_class
    ):
        """Test that default selection works correctly."""
        # Setup mocks
        mock_ui = Mock()
        mock_ui_class.return_value = mock_ui
        mock_ui.select.return_value = "claude"

        # Mock AI assistants
        mock_assistant1 = Mock()
        mock_assistant1.config.name = "claude"
        mock_assistant1.config.display_name = "Claude"
        mock_assistant1.config.description = "Anthropic's AI assistant"

        mock_assistant2 = Mock()
        mock_assistant2.config.name = "gemini"
        mock_assistant2.config.display_name = "Gemini"
        mock_assistant2.config.description = "Google's AI assistant"

        mock_get_assistants.return_value = [mock_assistant1, mock_assistant2]

        # Call function
        select_ai_assistant()

        # Verify default was set correctly
        call_args = mock_ui.select.call_args
        assert call_args[1]["default"] == "claude"

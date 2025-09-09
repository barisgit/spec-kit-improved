"""
Integration test for interactive init command with branch pattern selection.

This test is for Test-Driven Development (TDD) and MUST FAIL initially
since the enhanced interactive functionality is not yet fully implemented.

Based on Quickstart Specification (Scenario 1-3) and Requirements:
- Interactive branch pattern selection during init
- AI assistant selection works alongside branch pattern selection
- Configuration is properly saved to .specify/config.toml
- Full interactive flow validation
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import typer for Exit exception handling
from typer.testing import CliRunner

from specify_cli.core.app import app
from specify_cli.models.config import BranchNamingConfig, ProjectConfig, TemplateConfig


class TestInteractiveInitCommand:
    """
    Integration tests for interactive init command with branch pattern selection.

    CRITICAL TDD REQUIREMENTS:
    - These tests MUST FAIL initially since enhanced interactive functionality is not fully implemented
    - Key failing areas: branch_pattern integration, configuration persistence, script generation
    - Tests validate integration between UI prompts, project options, and final project structure
    - Based on quickstart validation scenarios from specs/002-as-outlined-in/quickstart.md

    SUCCESS CRITERIA (will fail initially):
    1. Interactive prompts collect both AI assistant and branch pattern choices
    2. Selected branch pattern is passed to ProjectManager via ProjectInitOptions
    3. Configuration files reflect selected branch pattern as default pattern
    4. Generated scripts include branch pattern logic
    5. Error handling works for invalid choices and cancellation
    """

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing"""
        # Register commands before testing
        from specify_cli.core.app import register_commands

        register_commands()
        return CliRunner()

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary directory for project testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                yield Path(temp_dir)
            finally:
                os.chdir(original_cwd)

    @pytest.fixture
    def mock_project_manager(self):
        """Mock project manager that simulates successful initialization"""
        with patch("specify_cli.commands.init.init.get_project_manager") as mock_pm:
            manager = MagicMock()

            # Mock successful project initialization
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.project_path = Path("test-project")
            mock_result.completed_steps = ["validation", "creation", "templates"]
            mock_result.error_message = None

            manager.initialize_project.return_value = mock_result
            mock_pm.return_value = manager
            yield manager

    def test_interactive_init_with_claude_and_traditional_pattern(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test interactive init with Claude assistant and traditional branch pattern.

        Covers Scenario 1 from quickstart: Interactive init with default settings
        Expected to FAIL initially - interactive prompting not fully implemented
        """
        # Mock UI selections: claude assistant, traditional pattern
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # First call: AI assistant selection returns "claude"
            # Second call: Branch pattern selection returns "001-feature-name"
            mock_ui.select.side_effect = ["claude", "001-feature-name"]

            # Run the command
            result = cli_runner.invoke(
                app, ["init", "test-project"], catch_exceptions=False
            )

        # Verify the command completed successfully
        assert result.exit_code == 0

        # Verify interactive prompts were called
        assert mock_ui.select.call_count == 2

        # Verify AI assistant prompt
        ai_call = mock_ui.select.call_args_list[0]
        # First argument is the message (positional)
        assert "Choose your AI assistant:" in str(ai_call[0])
        # Second argument is choices (keyword)
        assert "claude" in str(ai_call[1]["choices"])
        assert "gemini" in str(ai_call[1]["choices"])
        assert "copilot" in str(ai_call[1]["choices"])

        # Verify branch pattern prompt
        pattern_call = mock_ui.select.call_args_list[1]
        # First argument is the message (positional)
        assert "Choose your branch naming pattern:" in str(pattern_call[0])
        # Second argument is choices (keyword)
        assert "001-feature-name" in str(pattern_call[1]["choices"])
        assert "feature/{name}" in str(pattern_call[1]["choices"])

        # Verify project manager was called with correct options
        init_call = mock_project_manager.initialize_project.call_args[0][0]
        assert init_call.project_name == "test-project"
        assert init_call.ai_assistant == "claude"
        assert init_call.use_current_dir is False

        # CRITICAL TEST: Verify branch pattern is passed to project manager
        # This will FAIL initially since branch pattern integration may not be complete
        assert hasattr(init_call, "branch_pattern"), (
            "ProjectInitOptions should have branch_pattern field"
        )
        assert init_call.branch_pattern == "001-feature-name", (
            "Selected branch pattern should be passed to project manager"
        )

        # Check success message appears in output
        assert "Project initialized successfully" in result.stdout

    def test_interactive_init_with_gemini_and_modern_pattern(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test interactive init with Gemini assistant and modern branch pattern.

        Expected to FAIL initially - branch pattern integration not implemented
        """
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # Mock selections: gemini assistant, modern pattern
            mock_ui.select.side_effect = ["gemini", "feature/{name}"]

            result = cli_runner.invoke(
                app, ["init", "gemini-project"], catch_exceptions=False
            )

        assert result.exit_code == 0
        assert mock_ui.select.call_count == 2

        # Verify correct selections
        init_call = mock_project_manager.initialize_project.call_args[0][0]
        assert init_call.ai_assistant == "gemini"

    def test_interactive_init_here_flag_with_copilot(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test interactive init with --here flag and Copilot assistant.

        Expected to FAIL initially - current directory initialization integration
        """
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # Mock selections: copilot assistant, traditional pattern
            mock_ui.select.side_effect = ["copilot", "001-feature-name"]

            result = cli_runner.invoke(app, ["init", "--here"], catch_exceptions=False)

        assert result.exit_code == 0

        # Verify use_current_dir is True
        init_call = mock_project_manager.initialize_project.call_args[0][0]
        assert init_call.use_current_dir is True
        assert init_call.project_name is None
        assert init_call.ai_assistant == "copilot"

    def test_non_interactive_init_with_cli_options(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test non-interactive init when all options provided via CLI.

        Covers Scenario 2 from quickstart: Non-Interactive Init with Custom Pattern
        Expected to FAIL initially - CLI options not fully wired to config
        """
        result = cli_runner.invoke(
            app,
            [
                "init",
                "--ai",
                "gemini",
                "--branch-pattern",
                "feature/{name}",
                "cli-project",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        # Verify project manager called with CLI options
        init_call = mock_project_manager.initialize_project.call_args[0][0]
        assert init_call.project_name == "cli-project"
        assert init_call.ai_assistant == "gemini"

    def test_interactive_init_cancellation_during_ai_selection(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test cancellation during AI assistant selection.

        Covers Scenario 4 from quickstart: Cancellation Test
        Expected to FAIL initially - cancellation handling not implemented
        """
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # Simulate KeyboardInterrupt during AI selection
            mock_ui.select.side_effect = KeyboardInterrupt()

            result = cli_runner.invoke(
                app, ["init", "cancelled-project"], catch_exceptions=False
            )

        # Should exit with code 0 (cancelled cleanly)
        assert result.exit_code == 0
        assert "Setup cancelled" in result.stdout

        # Project manager should not be called
        mock_project_manager.initialize_project.assert_not_called()

    def test_interactive_init_cancellation_during_branch_pattern_selection(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test cancellation during branch pattern selection.

        Expected to FAIL initially - second prompt cancellation not handled
        """
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # First call succeeds, second call is cancelled
            mock_ui.select.side_effect = ["claude", KeyboardInterrupt()]

            result = cli_runner.invoke(
                app, ["init", "cancelled-project"], catch_exceptions=False
            )

        assert result.exit_code == 0
        assert "Setup cancelled" in result.stdout

    def test_config_file_generation_with_selected_options(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test that .specify/config.toml is created with selected options.

        This is the key integration test for configuration persistence.
        Expected to FAIL initially - config generation not implemented
        """
        project_dir = temp_project_dir / "config-test-project"

        # Mock project manager to create actual config file
        def mock_init_project(options):
            # Create project directory structure
            project_dir.mkdir(parents=True, exist_ok=True)
            specify_dir = project_dir / ".specify"
            specify_dir.mkdir(exist_ok=True)

            # Create expected config based on selections
            config = ProjectConfig(
                name="config-test-project",
                branch_naming=BranchNamingConfig(
                    description="Modern feature branches with hotfixes and main branches",
                    patterns=[
                        "feature/{name}",
                        "hotfix/{bug-id}",
                        "main",
                        "development",
                    ],
                    validation_rules=["max_length_50", "lowercase_only", "no_spaces"],
                ),
                template_settings=TemplateConfig(
                    ai_assistant="gemini", config_directory=".specify"
                ),
            )

            # Write config to TOML file
            config_file = specify_dir / "config.toml"
            config_content = f"""[project]
name = "{config.name}"

[project.branch_naming]
description = "{config.branch_naming.description}"
patterns = {config.branch_naming.patterns}
validation_rules = {config.branch_naming.validation_rules}

[project.template_settings]
ai_assistant = "{config.template_settings.ai_assistant}"
config_directory = "{config.template_settings.config_directory}"
template_cache_enabled = true
"""
            config_file.write_text(config_content)

            # Return mock result
            result = MagicMock()
            result.success = True
            result.project_path = project_dir
            result.completed_steps = ["validation", "creation", "config"]
            return result

        mock_project_manager.initialize_project.side_effect = mock_init_project

        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # Select gemini and modern branch pattern
            mock_ui.select.side_effect = ["gemini", "feature/{name}"]

            result = cli_runner.invoke(
                app, ["init", "config-test-project"], catch_exceptions=False
            )

        assert result.exit_code == 0

        # Verify config file was created
        config_file = project_dir / ".specify" / "config.toml"
        assert config_file.exists(), "Config file should be created"

        # Verify config content
        config_content = config_file.read_text()
        assert 'ai_assistant = "gemini"' in config_content
        # Handle both single and double quotes in TOML
        assert (
            'patterns = ["feature/{name}"' in config_content
            or "patterns = ['feature/{name}'" in config_content
        )
        assert 'name = "config-test-project"' in config_content

        # CRITICAL TEST: Verify that selected branch pattern becomes the default pattern
        # This is a key integration requirement that will FAIL initially
        # The selected pattern should be set as the primary/default pattern in config
        assert (
            'default_pattern = "feature/{name}"' in config_content
            or 'default_pattern = "feature/{feature-name}"' in config_content
        ), "Selected branch pattern should become the default pattern in config"

    def test_invalid_ai_assistant_error_handling(self, cli_runner, temp_project_dir):
        """
        Test error handling for invalid AI assistant choice.

        Covers Scenario 4 from quickstart: Error Handling
        """
        result = cli_runner.invoke(
            app, ["init", "--ai", "invalid-ai", "error-project"], catch_exceptions=False
        )

        assert result.exit_code == 1
        assert "Invalid AI assistant 'invalid-ai'" in result.stdout
        assert "Choose from: claude, gemini, copilot" in result.stdout

    def test_invalid_branch_pattern_error_handling(self, cli_runner, temp_project_dir):
        """
        Test error handling for invalid branch pattern choice.

        Expected to FAIL initially - branch pattern validation not implemented
        """
        result = cli_runner.invoke(
            app,
            ["init", "--branch-pattern", "invalid-pattern", "error-project"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "Invalid branch pattern 'invalid-pattern'" in result.stdout
        assert "Choose from:" in result.stdout

    def test_project_already_exists_error(self, cli_runner, temp_project_dir):
        """
        Test error when project directory already exists.
        """
        existing_project = temp_project_dir / "existing-project"
        existing_project.mkdir()

        result = cli_runner.invoke(
            app, ["init", "existing-project"], catch_exceptions=False
        )

        assert result.exit_code == 1
        assert "Directory 'existing-project' already exists" in result.stdout

    def test_branch_pattern_options_structure(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test that branch pattern options match the data model structure.

        This test validates the predefined branch naming patterns from
        the BranchNamingConfig data model are properly presented.

        Expected to FAIL initially - full pattern integration not implemented
        """
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # Mock both selections
            mock_ui.select.side_effect = ["claude", "001-feature-name"]

            cli_runner.invoke(app, ["init", "pattern-test"], catch_exceptions=False)

        # Verify the branch pattern selection call includes expected options
        pattern_call = mock_ui.select.call_args_list[1]
        choices = pattern_call[1]["choices"]

        # Should include traditional and modern patterns
        assert "001-feature-name" in choices
        assert "feature/{name}" in choices

        # Verify pattern descriptions are meaningful
        assert "Traditional numbered format" in str(
            choices.values()
        ) or "001-auth-system" in str(choices.values())
        assert "Modern branch format" in str(
            choices.values()
        ) or "feature/auth-system" in str(choices.values())

        # CRITICAL TEST: Verify choices align with BranchNamingConfig defaults
        # This should ideally include patterns from BranchNamingConfig.patterns
        # Current implementation only offers 2 choices, but data model defines more
        # This discrepancy will FAIL initially and shows room for enhancement
        from specify_cli.models.config import BranchNamingConfig

        default_config = BranchNamingConfig()

        # Check that at least some patterns from the data model are represented
        data_model_has_feature_pattern = any(
            "feature/" in pattern for pattern in default_config.patterns
        )
        assert data_model_has_feature_pattern, (
            "Data model should include feature/ patterns"
        )

        # This assertion may fail initially if UI choices don't match data model fully
        # showing the need to integrate BranchNamingConfig patterns with UI choices

    def test_ai_specific_next_steps_display(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test that AI-specific next steps are displayed correctly.

        Covers the final step display logic for different AI assistants.
        Expected to FAIL initially - enhanced next steps not implemented
        """
        # Test Claude-specific next steps
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui
            mock_ui.select.side_effect = ["claude", "001-feature-name"]

            result = cli_runner.invoke(
                app, ["init", "claude-steps"], catch_exceptions=False
            )

        assert result.exit_code == 0
        assert "Claude Code" in result.stdout
        assert "/ commands" in result.stdout

        # Test Gemini-specific next steps
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui
            mock_ui.select.side_effect = ["gemini", "feature/{name}"]

            result = cli_runner.invoke(
                app, ["init", "gemini-steps"], catch_exceptions=False
            )

        assert result.exit_code == 0
        assert "Gemini CLI" in result.stdout

        # Test Copilot-specific next steps
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui
            mock_ui.select.side_effect = ["copilot", "001-feature-name"]

            result = cli_runner.invoke(
                app, ["init", "copilot-steps"], catch_exceptions=False
            )

        assert result.exit_code == 0
        assert "GitHub Copilot" in result.stdout or "Copilot" in result.stdout

    @pytest.mark.parametrize(
        "ai_assistant,branch_pattern",
        [
            ("claude", "001-feature-name"),
            ("claude", "feature/{name}"),
            ("gemini", "001-feature-name"),
            ("gemini", "feature/{name}"),
            ("copilot", "001-feature-name"),
            ("copilot", "feature/{name}"),
        ],
    )
    def test_all_ai_assistant_and_branch_pattern_combinations(
        self,
        cli_runner,
        temp_project_dir,
        mock_project_manager,
        ai_assistant,
        branch_pattern,
    ):
        """
        Test all valid combinations of AI assistants and branch patterns.

        This parametrized test ensures all combinations work correctly.
        Expected to FAIL initially - not all combinations fully implemented
        """
        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui
            mock_ui.select.side_effect = [ai_assistant, branch_pattern]

            result = cli_runner.invoke(
                app,
                [
                    "init",
                    f"combo-{ai_assistant}-{branch_pattern.replace('/', '-').replace('{', '').replace('}', '')}",
                ],
                catch_exceptions=False,
            )

        assert result.exit_code == 0

        # Verify correct options passed to project manager
        init_call = mock_project_manager.initialize_project.call_args[0][0]
        assert init_call.ai_assistant == ai_assistant

    def test_branch_pattern_influences_generated_scripts(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test that selected branch pattern influences generated Python scripts.

        Based on quickstart Scenario 3: Scripts should use selected pattern.
        Expected to FAIL initially - script generation with pattern integration incomplete
        """
        project_dir = temp_project_dir / "script-pattern-test"

        # Mock script generation that includes branch pattern logic
        def mock_init_with_scripts(options):
            project_dir.mkdir(parents=True, exist_ok=True)
            scripts_dir = project_dir / ".specify" / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)

            # Generate create-feature.py script with pattern logic (mock)
            script_content = f'''#!/usr/bin/env python3
"""Auto-generated script for creating features with SpecifyX"""

# Selected branch pattern: {getattr(options, "branch_pattern", "MISSING")}
BRANCH_PATTERN = "{getattr(options, "branch_pattern", "MISSING")}"

def create_feature(feature_name):
    """Create feature with selected branch pattern"""
    if BRANCH_PATTERN == "001-feature-name":
        branch_name = f"001-{{feature_name.replace(' ', '-').lower()}}"
    elif BRANCH_PATTERN == "feature/{{name}}":
        branch_name = f"feature/{{feature_name.replace(' ', '-').lower()}}"
    else:
        branch_name = f"unknown-pattern-{{feature_name}}"
    
    return branch_name

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(create_feature(sys.argv[1]))
'''

            script_file = scripts_dir / "create-feature.py"
            script_file.write_text(script_content)
            script_file.chmod(0o755)  # Make executable

            result = MagicMock()
            result.success = True
            result.project_path = project_dir
            result.completed_steps = ["validation", "creation", "scripts"]
            return result

        mock_project_manager.initialize_project.side_effect = mock_init_with_scripts

        with patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class:
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui

            # Select modern pattern
            mock_ui.select.side_effect = ["claude", "feature/{name}"]

            result = cli_runner.invoke(
                app, ["init", "script-pattern-test"], catch_exceptions=False
            )

        assert result.exit_code == 0

        # CRITICAL TEST: Verify generated script contains the selected pattern
        script_file = project_dir / ".specify" / "scripts" / "create-feature.py"
        assert script_file.exists(), "Feature creation script should be generated"

        script_content = script_file.read_text()
        # This will FAIL initially if branch pattern isn't passed to script generation
        assert 'BRANCH_PATTERN = "feature/{name}"' in script_content, (
            "Generated script should use selected branch pattern"
        )

        # Verify script logic works with the pattern
        assert "feature/{" in script_content, (
            "Script should contain feature branch logic"
        )

    def test_step_tracker_integration_with_interactive_prompts(
        self, cli_runner, temp_project_dir, mock_project_manager
    ):
        """
        Test that StepTracker properly integrates with interactive prompts.

        This ensures the progress display works correctly during selection.
        Expected to FAIL initially - step tracker integration incomplete
        """
        with (
            patch("specify_cli.commands.init.init.InteractiveUI") as mock_ui_class,
            patch("specify_cli.commands.init.init.StepTracker") as mock_tracker_class,
        ):
            mock_ui = MagicMock()
            mock_ui_class.return_value = mock_ui
            mock_ui.select.side_effect = ["claude", "001-feature-name"]

            mock_tracker = MagicMock()
            mock_tracker.__enter__ = MagicMock(return_value=mock_tracker)
            mock_tracker.__exit__ = MagicMock(return_value=None)
            mock_tracker_class.create_default.return_value = mock_tracker

            result = cli_runner.invoke(
                app, ["init", "tracker-test"], catch_exceptions=False
            )

        assert result.exit_code == 0

        # Verify step tracker was used properly
        mock_tracker.add_step.assert_called()
        mock_tracker.start_step.assert_called()
        mock_tracker.complete_step.assert_called()


# TDD IMPLEMENTATION ROADMAP
"""
To make these tests pass, the following features need to be implemented:

PRIORITY 1 - Core Integration (Tests Currently Failing):
1. Add `branch_pattern` field to ProjectInitOptions data model
2. Wire branch_pattern from init command UI selection to ProjectInitOptions
3. Pass branch_pattern through ProjectManager to template rendering and config generation

PRIORITY 2 - Configuration Integration:
4. Update config generation to set selected pattern as default_pattern
5. Ensure TOML generation includes proper branch naming configuration
6. Validate pattern selection integrates with BranchNamingConfig data model

PRIORITY 3 - Script Generation Enhancement:
7. Pass branch_pattern to script generation templates
8. Update script templates to use selected pattern for branch creation logic  
9. Ensure generated scripts import SpecifyX utilities correctly

PRIORITY 4 - UI Enhancement:
10. Integrate BranchNamingConfig.patterns with interactive UI choices
11. Expand pattern options beyond current hardcoded two choices
12. Add pattern descriptions and examples for better UX

PRIORITY 5 - Error Handling:
13. Improve validation for custom branch patterns
14. Enhanced cancellation handling during multi-step prompts
15. Better error messages for invalid pattern selections

These tests provide comprehensive coverage of the interactive init workflow
and will guide TDD implementation of the enhanced branch pattern functionality.
"""

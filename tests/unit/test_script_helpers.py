"""
Unit tests for script_helpers module.

Tests the ScriptHelpers class and utility functions used by generated Python scripts.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from specify_cli.utils.script_helpers import (
    ScriptHelpers,
    echo_debug,
    echo_error,
    echo_info,
    echo_success,
    get_script_helpers,
    render_template_standalone,
)


class TestScriptHelpers:
    """Test the ScriptHelpers class functionality."""

    @pytest.fixture
    def script_helpers(self):
        """Create ScriptHelpers instance for testing."""
        return ScriptHelpers()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_git_repo(self, temp_dir):
        """Create a mock git repository structure."""
        # Create .git directory
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        # Create .specify directory
        specify_dir = temp_dir / ".specify"
        specify_dir.mkdir()

        # Create specs directory
        specs_dir = temp_dir / "specs"
        specs_dir.mkdir()

        return temp_dir

    def test_get_repo_root_from_scripts_dir(self, script_helpers, mock_git_repo):
        """Test getting repo root when running from .specify/scripts/ directory."""
        scripts_dir = mock_git_repo / ".specify" / "scripts"
        scripts_dir.mkdir(parents=True)

        with (
            patch("pathlib.Path.cwd", return_value=scripts_dir),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = str(mock_git_repo) + "\n"
            mock_run.return_value.returncode = 0

            result = script_helpers.get_repo_root()
            assert result == mock_git_repo

    def test_get_repo_root_from_project_root(self, script_helpers, mock_git_repo):
        """Test getting repo root when running from project root."""
        with (
            patch("pathlib.Path.cwd", return_value=mock_git_repo),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = str(mock_git_repo) + "\n"
            mock_run.returnvalue = 0

            result = script_helpers.get_repo_root()
            assert result == mock_git_repo

    def test_get_repo_root_fallback(self, script_helpers):
        """Test fallback when not in git repository."""
        with (
            patch("pathlib.Path.cwd", return_value=Path("/tmp/not-git")),
            patch(
                "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
            ),
        ):
            result = script_helpers.get_repo_root()
            assert result == Path("/tmp/not-git")

    def test_get_current_branch_success(self, script_helpers, mock_git_repo):
        """Test getting current branch successfully."""
        with (
            patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo),
            patch.object(
                script_helpers._git_service,
                "get_current_branch",
                return_value="feature/test",
            ),
        ):
            result = script_helpers.get_current_branch()
            assert result == "feature/test"

    def test_get_current_branch_fallback(self, script_helpers, mock_git_repo):
        """Test fallback to direct git command."""
        with (
            patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo),
            patch.object(
                script_helpers._git_service,
                "get_current_branch",
                side_effect=Exception(),
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = "feature/test\n"
            mock_run.return_value.returncode = 0

            result = script_helpers.get_current_branch()
            assert result == "feature/test"

    def test_get_current_branch_none_values(self, script_helpers, mock_git_repo):
        """Test handling of None-like string values."""
        with (
            patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo),
            patch.object(
                script_helpers._git_service, "get_current_branch", return_value="None"
            ),
        ):
            result = script_helpers.get_current_branch()
            assert result is None

    def test_load_project_config_success(self, script_helpers):
        """Test loading project config successfully."""
        mock_config = {
            "name": "test-project",
            "template_settings": {"ai_assistant": "claude"},
        }

        with patch.object(
            script_helpers._config_service,
            "load_project_config",
            return_value=mock_config,
        ):
            result = script_helpers.load_project_config()
            assert result == mock_config

    def test_load_project_config_with_object(self, script_helpers):
        """Test loading project config with ProjectConfig object."""
        mock_config_obj = Mock()
        mock_config_obj.to_dict.return_value = {"name": "test-project"}

        with patch.object(
            script_helpers._config_service,
            "load_project_config",
            return_value=mock_config_obj,
        ):
            result = script_helpers.load_project_config()
            assert result == {"name": "test-project"}

    def test_load_project_config_failure(self, script_helpers):
        """Test handling config loading failure."""
        with patch.object(
            script_helpers._config_service,
            "load_project_config",
            side_effect=Exception(),
        ):
            result = script_helpers.load_project_config()
            assert result is None

    def test_apply_branch_pattern_jinja2_style(self, script_helpers):
        """Test applying branch pattern with Jinja2-style variables."""
        pattern = "feature/{{ feature_name }}"
        result = script_helpers.apply_branch_pattern(
            pattern, feature_name="auth-system"
        )
        assert result == "feature/auth-system"

    def test_apply_branch_pattern_simple_style(self, script_helpers):
        """Test applying branch pattern with simple-style variables."""
        pattern = "feature/{feature_name}"
        result = script_helpers.apply_branch_pattern(
            pattern, feature_name="auth-system"
        )
        assert result == "feature/auth-system"

    def test_create_branch_name(self, script_helpers):
        """Test creating clean branch name from description."""
        result = script_helpers.create_branch_name("User Authentication System", "001")
        assert result == "001-user-authentication-system"

    def test_create_branch_name_short_description(self, script_helpers):
        """Test creating branch name from short description."""
        result = script_helpers.create_branch_name("Auth", "001")
        assert result == "001-auth"

    def test_validate_branch_name_against_patterns_success(self, script_helpers):
        """Test successful branch name validation."""
        with patch.object(
            script_helpers._config_service,
            "validate_branch_name_matches_pattern",
            return_value=(True, None),
        ):
            is_valid, error, pattern = (
                script_helpers.validate_branch_name_against_patterns(
                    "feature/test", ["feature/*"]
                )
            )
            assert is_valid is True
            assert error is None
            assert pattern == "feature/*"

    def test_validate_branch_name_against_patterns_failure(self, script_helpers):
        """Test failed branch name validation."""
        with patch.object(
            script_helpers._config_service,
            "validate_branch_name_matches_pattern",
            return_value=(False, "Invalid pattern"),
        ):
            is_valid, error, pattern = (
                script_helpers.validate_branch_name_against_patterns(
                    "invalid", ["feature/*"]
                )
            )
            assert is_valid is False
            assert "Invalid pattern" in error
            assert pattern is None

    def test_validate_branch_name_empty(self, script_helpers):
        """Test validation of empty branch name."""
        is_valid, error, pattern = script_helpers.validate_branch_name_against_patterns(
            "", ["feature/*"]
        )
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_spec_id_format_valid(self, script_helpers):
        """Test validation of valid spec ID."""
        is_valid, error = script_helpers.validate_spec_id_format("001")
        assert is_valid is True
        assert error is None

    def test_validate_spec_id_format_invalid(self, script_helpers):
        """Test validation of invalid spec ID."""
        is_valid, error = script_helpers.validate_spec_id_format("1")
        assert is_valid is False
        assert "3-digit number" in error

    def test_check_spec_id_exists_found(self, script_helpers, mock_git_repo):
        """Test checking for existing spec ID."""
        specs_dir = mock_git_repo / "specs"
        spec_dir = specs_dir / "001-existing-feature"
        spec_dir.mkdir(parents=True)

        with patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo):
            exists, path = script_helpers.check_spec_id_exists("001")
            assert exists is True
            assert path == spec_dir

    def test_check_spec_id_exists_not_found(self, script_helpers, mock_git_repo):
        """Test checking for non-existing spec ID."""
        with patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo):
            exists, path = script_helpers.check_spec_id_exists("999")
            assert exists is False
            assert path is None

    def test_check_branch_exists_with_commits(self, script_helpers, mock_git_repo):
        """Test checking branch existence when repo has commits."""
        with (
            patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo),
            patch("subprocess.run") as mock_run,
        ):
            # Mock rev-list to return 0 (has commits)
            mock_run.return_value.returncode = 0
            # Mock branch --list to return the branch
            mock_run.return_value.stdout = "  feature/test\n"

            result = script_helpers.check_branch_exists("feature/test")
            assert result is True

    def test_check_branch_exists_no_commits(self, script_helpers, mock_git_repo):
        """Test checking branch existence when repo has no commits."""
        with (
            patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo),
            patch("subprocess.run") as mock_run,
        ):
            # Mock rev-list to return non-zero (no commits)
            def side_effect(*args, **_kwargs):
                if "rev-list" in args[0]:
                    mock_result = Mock()
                    mock_result.returncode = 1
                    return mock_result
                else:
                    # Mock branch --show-current
                    mock_result = Mock()
                    mock_result.stdout = "feature/test\n"
                    return mock_result

            mock_run.side_effect = side_effect

            result = script_helpers.check_branch_exists("feature/test")
            assert result is True

    def test_complete_branch_name_already_complete(self, script_helpers):
        """Test completing branch name that's already complete."""
        with patch.object(
            script_helpers,
            "validate_branch_name_against_patterns",
            return_value=(True, None, "feature/*"),
        ):
            result, success, error = script_helpers.complete_branch_name(
                "feature/001-auth", ["feature/*"]
            )
            assert result == "feature/001-auth"
            assert success is True
            assert error is None

    def test_complete_branch_name_with_xxx(self, script_helpers):
        """Test completing branch name with xxx placeholder."""
        with (
            patch.object(script_helpers, "get_next_feature_number", return_value="001"),
            patch.object(
                script_helpers,
                "validate_branch_name_against_patterns",
                return_value=(True, None, "feature/{spec-id}-{feature-name}"),
            ),
        ):
            result, success, error = script_helpers.complete_branch_name(
                "feature/xxx-auth", ["feature/{spec-id}-{feature-name}"]
            )
            # The method should replace xxx with the spec ID
            assert result == "feature/001-auth"
            assert success is True
            assert error is None

    def test_get_next_feature_number(self, script_helpers, mock_git_repo):
        """Test getting next feature number."""
        specs_dir = mock_git_repo / "specs"
        # Create existing spec directories
        (specs_dir / "001-first").mkdir()
        (specs_dir / "003-third").mkdir()

        with patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo):
            result = script_helpers.get_next_feature_number()
            assert result == "004"

    def test_branch_to_directory_name_simple(self, script_helpers):
        """Test converting simple branch name to directory name."""
        with patch.object(
            script_helpers, "get_next_feature_number", return_value="001"
        ):
            result = script_helpers.branch_to_directory_name("auth-system")
            assert result == "001-auth-system"

    def test_branch_to_directory_name_with_slash(self, script_helpers):
        """Test converting branch name with slash to directory name."""
        with patch.object(
            script_helpers, "get_next_feature_number", return_value="001"
        ):
            result = script_helpers.branch_to_directory_name("feature/auth-system")
            assert result == "001-feature-auth-system"

    def test_branch_to_directory_name_already_numbered(self, script_helpers):
        """Test converting already numbered branch name."""
        # Even if next number would be 003, should preserve user's 001
        with patch.object(
            script_helpers, "get_next_feature_number", return_value="003"
        ):
            result = script_helpers.branch_to_directory_name("001-auth-system")
            assert result == "001-auth-system"  # Uses user's number, not 003

    def test_branch_to_directory_name_already_numbered_with_slash(self, script_helpers):
        """Test converting already numbered branch name with slash."""
        # Even if next number would be 003, should preserve user's 001 and convert slash
        with patch.object(
            script_helpers, "get_next_feature_number", return_value="003"
        ):
            result = script_helpers.branch_to_directory_name("001/auth-system")
            assert result == "001-auth-system"  # Uses user's number, not 003

    def test_find_feature_directory_found(self, script_helpers, mock_git_repo):
        """Test finding existing feature directory."""
        specs_dir = mock_git_repo / "specs"
        feature_dir = specs_dir / "001-auth-system"
        feature_dir.mkdir(parents=True)

        with (
            patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo),
            patch.object(
                script_helpers, "get_current_branch", return_value="feature/auth-system"
            ),
        ):
            result = script_helpers.find_feature_directory()
            assert result == feature_dir

    def test_find_feature_directory_not_found(self, script_helpers, mock_git_repo):
        """Test finding non-existing feature directory."""
        with (
            patch.object(script_helpers, "get_repo_root", return_value=mock_git_repo),
            patch.object(
                script_helpers, "get_current_branch", return_value="feature/nonexistent"
            ),
        ):
            result = script_helpers.find_feature_directory()
            assert result is None

    def test_get_branch_naming_config_from_project(self, script_helpers):
        """Test getting branch naming config from project config."""
        project_config = {
            "project": {
                "branch_naming": {
                    "patterns": ["feature/*"],
                    "validation_rules": ["max_length_50"],
                }
            }
        }

        with patch.object(
            script_helpers, "load_project_config", return_value=project_config
        ):
            result = script_helpers.get_branch_naming_config()
            assert result["patterns"] == ["feature/*"]

    def test_get_branch_naming_config_fallback(self, script_helpers):
        """Test fallback branch naming config."""
        with (
            patch.object(script_helpers, "load_project_config", return_value=None),
            patch("specify_cli.models.config.BranchNamingConfig") as mock_config,
        ):
            mock_config.return_value.to_dict.return_value = {"patterns": ["default"]}
            result = script_helpers.get_branch_naming_config()
            # The actual fallback returns default patterns, not our mock
            assert "patterns" in result
            assert len(result["patterns"]) > 0

    def test_validate_feature_description_valid(self, script_helpers):
        """Test validation of valid feature description."""
        is_valid, error = script_helpers.validate_feature_description(
            "User authentication system"
        )
        assert is_valid is True
        assert error is None

    def test_validate_feature_description_empty(self, script_helpers):
        """Test validation of empty feature description."""
        is_valid, error = script_helpers.validate_feature_description("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_feature_description_too_short(self, script_helpers):
        """Test validation of too short feature description."""
        is_valid, error = script_helpers.validate_feature_description("ab")
        assert is_valid is False
        assert "at least 3 characters" in error

    def test_validate_feature_description_no_letters(self, script_helpers):
        """Test validation of description with no letters."""
        is_valid, error = script_helpers.validate_feature_description("123")
        assert is_valid is False
        assert "must contain at least one letter" in error

    def test_check_git_repository_true(self, script_helpers):
        """Test checking git repository when in git repo."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = script_helpers.check_git_repository()
            assert result is True

    def test_check_git_repository_false(self, script_helpers):
        """Test checking git repository when not in git repo."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            result = script_helpers.check_git_repository()
            assert result is False

    def test_is_feature_branch_true(self, script_helpers):
        """Test checking if branch is feature branch."""
        with patch.object(
            script_helpers, "get_current_branch", return_value="feature/test"
        ):
            result = script_helpers.is_feature_branch()
            assert result is True

    def test_is_feature_branch_false(self, script_helpers):
        """Test checking if branch is not feature branch."""
        with patch.object(script_helpers, "get_current_branch", return_value="main"):
            result = script_helpers.is_feature_branch()
            assert result is False

    def test_get_current_date(self, script_helpers):
        """Test getting current date."""
        result = script_helpers.get_current_date()
        assert len(result) == 10  # YYYY-MM-DD format
        assert result.count("-") == 2

    def test_get_project_name_from_config(self, script_helpers):
        """Test getting project name from config."""
        with patch.object(
            script_helpers, "load_project_config", return_value={"name": "test-project"}
        ):
            result = script_helpers.get_project_name()
            assert result == "test-project"

    def test_get_project_name_fallback(self, script_helpers):
        """Test fallback to directory name for project name."""
        with (
            patch.object(script_helpers, "load_project_config", return_value=None),
            patch.object(
                script_helpers,
                "get_repo_root",
                return_value=Path("/path/to/test-project"),
            ),
        ):
            result = script_helpers.get_project_name()
            assert result == "test-project"

    def test_get_author_name_from_config(self, script_helpers):
        """Test getting author name from config."""
        config = {"template_settings": {"author_name": "John Doe"}}
        with patch.object(script_helpers, "load_project_config", return_value=config):
            result = script_helpers.get_author_name()
            assert result == "John Doe"

    def test_get_author_name_from_git(self, script_helpers):
        """Test getting author name from git config."""
        with (
            patch.object(script_helpers, "load_project_config", return_value=None),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = "John Doe\n"
            mock_run.return_value.returncode = 0

            result = script_helpers.get_author_name()
            assert result == "John Doe"

    def test_get_author_name_fallback(self, script_helpers):
        """Test fallback author name."""
        with (
            patch.object(script_helpers, "load_project_config", return_value=None),
            patch(
                "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
            ),
        ):
            result = script_helpers.get_author_name()
            assert result == "Unknown"

    def test_render_template_standalone_j2_template(self, script_helpers, temp_dir):
        """Test rendering .j2 template standalone."""
        template_path = temp_dir / "test.j2"
        template_path.write_text("Hello {{ project_name }}!")

        output_path = temp_dir / "output.txt"
        context = {"project_name": "TestProject"}

        success, error = script_helpers.render_template_standalone(
            template_path, context, output_path
        )

        assert success is True
        assert error is None
        assert output_path.read_text() == "Hello TestProject!"

    def test_render_template_standalone_regular_file(self, script_helpers, temp_dir):
        """Test copying regular file."""
        template_path = temp_dir / "test.txt"
        template_path.write_text("Hello World!")

        output_path = temp_dir / "output.txt"
        context = {}

        success, error = script_helpers.render_template_standalone(
            template_path, context, output_path
        )

        assert success is True
        assert error is None
        assert output_path.read_text() == "Hello World!"

    def test_render_template_standalone_make_executable(self, script_helpers, temp_dir):
        """Test rendering template and making executable."""
        template_path = temp_dir / "test.j2"
        template_path.write_text("#!/usr/bin/env python3\nprint('Hello')")

        output_path = temp_dir / "output.py"
        context = {}

        success, error = script_helpers.render_template_standalone(
            template_path, context, output_path, make_executable=True
        )

        assert success is True
        assert error is None
        assert output_path.exists()
        # Check if file is executable (on Unix systems)
        # On Windows, executable permissions work differently, so we skip this check
        import os

        if os.name != "nt" and hasattr(output_path.stat(), "st_mode"):
            assert output_path.stat().st_mode & 0o111

    def test_render_template_standalone_template_not_found(
        self, script_helpers, temp_dir
    ):
        """Test rendering non-existent template."""
        template_path = temp_dir / "nonexistent.j2"
        output_path = temp_dir / "output.txt"
        context = {}

        success, error = script_helpers.render_template_standalone(
            template_path, context, output_path
        )

        assert success is False
        assert "not found" in error

    def test_output_result_json_mode(self, script_helpers, capsys):
        """Test outputting result in JSON mode."""
        result = {"status": "success", "message": "Done"}
        script_helpers.output_result(result, success=True, json_mode=True)

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == result

    def test_output_result_human_readable(self, script_helpers, capsys):
        """Test outputting result in human-readable mode."""
        result = {"status": "success", "message": "Done"}
        script_helpers.output_result(result, success=True, json_mode=False)

        captured = capsys.readouterr()
        assert "Status: success" in captured.out
        assert "Message: Done" in captured.out

    def test_output_result_error(self, script_helpers, capsys):
        """Test outputting error result."""
        result = {"error": "Something went wrong"}
        script_helpers.output_result(result, success=False, json_mode=False)

        captured = capsys.readouterr()
        assert "Error: Something went wrong" in captured.err

    def test_handle_typer_exceptions_success(self, script_helpers):
        """Test handling successful typer command."""

        def test_func():
            return "success"

        wrapped = script_helpers.handle_typer_exceptions(test_func)
        result = wrapped()
        assert result == "success"

    def test_handle_typer_exceptions_keyboard_interrupt(self, script_helpers):
        """Test handling keyboard interrupt in typer command."""

        def test_func():
            raise KeyboardInterrupt()

        wrapped = script_helpers.handle_typer_exceptions(test_func)

        with pytest.raises(Exception) as exc_info:
            wrapped()
        # The actual exception is click.exceptions.Exit, not SystemExit
        assert hasattr(exc_info.value, "exit_code") or str(exc_info.value) == "1"

    def test_handle_typer_exceptions_general_exception(self, script_helpers):
        """Test handling general exception in typer command."""

        def test_func():
            raise ValueError("Test error")

        wrapped = script_helpers.handle_typer_exceptions(test_func)

        with pytest.raises(Exception) as exc_info:
            wrapped()
        # The actual exception is click.exceptions.Exit, not SystemExit
        assert hasattr(exc_info.value, "exit_code") or str(exc_info.value) == "1"


class TestUtilityFunctions:
    """Test utility functions in script_helpers module."""

    def test_echo_info(self, capsys):
        """Test echo_info function."""
        echo_info("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_echo_info_quiet(self, capsys):
        """Test echo_info in quiet mode."""
        echo_info("Test message", quiet=True)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_echo_debug(self, capsys):
        """Test echo_debug function."""
        echo_debug("Debug message", debug=True)
        captured = capsys.readouterr()
        assert "DEBUG: Debug message" in captured.out

    def test_echo_debug_disabled(self, capsys):
        """Test echo_debug when debug is disabled."""
        echo_debug("Debug message", debug=False)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_echo_error(self, capsys):
        """Test echo_error function."""
        echo_error("Error message")
        captured = capsys.readouterr()
        assert "Error: Error message" in captured.out

    def test_echo_success(self, capsys):
        """Test echo_success function."""
        echo_success("Success message")
        captured = capsys.readouterr()
        assert "✓ Success message" in captured.out

    def test_echo_success_quiet(self, capsys):
        """Test echo_success in quiet mode."""
        echo_success("Success message", quiet=True)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_get_script_helpers(self):
        """Test get_script_helpers function."""
        helpers = get_script_helpers()
        assert isinstance(helpers, ScriptHelpers)

    def test_render_template_standalone_function(self, tmp_path):
        """Test render_template_standalone function."""
        template_path = tmp_path / "test.j2"
        template_path.write_text("Hello {{ project_name }}!")

        output_path = tmp_path / "output.txt"
        context = {"project_name": "TestProject"}

        success, error = render_template_standalone(template_path, context, output_path)

        assert success is True
        assert error is None
        assert output_path.read_text() == "Hello TestProject!"

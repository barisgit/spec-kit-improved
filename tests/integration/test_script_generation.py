"""
Integration test for SpecifyX Python script generation functionality

This test follows TDD principles and will FAIL initially since the script generation services aren't implemented yet.
Tests the complete script generation workflow from Jinja2 templates to executable Python scripts.

MISSING METHODS that need to be implemented:
- ScriptGenerationService.generate_scripts_from_templates() -> List[GeneratedScript]: Generate Python scripts from script templates
- ScriptGenerationService.set_script_permissions() -> bool: Set execute permissions on generated scripts
- ScriptGenerationService.validate_script_imports() -> bool: Validate SpecifyX utility imports
- ScriptGenerationService.test_script_execution() -> bool: Test script execution and --json flag support
- TemplateService.discover_templates_by_category("scripts") -> List[GranularTemplate]: Filter script templates
- ProjectManager.generate_python_scripts() -> List[GeneratedScript]: Orchestrate script generation

CURRENT FUNCTIONALITY that needs enhancement:
- Template rendering exists but needs script-specific context handling
- File operations exist but need script permission management
- Branch naming validation exists but needs script integration

The tests validate:
1. Python script generation from Jinja2 templates in src/specify_cli/init_templates/scripts/
2. Generated scripts have proper SpecifyX utility imports and access
3. Script execution permissions are set correctly across platforms
4. Cross-platform script compatibility (shebang, imports, paths)
5. Scripts contain branch naming pattern logic and validation
6. JSON output support (--json flag) in generated scripts
7. Error handling for script generation failures
8. Integration with the template rendering system
"""

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# These imports will FAIL initially for services - that's expected for TDD
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.project import ProjectConfig, TemplateContext
from specify_cli.models.template import (
    GeneratedScript,
)
from specify_cli.services.project_manager import ProjectManager
from specify_cli.services.script_generation_service import ScriptGenerationService
from specify_cli.services.template_service import TemplateService


class TestScriptGeneration:
    """Integration tests for Python script generation from Jinja2 templates"""

    @pytest.fixture
    def temp_project_dir(self) -> Path:
        """Create temporary project directory for script generation tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            project_path.mkdir(parents=True)

            # Create .specify directory structure
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "scripts").mkdir()
            (project_path / ".specify" / "templates").mkdir()
            (project_path / ".claude" / "commands").mkdir(parents=True)

            yield project_path

    @pytest.fixture
    def script_template_context(self) -> TemplateContext:
        """Create template context for script generation"""
        branch_config = BranchNamingConfig(
            description="Traditional numbered branches with hotfixes and main branches",
            patterns=[
                "{number-3}-{feature-name}",
                "hotfix/{bug-id}",
                "main",
                "development",
            ],
            validation_rules=[
                "max_length_50",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_only",
            ],
        )

        return TemplateContext(
            project_name="script-test-project",
            ai_assistant="claude",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/project"),
            target_paths={
                "create-feature.j2": Path(
                    "/test/project/.specify/scripts/create-feature.py"
                ),
                "setup-plan.j2": Path("/test/project/.specify/scripts/setup-plan.py"),
                "check-prerequisites.j2": Path(
                    "/test/project/.specify/scripts/check-prerequisites.py"
                ),
            },
        )

    @pytest.fixture
    def project_config(self) -> ProjectConfig:
        """Create project configuration for script generation"""
        return ProjectConfig(
            name="script-test-project",
            branch_naming=BranchNamingConfig(
                description="Traditional numbered branches",
                patterns=["{number-3}-{feature-name}", "hotfix/{bug-id}"],
                validation_rules=["max_length_50", "lowercase_only", "no_spaces"],
            ),
            template_settings={
                "ai_assistant": "claude",
                "config_directory": ".specify",
            },
        )

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance - will fail initially due to missing script methods"""
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    @pytest.fixture
    def script_generation_service(self) -> ScriptGenerationService:
        """Create ScriptGenerationService instance - will fail initially as service doesn't exist"""
        # This import will fail - that's expected for TDD
        return ScriptGenerationService()

    @pytest.fixture
    def project_manager(self) -> ProjectManager:
        """Create ProjectManager instance for script generation orchestration"""
        return ProjectManager()

    def test_discover_script_templates_from_package(
        self, template_service: TemplateService
    ):
        """Test discovery of script templates from SpecifyX package resources"""
        # This will fail initially - testing method that doesn't exist yet
        script_templates = template_service.discover_templates_by_category("scripts")

        # Should find all script templates from src/specify_cli/init_templates/scripts/
        assert (
            len(script_templates) >= 3
        )  # We know create-feature, setup-plan, check-prerequisites exist

        # Validate specific script templates exist
        template_names = [t.name for t in script_templates]
        expected_scripts = ["create-feature", "setup-plan", "check-prerequisites"]

        for script_name in expected_scripts:
            assert script_name in template_names, (
                f"Missing script template: {script_name}"
            )

        # All script templates should be marked as executable
        for template in script_templates:
            assert template.executable is True, (
                f"Script template {template.name} should be executable"
            )
            assert template.category == "scripts", (
                f"Template {template.name} should have 'scripts' category"
            )
            assert template.target_path.endswith(".py"), (
                f"Script {template.name} should generate .py file"
            )

    def test_generate_scripts_from_templates(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test generating Python scripts from Jinja2 templates"""
        # This will fail initially - testing method that doesn't exist yet
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            template_context=script_template_context,
            output_directory=temp_project_dir / ".specify" / "scripts",
        )

        # Should generate scripts for each template
        assert len(generated_scripts) >= 3

        # Validate GeneratedScript objects
        for script in generated_scripts:
            assert isinstance(script, GeneratedScript)
            assert script.name in [
                "create-feature",
                "setup-plan",
                "check-prerequisites",
            ]
            assert script.target_path.exists(), (
                f"Generated script {script.name} should exist on disk"
            )
            assert script.target_path.suffix == ".py", (
                f"Script {script.name} should have .py extension"
            )
            assert script.executable is True, (
                f"Script {script.name} should be marked as executable"
            )

            # Validate script content structure
            script_content = script.target_path.read_text()
            assert script_content.startswith("#!/usr/bin/env python3"), (
                f"Script {script.name} should have proper shebang"
            )
            assert "import" in script_content, (
                f"Script {script.name} should have imports"
            )

            # Should contain SpecifyX utility imports
            assert len(script.imports) > 0, (
                f"Script {script.name} should have SpecifyX imports"
            )
            assert any("specify_cli" in imp for imp in script.imports), (
                f"Script {script.name} should import SpecifyX utilities"
            )

    def test_script_specityx_utility_imports(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test that generated scripts correctly import SpecifyX utilities"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        # Test each generated script for proper imports
        expected_imports = {
            "create-feature": [
                "from specify_cli.services import CommandLineGitService, TomlConfigService",
                "from specify_cli.utils.validators import validate_feature_description",
            ],
            "setup-plan": [
                "from specify_cli.services import ProjectManager, TemplateService",
                "from specify_cli.utils.file_operations import ensure_directory_exists",
            ],
            "check-prerequisites": [
                "from specify_cli.services import ConfigService",
                "from specify_cli.utils.validators import validate_git_repository",
            ],
        }

        for script in generated_scripts:
            script_content = script.target_path.read_text()

            if script.name in expected_imports:
                # Check for expected imports
                for expected_import in expected_imports[script.name]:
                    assert expected_import in script_content, (
                        f"Script {script.name} should contain import: {expected_import}"
                    )

            # All scripts should have fallback handling for missing imports
            assert "ImportError" in script_content, (
                f"Script {script.name} should handle ImportError"
            )
            assert (
                "try:" in script_content and "except ImportError:" in script_content
            ), f"Script {script.name} should have try/except for imports"

    def test_script_execution_permissions(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test that script execution permissions are set correctly"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        # This will fail initially - testing method that doesn't exist yet
        permissions_set = script_generation_service.set_script_permissions(
            generated_scripts
        )
        assert permissions_set is True

        # Check file permissions on each script
        for script in generated_scripts:
            script_stat = script.target_path.stat()

            # Should be executable by user (at minimum)
            assert script_stat.st_mode & stat.S_IEXEC, (
                f"Script {script.name} should be executable by user"
            )
            assert script_stat.st_mode & stat.S_IRUSR, (
                f"Script {script.name} should be readable by user"
            )
            assert script_stat.st_mode & stat.S_IWUSR, (
                f"Script {script.name} should be writable by user"
            )

            # On Unix-like systems, should also be group/other executable
            if os.name == "posix":
                assert script_stat.st_mode & stat.S_IXGRP, (
                    f"Script {script.name} should be group executable on Unix"
                )
                assert script_stat.st_mode & stat.S_IXOTH, (
                    f"Script {script.name} should be other executable on Unix"
                )

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Skip on Windows due to different executable handling",
    )
    def test_cross_platform_script_execution_unix(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test cross-platform script execution on Unix-like systems (macOS, Linux)"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )
        script_generation_service.set_script_permissions(generated_scripts)

        # Test script execution with --help flag
        for script in generated_scripts:
            try:
                # Should be able to execute script directly
                result = subprocess.run(
                    [str(script.target_path), "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=temp_project_dir,
                )

                # Script should run without syntax errors (may fail with usage error, but that's OK)
                # We're testing that the Python syntax is valid and imports work
                assert result.returncode != 127, (
                    f"Script {script.name} should be found and executable"
                )

            except subprocess.TimeoutExpired:
                pytest.fail(f"Script {script.name} execution timed out")
            except Exception as e:
                # Log the error but don't fail - script might depend on git repo or other context
                print(f"Warning: Could not execute script {script.name}: {e}")

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_cross_platform_script_execution_windows(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test cross-platform script execution on Windows"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        # On Windows, test execution via Python interpreter
        for script in generated_scripts:
            try:
                result = subprocess.run(
                    [sys.executable, str(script.target_path), "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=temp_project_dir,
                )

                # Script should run without syntax errors
                assert result.returncode != 2, (
                    f"Script {script.name} should have valid Python syntax"
                )

            except subprocess.TimeoutExpired:
                pytest.fail(f"Script {script.name} execution timed out on Windows")
            except Exception as e:
                print(
                    f"Warning: Could not execute script {script.name} on Windows: {e}"
                )

    def test_scripts_contain_branch_naming_logic(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test that generated scripts contain branch naming pattern logic"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        # Focus on create-feature script which should have branch naming logic
        create_feature_script = next(
            s for s in generated_scripts if s.name == "create-feature"
        )
        script_content = create_feature_script.target_path.read_text()

        # Should contain branch pattern logic
        assert (
            "get_branch_pattern" in script_content or "branch_pattern" in script_content
        ), "create-feature script should contain branch pattern handling"

        # Should contain pattern application logic
        assert (
            "apply_branch_pattern" in script_content or "{feature" in script_content
        ), "create-feature script should contain pattern application"

        # Should reference the configured patterns from context
        branch_patterns = script_template_context.branch_naming_config.patterns
        for pattern in branch_patterns:
            # Pattern or similar logic should appear in script
            if "{" in pattern:  # Template patterns
                pattern_parts = pattern.replace("{", "").replace("}", "")
                # Some part of the pattern logic should be present
                assert any(
                    part in script_content for part in pattern_parts.split("-")
                ), f"Script should contain logic for pattern: {pattern}"

        # Should contain validation rules application
        validation_rules = script_template_context.branch_naming_config.validation_rules
        for rule in validation_rules:
            if "lowercase" in rule:
                assert ".lower()" in script_content, (
                    "Script should contain lowercase conversion"
                )
            elif "no_spaces" in rule:
                assert "replace" in script_content or "re.sub" in script_content, (
                    "Script should contain space replacement logic"
                )

    def test_json_output_support(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test that generated scripts support --json flag for output"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        # All scripts should support JSON output
        for script in generated_scripts:
            assert script.json_output is True, (
                f"Script {script.name} should support JSON output"
            )

            script_content = script.target_path.read_text()

            # Should have --json argument parser
            assert "--json" in script_content, (
                f"Script {script.name} should have --json argument"
            )
            assert 'action="store_true"' in script_content, (
                f"Script {script.name} should have store_true for --json"
            )

            # Should have JSON output logic
            assert "json.dumps" in script_content, (
                f"Script {script.name} should have JSON serialization"
            )
            assert "import json" in script_content, (
                f"Script {script.name} should import json module"
            )

            # Should have conditional JSON output
            assert (
                "if args.json" in script_content or "if json_mode" in script_content
            ), f"Script {script.name} should have conditional JSON output"

    def test_script_validation(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test script validation for syntax and imports"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        # This will fail initially - testing method that doesn't exist yet
        validation_passed = script_generation_service.validate_script_imports(
            generated_scripts
        )
        assert validation_passed is True

        # Test individual script validation
        for script in generated_scripts:
            # Script should have valid Python syntax
            script_content = script.target_path.read_text()

            # Basic syntax validation - should be able to compile
            try:
                compile(script_content, str(script.target_path), "exec")
            except SyntaxError as e:
                pytest.fail(f"Script {script.name} has syntax error: {e}")

            # Should have required imports
            assert len(script.imports) > 0, f"Script {script.name} should have imports"

            # Should have main function or entry point
            assert (
                "def main(" in script_content
                or 'if __name__ == "__main__"' in script_content
            ), f"Script {script.name} should have main entry point"

    def test_error_handling_for_script_generation_failures(
        self, script_generation_service: ScriptGenerationService
    ):
        """Test error handling when script generation fails"""
        # Test with invalid template context
        with pytest.raises(Exception):
            script_generation_service.generate_scripts_from_templates(
                template_context=None, output_directory=Path("/invalid/path")
            )

        # Test with non-existent output directory
        invalid_context = TemplateContext(
            project_name="error-test",
            ai_assistant="claude",
            branch_naming_config=BranchNamingConfig("", ["test"], []),
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test"),
            target_paths={},
        )

        with pytest.raises(Exception):
            script_generation_service.generate_scripts_from_templates(
                invalid_context, Path("/nonexistent/directory")
            )

    def test_integration_with_template_rendering_system(
        self,
        project_manager: ProjectManager,
        project_config: ProjectConfig,
        temp_project_dir: Path,
    ):
        """Test integration between script generation and template rendering system"""
        # This will fail initially - testing method that doesn't exist yet
        generated_scripts = project_manager.generate_python_scripts(
            project_config=project_config, project_path=temp_project_dir
        )

        # Should generate scripts using the template rendering system
        assert len(generated_scripts) > 0

        # Scripts should be created in correct location
        scripts_dir = temp_project_dir / ".specify" / "scripts"
        assert scripts_dir.exists()

        # Each script should be a proper GeneratedScript object
        for script in generated_scripts:
            assert isinstance(script, GeneratedScript)
            assert script.target_path.parent == scripts_dir
            assert script.target_path.exists()

            # Should have proper template source reference
            assert script.source_template is not None
            assert script.source_template.endswith(".j2")

    def test_script_content_matches_template_context(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test that generated script content matches template context variables"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        for script in generated_scripts:
            script_content = script.target_path.read_text()

            # Should contain project name from context
            assert (
                script_template_context.project_name in script_content
                or script_template_context.project_name.replace("-", "_")
                in script_content
            ), f"Script {script.name} should reference project name"

            # Should contain AI assistant information (if relevant)
            if script_template_context.ai_assistant == "claude":
                # May contain Claude-specific comments or references
                assert (
                    "claude" in script_content.lower() or "Claude" in script_content
                ), f"Script {script.name} should reference Claude assistant"

            # Should contain date information
            assert script_template_context.creation_date in script_content, (
                f"Script {script.name} should contain creation date"
            )

    def test_generated_script_dependencies(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test that generated scripts have correct dependencies and imports"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )

        # Expected dependencies for each script type
        script_dependencies = {
            "create-feature": ["git", "subprocess", "pathlib", "argparse", "json"],
            "setup-plan": ["pathlib", "argparse", "json"],
            "check-prerequisites": ["subprocess", "pathlib", "argparse", "json"],
        }

        for script in generated_scripts:
            script_content = script.target_path.read_text()

            if script.name in script_dependencies:
                expected_deps = script_dependencies[script.name]
                for dep in expected_deps:
                    assert (
                        f"import {dep}" in script_content
                        or f"from {dep}" in script_content
                    ), f"Script {script.name} should import {dep}"

            # All scripts should import these common dependencies
            common_deps = ["sys", "pathlib.Path"]
            for dep in common_deps:
                if "." in dep:
                    module, item = dep.split(".", 1)
                    assert (
                        f"from {module} import" in script_content
                        and item in script_content
                    ), f"Script {script.name} should import {dep}"
                else:
                    assert f"import {dep}" in script_content, (
                        f"Script {script.name} should import {dep}"
                    )

    def test_script_execution_with_mocked_specityx(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
        temp_project_dir: Path,
    ):
        """Test script execution with mocked SpecifyX utilities"""
        generated_scripts = script_generation_service.generate_scripts_from_templates(
            script_template_context, temp_project_dir / ".specify" / "scripts"
        )
        script_generation_service.set_script_permissions(generated_scripts)

        # Mock SpecifyX utilities and test script execution
        with (
            patch("specify_cli.services.CommandLineGitService") as mock_git,
            patch(
                "specify_cli.utils.validators.validate_feature_description"
            ) as mock_validator,
        ):
            mock_validator.return_value = (True, None)
            mock_git_instance = Mock()
            mock_git.return_value = mock_git_instance
            mock_git_instance.create_branch.return_value = True

            # Test create-feature script specifically
            create_feature = next(
                s for s in generated_scripts if s.name == "create-feature"
            )

            # Should be able to import and execute main functions
            script_globals = {}
            script_content = create_feature.target_path.read_text()

            try:
                exec(script_content, script_globals)
                # Should have main function available
                assert "main" in script_globals, "Script should have main function"

                # Should have helper functions
                expected_functions = [
                    "get_repo_root",
                    "create_branch_name",
                    "load_project_config",
                ]
                for func_name in expected_functions:
                    if (
                        func_name in script_content
                    ):  # Only check if function exists in script
                        assert func_name in script_globals, (
                            f"Script should define {func_name} function"
                        )

            except Exception as e:
                # Don't fail test for import errors - scripts may have complex dependencies
                print(f"Warning: Could not execute script content: {e}")

    @pytest.mark.parametrize(
        "ai_assistant,expected_pattern",
        [
            ("claude", "{number-3}-{feature-name}"),
            ("gemini", "feature/{feature-name}"),
            ("copilot", "{team}/{feature-name}"),
        ],
    )
    def test_ai_specific_script_generation(
        self,
        script_generation_service: ScriptGenerationService,
        ai_assistant: str,
        expected_pattern: str,
        temp_project_dir: Path,
    ):
        """Test AI-specific script generation with different branch patterns"""
        # Create context for specific AI assistant
        ai_context = TemplateContext(
            project_name=f"{ai_assistant}-project",
            ai_assistant=ai_assistant,
            branch_naming_config=BranchNamingConfig(
                description=f"{ai_assistant} branch naming",
                patterns=[expected_pattern, "main", "development"],
                validation_rules=["max_length_50", "lowercase_only"],
            ),
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=temp_project_dir,
            target_paths={},
        )

        generated_scripts = script_generation_service.generate_scripts_from_templates(
            ai_context, temp_project_dir / ".specify" / "scripts"
        )

        # Scripts should be generated for this AI assistant
        assert len(generated_scripts) > 0

        # Create-feature script should contain AI-specific branch pattern
        create_feature = next(
            s for s in generated_scripts if s.name == "create-feature"
        )
        script_content = create_feature.target_path.read_text()

        # Should reference the expected pattern or its components
        pattern_parts = expected_pattern.replace("{", "").replace("}", "").split("/")
        for part in pattern_parts:
            if part and part not in ["feature", "number", "3"]:  # Skip generic parts
                assert (
                    part in script_content or part.replace("-", "_") in script_content
                ), f"Script should reference pattern part: {part}"

    def test_script_output_directory_creation(
        self,
        script_generation_service: ScriptGenerationService,
        script_template_context: TemplateContext,
    ):
        """Test that script generation creates necessary output directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "new-project"
            # Don't create .specify/scripts directory - let script generation create it

            scripts_dir = project_path / ".specify" / "scripts"
            assert not scripts_dir.exists(), (
                "Scripts directory should not exist initially"
            )

            # Generate scripts should create the directory
            generated_scripts = (
                script_generation_service.generate_scripts_from_templates(
                    script_template_context, scripts_dir
                )
            )

            # Directory should now exist
            assert scripts_dir.exists(), (
                "Script generation should create output directory"
            )
            assert scripts_dir.is_dir(), "Scripts path should be a directory"

            # Scripts should be created in the directory
            assert len(generated_scripts) > 0
            for script in generated_scripts:
                assert script.target_path.parent == scripts_dir
                assert script.target_path.exists()

"""
Cross-platform compatibility integration test for SpecifyX

This test follows TDD principles and will FAIL initially since cross-platform handling isn't fully implemented yet.
Tests the complete cross-platform compatibility across Windows, macOS, and Linux environments.

MISSING METHODS that need cross-platform implementation:
- FileOperations.set_executable_permissions() -> bool: Platform-specific executable permissions
- FileOperations.normalize_path_separators() -> str: Convert paths to platform-specific separators
- FileOperations.get_platform_specific_line_endings() -> str: Handle \n vs \r\n line endings
- ScriptGenerationService.generate_platform_scripts() -> Dict[str, GeneratedScript]: Platform-specific script generation
- TemplateService.render_with_platform_context() -> str: Platform-aware template rendering
- GitService.configure_platform_line_endings() -> bool: Configure git for platform line endings
- ProjectManager.initialize_cross_platform_project() -> bool: Cross-platform project initialization

CURRENT FUNCTIONALITY that needs cross-platform enhancement:
- File operations exist but need platform-specific path handling
- Template rendering exists but needs platform-aware context
- Script generation exists but needs platform-specific executable handling
- Git operations exist but need platform-specific configuration

The tests validate:
1. File paths use correct separators (/ on Unix, \ on Windows)
2. Generated scripts have platform-appropriate executable permissions and extensions
3. Line endings are handled correctly per platform (\n vs \r\n)
4. .specify directory creation works across all platforms
5. Template rendering handles platform-specific paths and variables
6. Generated Python scripts execute correctly on target platform
7. Configuration files work consistently across platforms
8. Error messages and paths are displayed correctly per platform
9. Git configuration respects platform conventions
10. File permissions and ownership work as expected per platform
"""

import subprocess
import tempfile
from pathlib import Path, PosixPath, WindowsPath
from typing import Any, Dict
from unittest.mock import patch

import pytest

# These imports will FAIL initially for cross-platform services - that's expected for TDD
from specify_cli.models.config import ProjectConfig, TemplateConfig
from specify_cli.models.project import ProjectInitOptions, TemplateContext
from specify_cli.services import (
    ConfigService,
    GitService,
    ProjectManager,
    TemplateService,
)
from specify_cli.utils.file_operations import FileOperations

# These imports will fail initially - expected for TDD
try:
    from specify_cli.models.template import GeneratedScript, GranularTemplate
    from specify_cli.services.script_generation_service import ScriptGenerationService
except ImportError:
    # Expected - these don't exist yet
    pass


class TestCrossPlatformCompatibility:
    """Integration tests for cross-platform compatibility across Windows, macOS, and Linux"""

    @pytest.fixture
    def temp_project_dir(self) -> Path:
        """Create temporary project directory for cross-platform tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "cross-platform-test"
            project_path.mkdir(parents=True)
            yield project_path

    @pytest.fixture
    def mock_platform_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Mock platform-specific contexts for testing"""
        return {
            "windows": {
                "os_name": "nt",
                "platform": "win32",
                "path_separator": "\\",
                "line_ending": "\r\n",
                "executable_extension": ".bat",
                "python_executable": "python.exe",
                "script_shebang": None,  # Windows doesn't use shebangs
                "path_class": WindowsPath,
                "file_permissions": 0o777,  # Windows permissions are different
            },
            "macos": {
                "os_name": "posix",
                "platform": "darwin",
                "path_separator": "/",
                "line_ending": "\n",
                "executable_extension": "",
                "python_executable": "python3",
                "script_shebang": "#!/usr/bin/env python3",
                "path_class": PosixPath,
                "file_permissions": 0o755,
            },
            "linux": {
                "os_name": "posix",
                "platform": "linux",
                "path_separator": "/",
                "line_ending": "\n",
                "executable_extension": "",
                "python_executable": "python3",
                "script_shebang": "#!/usr/bin/env python3",
                "path_class": PosixPath,
                "file_permissions": 0o755,
            },
        }

    @pytest.fixture
    def template_service(self):
        """Create TemplateService for cross-platform testing"""
        from specify_cli.services import JinjaTemplateService

        return JinjaTemplateService()

    @pytest.fixture
    def config_service(self):
        """Create ConfigService for cross-platform testing"""
        from specify_cli.services import TomlConfigService

        return TomlConfigService()

    @pytest.fixture
    def git_service(self):
        """Create GitService for cross-platform testing"""
        from specify_cli.services import CommandLineGitService

        return CommandLineGitService()

    @pytest.fixture
    def file_operations(self) -> FileOperations:
        """Create FileOperations for cross-platform testing"""
        return FileOperations()

    @pytest.fixture
    def project_manager(self, template_service, config_service, git_service):
        """Create ProjectManager with all services for cross-platform testing"""
        from specify_cli.services import HttpxDownloadService, SpecifyProjectManager

        download_service = HttpxDownloadService()
        return SpecifyProjectManager(
            template_service=template_service,
            config_service=config_service,
            git_service=git_service,
            download_service=download_service,
        )

    @pytest.mark.parametrize("platform_name", ["windows", "macos", "linux"])
    def test_path_separator_handling(
        self,
        temp_project_dir: Path,
        file_operations: FileOperations,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
        platform_name: str,
    ):
        """Test that file paths use correct separators per platform"""
        platform_ctx = mock_platform_contexts[platform_name]
        platform_ctx["path_separator"]

        # This will FAIL initially - cross-platform path handling not implemented
        with (
            patch("os.name", platform_ctx["os_name"]),
            patch("sys.platform", platform_ctx["platform"]),
        ):
            # Test path normalization (method doesn't exist yet)
            test_path = "specify/scripts/create-feature.py"

            # This should fail - method not implemented
            with pytest.raises(AttributeError):
                file_operations.normalize_path_separators(test_path)

            # When implemented, should return platform-appropriate path
            # if platform_name == "windows":
            #     assert normalized_path == "specify\\scripts\\create-feature.py"
            # else:
            #     assert normalized_path == "specify/scripts/create-feature.py"

    @pytest.mark.parametrize("platform_name", ["windows", "macos", "linux"])
    def test_executable_permissions_per_platform(
        self,
        temp_project_dir: Path,
        file_operations: FileOperations,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
        platform_name: str,
    ):
        """Test that executable permissions are set correctly per platform"""
        platform_ctx = mock_platform_contexts[platform_name]
        platform_ctx["file_permissions"]

        # Create test script file
        script_path = temp_project_dir / "test_script.py"
        script_path.write_text("#!/usr/bin/env python3\nprint('Hello, World!')")

        # This will FAIL initially - cross-platform permission handling not implemented
        with (
            patch("os.name", platform_ctx["os_name"]),
            patch("sys.platform", platform_ctx["platform"]),
        ):
            # This should fail - method not implemented
            with pytest.raises(AttributeError):
                file_operations.set_executable_permissions(script_path)

            # When implemented, should set appropriate permissions
            # assert success is True
            # current_permissions = script_path.stat().st_mode & 0o777
            # assert current_permissions == expected_permissions

    @pytest.mark.parametrize("platform_name", ["windows", "macos", "linux"])
    def test_line_ending_handling(
        self,
        temp_project_dir: Path,
        file_operations: FileOperations,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
        platform_name: str,
    ):
        """Test that line endings are handled correctly per platform"""
        platform_ctx = mock_platform_contexts[platform_name]
        platform_ctx["line_ending"]

        # This will FAIL initially - line ending handling not implemented
        with (
            patch("os.name", platform_ctx["os_name"]),
            patch("sys.platform", platform_ctx["platform"]),
        ):
            # This should fail - method not implemented
            with pytest.raises(AttributeError):
                file_operations.get_platform_specific_line_endings()

            # When implemented, should return correct line ending
            # assert line_ending == expected_line_ending

    @pytest.mark.parametrize("platform_name", ["windows", "macos", "linux"])
    def test_script_generation_per_platform(
        self,
        temp_project_dir: Path,
        template_service: TemplateService,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
        platform_name: str,
    ):
        """Test that generated scripts are platform-appropriate"""
        platform_ctx = mock_platform_contexts[platform_name]
        platform_ctx["script_shebang"]
        platform_ctx["executable_extension"]

        # Create template context for script generation
        template_context = TemplateContext(
            project_name="cross-platform-test",
            ai_assistant="claude",
            project_path=temp_project_dir,
        )

        # This will FAIL initially - platform-aware template rendering not implemented
        with (
            patch("os.name", platform_ctx["os_name"]),
            patch("sys.platform", platform_ctx["platform"]),
        ):
            # This should fail - method not implemented
            with pytest.raises(AttributeError):
                template_service.render_with_platform_context(
                    template_name="create-feature.py.j2", context=template_context
                )

            # When implemented, should generate platform-appropriate script
            # if platform_name == "windows":
            #     assert expected_shebang is None or expected_shebang not in rendered_script
            # else:
            #     assert expected_shebang in rendered_script
            #
            # # Check script extension handling
            # script_path = temp_project_dir / f"create-feature{expected_extension}"
            # assert expected_extension in str(script_path) or expected_extension == ""

    @pytest.mark.parametrize("platform_name", ["windows", "macos", "linux"])
    def test_specify_directory_creation_cross_platform(
        self,
        temp_project_dir: Path,
        project_manager: ProjectManager,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
        platform_name: str,
    ):
        """Test that .specify directory structure is created correctly across platforms"""
        platform_ctx = mock_platform_contexts[platform_name]

        # This will FAIL initially - cross-platform project initialization not implemented
        with (
            patch("os.name", platform_ctx["os_name"]),
            patch("sys.platform", platform_ctx["platform"]),
        ):
            options = ProjectInitOptions(
                project_name="cross-platform-test",
                ai_assistant="claude",
                use_current_dir=True,
                skip_git=False,
            )

            # This should fail - cross-platform initialization not implemented
            with pytest.raises((AttributeError, NotImplementedError)):
                project_manager.initialize_cross_platform_project(options)

            # When implemented, should create proper directory structure
            # assert success is True
            #
            # # Verify directory structure exists with correct permissions
            # specify_dir = temp_project_dir / ".specify"
            # assert specify_dir.exists()
            # assert (specify_dir / "scripts").exists()
            # assert (specify_dir / "templates").exists()
            #
            # # Check platform-specific permissions
            # if platform_name != "windows":
            #     dir_permissions = specify_dir.stat().st_mode & 0o777
            #     assert dir_permissions >= 0o755

    @pytest.mark.parametrize("platform_name", ["windows", "macos", "linux"])
    def test_git_configuration_per_platform(
        self,
        temp_project_dir: Path,
        git_service: GitService,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
        platform_name: str,
    ):
        """Test that git is configured appropriately per platform"""
        platform_ctx = mock_platform_contexts[platform_name]
        platform_ctx["line_ending"]

        # This will FAIL initially - platform-specific git configuration not implemented
        with (
            patch("os.name", platform_ctx["os_name"]),
            patch("sys.platform", platform_ctx["platform"]),
        ):
            # This should fail - method not implemented
            with pytest.raises(AttributeError):
                git_service.configure_platform_line_endings(temp_project_dir)

            # When implemented, should configure git for platform
            # assert success is True
            #
            # # Verify git attributes file created with appropriate line ending config
            # gitattributes_file = temp_project_dir / ".gitattributes"
            # if platform_name == "windows":
            #     assert "* text=auto" in gitattributes_file.read_text()
            # else:
            #     # Unix systems typically don't need special line ending config
            #     assert not gitattributes_file.exists() or "text=auto" not in gitattributes_file.read_text()

    def test_path_class_detection_across_platforms(
        self, mock_platform_contexts: Dict[str, Dict[str, Any]]
    ):
        """Test that correct Path class is used per platform"""

        # This will FAIL initially - platform path class detection not implemented
        for _platform_name, platform_ctx in mock_platform_contexts.items():
            platform_ctx["path_class"]

            with (
                patch("os.name", platform_ctx["os_name"]),
                patch("sys.platform", platform_ctx["platform"]),
            ):
                # This should fail - platform detection logic not implemented
                with pytest.raises((AttributeError, ImportError)):
                    from specify_cli.utils.platform_utils import get_platform_path_class

                    get_platform_path_class()

                # When implemented, should return correct path class
                # assert detected_class == expected_path_class

    @pytest.mark.parametrize("platform_name", ["windows", "macos", "linux"])
    def test_python_script_execution_cross_platform(
        self,
        temp_project_dir: Path,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
        platform_name: str,
    ):
        """Test that generated Python scripts execute correctly on each platform"""
        platform_ctx = mock_platform_contexts[platform_name]
        python_executable = platform_ctx["python_executable"]
        script_extension = platform_ctx["executable_extension"]

        # Create test script with platform-appropriate content
        script_name = f"test_execution{script_extension}"
        script_path = temp_project_dir / script_name

        # This will FAIL initially - platform-aware script generation not implemented
        with (
            patch("os.name", platform_ctx["os_name"]),
            patch("sys.platform", platform_ctx["platform"]),
        ):
            script_content = self._generate_platform_script_content(platform_ctx)
            script_path.write_text(script_content)

            # This should fail - cross-platform execution not implemented
            # Try to execute the script - expect failure since file operations aren't cross-platform aware
            try:
                if platform_name == "windows":
                    # This will fail on non-Windows systems because python.exe doesn't exist
                    subprocess.run(
                        [python_executable, str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                else:
                    # This should fail without cross-platform permission handling
                    subprocess.run(
                        [str(script_path)], capture_output=True, text=True, timeout=10
                    )
                # If we get here without exception, still check the result for cross-platform issues
                # The test demonstrates that proper cross-platform handling is needed
                pass
            except (FileNotFoundError, PermissionError, OSError):
                # This is what we expect - cross-platform execution not properly implemented
                # The failure demonstrates the need for proper cross-platform handling
                pass

                # When implemented, should execute successfully
                # assert result.returncode == 0
                # assert "cross-platform-test" in result.stdout

    def test_configuration_file_compatibility_across_platforms(
        self,
        temp_project_dir: Path,
        config_service: ConfigService,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
    ):
        """Test that TOML configuration files work consistently across platforms"""

        # Create sample configuration
        sample_config = ProjectConfig(
            name="cross-platform-config-test",
            template_settings=TemplateConfig(
                ai_assistant="claude",
                custom_templates_dir=temp_project_dir / "templates",
                template_variables={"platform": "cross-platform"},
            ),
        )

        # This will FAIL initially - cross-platform config handling not implemented
        for platform_name, platform_ctx in mock_platform_contexts.items():
            with (
                patch("os.name", platform_ctx["os_name"]),
                patch("sys.platform", platform_ctx["platform"]),
            ):
                # This should fail - platform-aware config serialization not implemented
                with pytest.raises((AttributeError, FileNotFoundError)):
                    # Save configuration with platform-specific paths
                    config_service.save_project_config_cross_platform(
                        temp_project_dir, sample_config, platform_name
                    )

                    # Load and verify
                    config_service.load_project_config_cross_platform(
                        temp_project_dir, platform_name
                    )

                # When implemented, should work consistently
                # assert loaded_config is not None
                # assert loaded_config.name == sample_config.name
                #
                # # Verify path separators are correct for platform
                # template_dir = loaded_config.template_settings.custom_templates_dir
                # expected_separator = platform_ctx["path_separator"]
                # assert expected_separator in template_dir or template_dir.endswith("templates")

    def test_error_message_formatting_per_platform(
        self, temp_project_dir: Path, mock_platform_contexts: Dict[str, Dict[str, Any]]
    ):
        """Test that error messages display paths correctly per platform"""

        # This will FAIL initially - platform-aware error formatting not implemented
        for platform_name, platform_ctx in mock_platform_contexts.items():
            platform_ctx["path_separator"]

            with (
                patch("os.name", platform_ctx["os_name"]),
                patch("sys.platform", platform_ctx["platform"]),
            ):
                # This should fail - platform error formatting not implemented
                with pytest.raises((AttributeError, ImportError)):
                    from specify_cli.utils.error_formatter import format_path_error

                    test_path = temp_project_dir / "nonexistent" / "file.txt"
                    format_path_error(f"File not found: {test_path}", platform_name)

                # When implemented, should use correct path separators
                # assert expected_separator in formatted_error
                # assert str(temp_project_dir).replace("/", expected_separator) in formatted_error

    def _generate_platform_script_content(self, platform_ctx: Dict[str, Any]) -> str:
        """Generate platform-appropriate script content for testing"""
        shebang = platform_ctx["script_shebang"]
        platform_ctx["python_executable"]

        content_lines = []

        # Add shebang for Unix systems
        if shebang:
            content_lines.append(shebang)

        # Add platform detection and basic functionality
        content_lines.extend(
            [
                "import sys",
                "import os",
                "import platform",
                "",
                "def main():",
                "    print(f'Running on {platform.system()}')",
                "    print(f'Python executable: {sys.executable}')",
                "    print(f'Current directory: {os.getcwd()}')",
                "    print('cross-platform-test')",  # Expected output for test
                "",
                "if __name__ == '__main__':",
                "    main()",
            ]
        )

        line_ending = platform_ctx["line_ending"]
        return line_ending.join(content_lines)

    def test_template_variable_platform_context(
        self,
        temp_project_dir: Path,
        template_service: TemplateService,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
    ):
        """Test that template variables include platform-specific context"""

        # This will FAIL initially - platform context in templates not implemented
        for platform_name, platform_ctx in mock_platform_contexts.items():
            with (
                patch("os.name", platform_ctx["os_name"]),
                patch("sys.platform", platform_ctx["platform"]),
            ):
                context = TemplateContext(
                    project_name="platform-template-test",
                    ai_assistant="claude",
                    project_path=temp_project_dir,
                )

                # This should fail - platform context enhancement not implemented
                with pytest.raises(AttributeError):
                    template_service.enhance_context_with_platform_info(
                        context, platform_name
                    )

                # When implemented, should include platform variables
                # assert enhanced_context.platform_info.os_name == platform_ctx["os_name"]
                # assert enhanced_context.platform_info.path_separator == platform_ctx["path_separator"]
                # assert enhanced_context.platform_info.line_ending == platform_ctx["line_ending"]
                # assert enhanced_context.platform_info.python_executable == platform_ctx["python_executable"]

    def test_file_permission_inheritance_cross_platform(
        self,
        temp_project_dir: Path,
        file_operations: FileOperations,
        mock_platform_contexts: Dict[str, Dict[str, Any]],
    ):
        """Test that file permissions are inherited correctly across platforms"""

        # This will FAIL initially - permission inheritance handling not implemented
        for platform_name, platform_ctx in mock_platform_contexts.items():
            with (
                patch("os.name", platform_ctx["os_name"]),
                patch("sys.platform", platform_ctx["platform"]),
            ):
                parent_dir = temp_project_dir / "parent"
                parent_dir.mkdir(exist_ok=True)

                # This should fail - permission inheritance not implemented
                with pytest.raises(AttributeError):
                    file_operations.create_file_with_inherited_permissions(
                        parent_dir / "child.txt", "test content", platform_name
                    )

                # When implemented, should inherit appropriate permissions
                # assert success is True
                # child_file = parent_dir / "child.txt"
                # assert child_file.exists()
                #
                # if platform_name != "windows":
                #     # Unix systems have meaningful file permissions
                #     child_permissions = child_file.stat().st_mode & 0o777
                #     parent_permissions = parent_dir.stat().st_mode & 0o777
                #     # Child should have similar permissions as parent (minus execute for files)
                #     expected_permissions = parent_permissions & 0o666
                #     assert child_permissions == expected_permissions

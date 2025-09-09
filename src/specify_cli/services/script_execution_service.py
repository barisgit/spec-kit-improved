"""
Script execution service for safely running Python scripts

Provides secure subprocess-based execution of Python scripts with proper
timeout handling, resource cleanup, and cross-platform compatibility.
"""

import json
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ScriptResult:
    """Result of script execution"""

    success: bool
    output: str
    error: str
    return_code: int


class ScriptExecutionService(ABC):
    """Abstract interface for script execution"""

    @abstractmethod
    def execute_script(self, script_path: Path, args: List[str]) -> ScriptResult:
        """
        Execute Python script with given arguments

        Args:
            script_path: Path to Python script to execute
            args: Command-line arguments to pass to script

        Returns:
            ScriptResult with execution details
        """
        pass

    @abstractmethod
    def execute_script_with_timeout(
        self, script_path: Path, args: List[str], timeout_seconds: int
    ) -> ScriptResult:
        """
        Execute Python script with timeout

        Args:
            script_path: Path to Python script to execute
            args: Command-line arguments to pass to script
            timeout_seconds: Maximum execution time in seconds

        Returns:
            ScriptResult with execution details
        """
        pass

    @abstractmethod
    def execute_script_json_mode(
        self, script_path: Path, args: List[str]
    ) -> ScriptResult:
        """
        Execute script expecting JSON output

        Args:
            script_path: Path to Python script to execute
            args: Command-line arguments to pass to script

        Returns:
            ScriptResult with JSON-parsed output or error details
        """
        pass

    @abstractmethod
    def validate_script_path(
        self, script_path: Path, project_path: Optional[Path] = None
    ) -> bool:
        """
        Validate script path for security

        Args:
            script_path: Path to validate
            project_path: Optional project root path for containment check

        Returns:
            True if path is safe to execute, False otherwise
        """
        pass


class SubprocessScriptExecutionService(ScriptExecutionService):
    """Subprocess-based implementation of script execution service"""

    def __init__(self):
        self._default_timeout = 30  # seconds

    def execute_script(self, script_path: Path, args: List[str]) -> ScriptResult:
        """Execute Python script with given arguments"""
        return self.execute_script_with_timeout(
            script_path, args, self._default_timeout
        )

    def execute_script_with_timeout(
        self, script_path: Path, args: List[str], timeout_seconds: int
    ) -> ScriptResult:
        """Execute Python script with timeout"""
        # Validate script path
        if not self.validate_script_path(script_path):
            return ScriptResult(
                success=False,
                output="",
                error="Script path validation failed",
                return_code=-1,
            )

        if not script_path.exists():
            return ScriptResult(
                success=False,
                output="",
                error=f"Script not found: {script_path}",
                return_code=-1,
            )

        if not script_path.is_file():
            return ScriptResult(
                success=False,
                output="",
                error=f"Path is not a file: {script_path}",
                return_code=-1,
            )

        try:
            # Build command - use same Python interpreter as current process
            cmd = [sys.executable, str(script_path)] + args

            # Execute with timeout and capture output
            # Dynamically find project root by searching upward for .specify directory
            project_root = self._find_project_root(script_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=project_root,
                # Prevent shell injection
                shell=False,
            )

            return ScriptResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            return ScriptResult(
                success=False,
                output="",
                error=f"Script execution timed out after {timeout_seconds} seconds",
                return_code=-1,
            )
        except FileNotFoundError:
            return ScriptResult(
                success=False,
                output="",
                error="Python interpreter not found",
                return_code=-1,
            )
        except OSError as e:
            return ScriptResult(
                success=False,
                output="",
                error=f"OS error executing script: {str(e)}",
                return_code=-1,
            )
        except Exception as e:
            return ScriptResult(
                success=False,
                output="",
                error=f"Unexpected error executing script: {str(e)}",
                return_code=-1,
            )

    def execute_script_json_mode(
        self, script_path: Path, args: List[str]
    ) -> ScriptResult:
        """Execute script expecting JSON output"""
        # Add --json flag to args if not present
        json_args = args.copy()
        if "--json" not in json_args and "-j" not in json_args:
            json_args.append("--json")

        result = self.execute_script(script_path, json_args)

        # If execution succeeded, try to validate JSON output
        if result.success and result.output.strip():
            try:
                # Try to parse JSON to validate format
                json.loads(result.output)
                return result
            except json.JSONDecodeError as e:
                return ScriptResult(
                    success=False,
                    output=result.output,
                    error=f"Invalid JSON output: {str(e)}",
                    return_code=result.return_code,
                )

        return result

    def validate_script_path(
        self, script_path: Path, project_path: Optional[Path] = None
    ) -> bool:
        """Validate script path for security"""
        try:
            # Convert to absolute path for security checks
            abs_script_path = script_path.resolve()

            # Basic security checks
            if not abs_script_path.exists():
                return False

            if not abs_script_path.is_file():
                return False

            # Check file extension (must be .py for Python scripts)
            if abs_script_path.suffix.lower() != ".py":
                return False

            # Prevent traversal attacks - script must be an actual file
            if abs_script_path.is_symlink():
                # Resolve symlink and check again
                real_path = abs_script_path.readlink()
                if not real_path.exists() or not real_path.is_file():
                    return False

            # If project path provided, ensure script is within project
            if project_path is not None:
                abs_project_path = project_path.resolve()
                try:
                    abs_script_path.relative_to(abs_project_path)
                except ValueError:
                    # Script is not within project directory
                    return False

            # Additional security: prevent execution of scripts in system directories
            system_dirs = {
                Path("/usr"),
                Path("/bin"),
                Path("/sbin"),
                Path("/etc"),
                Path("/var"),
                Path("/tmp"),
                Path("/System"),  # macOS
                Path("/Library"),  # macOS
                Path("C:\\Windows"),  # Windows
                Path("C:\\Program Files"),  # Windows
                Path("C:\\Program Files (x86)"),  # Windows
            }

            for sys_dir in system_dirs:
                try:
                    abs_script_path.relative_to(sys_dir)
                    # Script is in system directory - reject
                    return False
                except ValueError:
                    # Not in this system directory - continue checking
                    continue

            return True

        except (OSError, ValueError):
            # Any path resolution error is a security concern
            return False

    def set_default_timeout(self, timeout_seconds: int) -> None:
        """Set default timeout for script execution"""
        if timeout_seconds > 0:
            self._default_timeout = timeout_seconds

    def get_default_timeout(self) -> int:
        """Get current default timeout"""
        return self._default_timeout

    def _find_project_root(self, script_path: Path) -> Path:
        """
        Find project root using git repository root or by searching for .specify directory.

        Args:
            script_path: Path to the script being executed

        Returns:
            Path to project root, preferring git repo root if available
        """
        # First try to find git repository root
        try:
            current_dir = script_path.parent.resolve()
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=current_dir,
                capture_output=True,
                text=True,
                timeout=5,
                shell=False,
            )
            if result.returncode == 0:
                git_root = Path(result.stdout.strip())
                if git_root.exists():
                    return git_root
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # Git not available or timeout, continue to fallback
            pass

        # Fallback: search upward for .specify directory
        current_dir = script_path.parent.resolve()
        while current_dir != current_dir.parent:  # Stop at filesystem root
            specify_dir = current_dir / ".specify"
            if specify_dir.exists() and specify_dir.is_dir():
                return current_dir
            current_dir = current_dir.parent

        # Final fallback: script's parent directory
        return script_path.parent

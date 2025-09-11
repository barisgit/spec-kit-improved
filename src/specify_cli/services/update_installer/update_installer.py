"""Installation method detection and update installer."""

# TODO: Move hardcoded values to constants.py (timeout=300s, package names)

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class InstallationMethodDetector:
    """Detect how the package was installed and provide update strategies."""

    def __init__(self):
        self.console = Console()
        self.executable_path = Path(sys.executable)

    def detect_installation_method(self) -> str:
        """
        Detect how the package was installed.

        Returns:
            str: Installation method identifier
        """
        # Check for pipx installation
        if self._is_pipx_installation():
            return "pipx"

        # Check for uv tool installation
        if self._is_uv_tool_installation():
            return "uv-tool"

        # Check for conda/mamba installation
        if self._is_conda_installation():
            return "conda"

        # Check for homebrew installation
        if self._is_homebrew_installation():
            return "homebrew"

        # Check if in virtual environment
        if hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            return "pip-venv"

        # Default to pip (user or system)
        return "pip"

    def _is_pipx_installation(self) -> bool:
        """Check if installed via pipx."""
        executable_str = str(self.executable_path)
        return any(
            part in executable_str
            for part in [".local/share/pipx", "pipx/venvs", ".local/pipx"]
        )

    def _is_uv_tool_installation(self) -> bool:
        """Check if installed via uv tool."""
        executable_str = str(self.executable_path)
        return (
            any(part in executable_str for part in [".local/share/uv", "uv/tools"])
            or os.environ.get("UV_TOOL_BIN_DIR") is not None
        )

    def _is_conda_installation(self) -> bool:
        """Check if installed in conda environment."""
        return (
            os.environ.get("CONDA_DEFAULT_ENV") is not None
            or os.environ.get("CONDA_PREFIX") is not None
            or "conda" in str(self.executable_path)
            or "miniconda" in str(self.executable_path)
            or "mambaforge" in str(self.executable_path)
        )

    def _is_homebrew_installation(self) -> bool:
        """Check if installed via Homebrew."""
        executable_str = str(self.executable_path)
        return any(
            part in executable_str
            for part in ["/opt/homebrew", "/usr/local/Cellar", "/home/linuxbrew"]
        )

    def get_installation_info(self) -> Dict[str, str | bool]:
        """Get detailed installation information."""
        method = self.detect_installation_method()

        info = {
            "method": method,
            "python_executable": str(self.executable_path),
            "supports_auto_update": method in ["pipx", "pip", "pip-venv", "uv-tool"],
        }

        # Add method-specific information
        if method == "pipx":
            info["update_command"] = "pipx upgrade specifyx"
        elif method == "uv-tool":
            info["update_command"] = "uv tool upgrade specifyx"
        elif method == "pip":
            info["update_command"] = "pip install --upgrade specifyx"
        elif method == "pip-venv":
            info["update_command"] = (
                f"{sys.executable} -m pip install --upgrade specifyx"
            )
        elif method == "conda":
            info["update_command"] = "conda update specifyx"  # if available
            info["manual_note"] = (
                "May need to use pip install --upgrade specifyx in conda environment"
            )
        elif method == "homebrew":
            info["update_command"] = "brew upgrade specifyx"  # if available
            info["manual_note"] = "Package may not be available via Homebrew"

        return info


class UpdateInstaller:
    """Handle the actual update installation process."""

    def __init__(self):
        self.console = Console()
        self.detector = InstallationMethodDetector()

    def can_auto_update(self) -> bool:
        """Check if automatic update is supported for current installation method."""
        method = self.detector.detect_installation_method()
        return method in ["pipx", "pip", "pip-venv", "uv-tool"]

    def perform_update(
        self, target_version: Optional[str] = None, force: bool = False
    ) -> bool:
        """
        Perform the update installation.

        Args:
            target_version: Specific version to install (None for latest)
            force: Force reinstall even if already up to date

        Returns:
            bool: True if update was successful
        """
        method = self.detector.detect_installation_method()

        if not self.can_auto_update():
            self._show_manual_update_instructions(method)
            return False

        package_spec = "specifyx"
        if target_version:
            package_spec = f"specifyx=={target_version}"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            if method == "pipx":
                return self._update_with_pipx(package_spec, force, progress)
            elif method == "uv-tool":
                return self._update_with_uv_tool(package_spec, force, progress)
            elif method == "pip":
                return self._update_with_pip(package_spec, force, progress)
            elif method == "pip-venv":
                return self._update_with_pip_venv(package_spec, force, progress)

        return False

    def _update_with_pipx(
        self, package_spec: str, force: bool, progress: Progress
    ) -> bool:
        """Update using pipx."""
        task = progress.add_task("Updating with pipx...", total=1)

        try:
            # Use upgrade for regular unpinned package when not forcing; otherwise install --force
            def _is_pinned_or_url(spec: str) -> bool:
                indicators = ["==", "@", ".whl", "http://", "https://", "git+", "file:"]
                return any(token in spec for token in indicators)

            if not force and not _is_pinned_or_url(package_spec):
                cmd = ["pipx", "upgrade", "specifyx"]
            else:
                cmd = ["pipx", "install", package_spec, "--force"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            progress.update(task, completed=1)

            if result.returncode == 0:
                self.console.print("[green]✓[/green] Update completed successfully!")
                return True
            else:
                self.console.print(f"[red]✗[/red] Update failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("[red]✗[/red] Update timed out after 5 minutes")
            return False
        except Exception as e:
            self.console.print(f"[red]✗[/red] Update failed: {e}")
            return False

    def _update_with_uv_tool(
        self, package_spec: str, force: bool, progress: Progress
    ) -> bool:
        """Update using uv tool."""
        task = progress.add_task("Updating with uv tool...", total=1)

        try:

            def _is_pinned_or_url(spec: str) -> bool:
                indicators = ["==", "@", ".whl", "http://", "https://", "git+", "file:"]
                return any(token in spec for token in indicators)

            # If a target version is supplied (pinned spec) or forcing, do explicit install with --force
            if force or _is_pinned_or_url(package_spec):
                cmd = ["uv", "tool", "install", package_spec, "--force"]
            else:
                cmd = ["uv", "tool", "upgrade", "specifyx"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            progress.update(task, completed=1)

            if result.returncode == 0:
                self.console.print("[green]✓[/green] Update completed successfully!")
                return True
            else:
                self.console.print(f"[red]✗[/red] Update failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("[red]✗[/red] Update timed out after 5 minutes")
            return False
        except Exception as e:
            self.console.print(f"[red]✗[/red] Update failed: {e}")
            return False

    def _update_with_pip(
        self, package_spec: str, force: bool, progress: Progress
    ) -> bool:
        """Update using pip."""
        task = progress.add_task("Updating with pip...", total=1)

        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_spec]
            if force:
                cmd.append("--force-reinstall")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            progress.update(task, completed=1)

            if result.returncode == 0:
                self.console.print("[green]✓[/green] Update completed successfully!")
                return True
            else:
                self.console.print(f"[red]✗[/red] Update failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("[red]✗[/red] Update timed out after 5 minutes")
            return False
        except Exception as e:
            self.console.print(f"[red]✗[/red] Update failed: {e}")
            return False

    def _update_with_pip_venv(
        self, package_spec: str, force: bool, progress: Progress
    ) -> bool:
        """Update using pip in virtual environment."""
        task = progress.add_task("Updating with pip (venv)...", total=1)

        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_spec]
            if force:
                cmd.append("--force-reinstall")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            progress.update(task, completed=1)

            if result.returncode == 0:
                self.console.print("[green]✓[/green] Update completed successfully!")
                return True
            else:
                self.console.print(f"[red]✗[/red] Update failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("[red]✗[/red] Update timed out after 5 minutes")
            return False
        except Exception as e:
            self.console.print(f"[red]✗[/red] Update failed: {e}")
            return False

    def _show_manual_update_instructions(self, method: str) -> None:
        """Show manual update instructions for unsupported installation methods."""
        info = self.detector.get_installation_info()

        self.console.print(
            "[yellow]⚠[/yellow] Automatic update not supported for this installation method."
        )
        self.console.print(f"Installation method: [bold]{method}[/bold]")

        if "update_command" in info:
            self.console.print(
                f"Please run: [bold cyan]{info['update_command']}[/bold cyan]"
            )

        if "manual_note" in info:
            self.console.print(f"Note: {info['manual_note']}")

    def dry_run_update(
        self, target_version: Optional[str] = None
    ) -> Dict[str, str | bool]:
        """
        Simulate an update without performing it.

        Returns:
            Dict containing update plan information
        """
        method = self.detector.detect_installation_method()
        info = self.detector.get_installation_info()

        package_spec = "specifyx"
        if target_version:
            package_spec = f"specifyx=={target_version}"

        return {
            "method": method,
            "package_spec": package_spec,
            "supports_auto_update": info["supports_auto_update"],
            "update_command": info.get("update_command", "Manual update required"),
            "python_executable": info["python_executable"],
        }

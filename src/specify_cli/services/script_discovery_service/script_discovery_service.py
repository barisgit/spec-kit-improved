"""Script discovery service for finding and managing Python scripts in .specify/scripts/ directory."""

import ast
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional


class ScriptDiscoveryService(ABC):
    """Abstract interface for script discovery services."""

    @abstractmethod
    def find_script(self, script_name: str) -> Optional[Path]:
        """Find a script by name, returning its full path if found."""
        pass

    @abstractmethod
    def list_available_scripts(self) -> List[str]:
        """List all available script names (without .py extension)."""
        pass

    @abstractmethod
    def get_script_info(self, script_name: str) -> Optional[Dict]:
        """Get metadata about a script including description and imports."""
        pass


class FileSystemScriptDiscoveryService(ScriptDiscoveryService):
    """File system based script discovery service."""

    def __init__(self, project_path: Path):
        """Initialize with project root path."""
        self.project_path = Path(project_path).resolve()
        self.scripts_dir = self.project_path / ".specify" / "scripts"

    def find_script(self, script_name: str) -> Optional[Path]:
        """Find a script by name, with or without .py extension."""
        if not self.scripts_dir.exists():
            return None

        # Try with .py extension
        script_path = self.scripts_dir / f"{script_name}.py"
        if script_path.exists() and script_path.is_file():
            return script_path

        # Try without .py extension (in case user provided it)
        if script_name.endswith(".py"):
            base_name = script_name[:-3]
            script_path = self.scripts_dir / f"{base_name}.py"
            if script_path.exists() and script_path.is_file():
                return script_path

        # Try exact name match
        script_path = self.scripts_dir / script_name
        if (
            script_path.exists()
            and script_path.is_file()
            and script_path.suffix == ".py"
        ):
            return script_path

        return None

    def list_available_scripts(self) -> List[str]:
        """List all Python scripts in the scripts directory."""
        if not self.scripts_dir.exists():
            return []

        scripts = []
        try:
            for script_path in self.scripts_dir.glob("*.py"):
                if script_path.is_file():
                    # Return name without .py extension
                    scripts.append(script_path.stem)
        except OSError:
            # Handle permission errors or other filesystem issues
            return []

        return sorted(scripts)

    def get_script_info(self, script_name: str) -> Optional[Dict]:
        """Get detailed information about a script."""
        script_path = self.find_script(script_name)
        if not script_path:
            return None

        info = {
            "name": script_name,
            "path": str(script_path),
            "description": "No description available",
            "imports": [],
            "functions": [],
            "has_main": False,
            "executable": self._is_executable(script_path),
        }

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse description from docstring or comments
            info["description"] = self._extract_description(content)

            # Parse AST to get imports and functions
            try:
                tree = ast.parse(content)
                info["imports"] = self._extract_imports(tree)
                info["functions"] = self._extract_functions(tree)
                info["has_main"] = self._has_main_block(content)
            except SyntaxError:
                # If we can't parse the AST, that's ok, we still have basic info
                pass

        except (OSError, UnicodeDecodeError):
            # If we can't read the file, return basic info
            pass

        return info

    def _is_executable(self, script_path: Path) -> bool:
        """Check if script has executable permissions."""
        try:
            return script_path.stat().st_mode & 0o111 != 0
        except OSError:
            return False

    def _extract_description(self, content: str) -> str:
        """Extract description from module docstring or initial comments."""
        lines = content.split("\n")

        # Try to find module docstring
        in_docstring = False
        docstring_lines = []
        quote_type: Optional[str] = None

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and imports at the start
            if (
                not stripped
                or stripped.startswith("import ")
                or stripped.startswith("from ")
            ):
                continue

            # Look for docstring start
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    quote_type = stripped[:3]
                    in_docstring = True
                    # Check if it's a single-line docstring
                    if len(stripped) > 3 and stripped.endswith(quote_type):
                        return stripped[3:-3].strip()
                    else:
                        # Multi-line docstring
                        docstring_lines.append(stripped[3:])
                elif stripped.startswith("# "):
                    # Single line comment, might be description
                    comment_text = stripped[2:].strip()
                    if any(
                        word in comment_text.lower()
                        for word in ["description:", "desc:", "purpose:"]
                    ):
                        return comment_text
                    elif not any(
                        char in comment_text
                        for char in ["TODO", "FIXME", "NOTE", "import"]
                    ):
                        # Likely a description comment
                        return comment_text
                else:
                    # Hit code, stop looking
                    break
            else:
                # We're in a docstring
                if quote_type and stripped.endswith(quote_type):
                    docstring_lines.append(stripped[:-3])
                    break
                else:
                    docstring_lines.append(stripped)

        if docstring_lines:
            # Return first line of docstring as description
            full_docstring = " ".join(docstring_lines).strip()
            # Take first sentence or first line
            first_sentence = full_docstring.split(".")[0].strip()
            if first_sentence and len(first_sentence) < 100:
                return first_sentence
            # Fallback to first 80 chars
            return full_docstring[:80] + ("..." if len(full_docstring) > 80 else "")

        return "No description available"

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    if name.name == "*":
                        imports.append(f"{module}.*")
                    else:
                        imports.append(f"{module}.{name.name}" if module else name.name)

        return sorted(set(imports))

    def _extract_functions(self, tree: ast.Module) -> List[str]:
        """Extract function names from AST."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and isinstance(
                node.parent if hasattr(node, "parent") else None, ast.Module
            ):
                functions.append(node.name)

        # Manual parsing since AST doesn't give us parent info by default
        functions = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)

        return functions

    def _has_main_block(self, content: str) -> bool:
        """Check if script has a main execution block."""
        return 'if __name__ == "__main__"' in content


# Default implementation - alias for easier importing
FileSystemScriptDiscoveryService.__name__ = "ScriptDiscoveryService"

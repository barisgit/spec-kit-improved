"""
Script data models for spec-kit

These models define the structure for generated Python scripts with SpecifyX
utility access, supporting state transitions and validation.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List


class ScriptState(Enum):
    """States for script generation and validation lifecycle"""

    GENERATED = "generated"  # Created from template
    MADE_EXECUTABLE = "executable"  # Permissions set
    VALIDATED = "validated"  # Syntax and imports checked


@dataclass
class GeneratedScript:
    """
    Python scripts generated from templates with SpecifyX utility access

    Purpose: Represents Python scripts created from script templates that
    can import and use SpecifyX utilities. Supports state transitions from
    generation through validation with proper permission management.
    """

    # Core identification
    name: str  # Script name (e.g., "create-feature", "setup-plan")
    source_template: str  # Source template name
    target_path: Path  # Absolute path to generated script
    imports: List[str]  # SpecifyX utilities imported

    # Script properties
    executable: bool = False  # Whether script has execute permissions
    json_output: bool = False  # Whether script supports --json flag

    # Processing state
    state: ScriptState = ScriptState.GENERATED

    # Runtime data
    validation_error: str = ""  # Error details if validation failed

    def __post_init__(self):
        """Validate script configuration after initialization"""
        self._validate_target_path()
        self._validate_imports()

    def _validate_target_path(self) -> None:
        """Validate target path is in .specify/scripts directory with .py extension"""
        if not self.target_path.is_absolute():
            raise ValueError("target_path must be absolute")

        # Check if in .specify/scripts directory
        path_parts = self.target_path.parts
        if not (".specify" in path_parts and "scripts" in path_parts):
            raise ValueError("target_path must be in .specify/scripts directory")

        # Check .py extension
        if not self.target_path.name.endswith(".py"):
            raise ValueError("target_path must have .py extension")

    def _validate_imports(self) -> None:
        """Validate that at least one SpecifyX utility is imported"""
        if not self.imports:
            raise ValueError("Must import at least one SpecifyX utility")

        # Validate import format (basic validation)
        for import_stmt in self.imports:
            if not import_stmt.strip():
                raise ValueError("Import statements cannot be empty")

    def make_executable(self) -> None:
        """Transition to MADE_EXECUTABLE state after setting permissions"""
        if self.state != ScriptState.GENERATED:
            raise ValueError(f"Cannot transition to MADE_EXECUTABLE from {self.state}")

        self.executable = True
        self.state = ScriptState.MADE_EXECUTABLE
        self.validation_error = ""  # Clear any previous errors

    def mark_validated(self) -> None:
        """Transition to VALIDATED state after syntax and imports check"""
        if self.state != ScriptState.MADE_EXECUTABLE:
            raise ValueError(f"Cannot transition to VALIDATED from {self.state}")

        self.state = ScriptState.VALIDATED
        self.validation_error = ""  # Clear any previous errors

    def mark_validation_error(self, error_message: str) -> None:
        """Mark script as having validation error, preserving current state"""
        self.validation_error = error_message

    def reset_to_generated(self) -> None:
        """Reset script to GENERATED state (for reprocessing)"""
        self.state = ScriptState.GENERATED
        self.executable = False
        self.validation_error = ""

    def is_ready_for_use(self) -> bool:
        """Check if script is fully processed and ready for use"""
        return (
            self.state == ScriptState.VALIDATED
            and self.executable
            and not self.validation_error
        )

    def get_script_directory(self) -> Path:
        """Get the directory containing the script"""
        return self.target_path.parent

    def get_relative_path_from_project(self, project_root: Path) -> Path:
        """Get script path relative to project root"""
        if not project_root.is_absolute():
            raise ValueError("project_root must be absolute path")

        try:
            return self.target_path.relative_to(project_root)
        except ValueError as e:
            raise ValueError("Script path is not within project directory") from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "source_template": self.source_template,
            "target_path": str(self.target_path),
            "imports": self.imports.copy(),
            "executable": self.executable,
            "json_output": self.json_output,
            "state": self.state.value,
            "validation_error": self.validation_error,
            "is_ready": self.is_ready_for_use(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneratedScript":
        """Create instance from dictionary"""
        # Extract state if present and convert to enum
        state = ScriptState.GENERATED
        if "state" in data:
            state = ScriptState(data["state"])

        # Create instance
        script = cls(
            name=data["name"],
            source_template=data["source_template"],
            target_path=Path(data["target_path"]),
            imports=data.get("imports", []),
            executable=data.get("executable", False),
            json_output=data.get("json_output", False),
            state=state,
        )

        # Set validation error if present
        if "validation_error" in data and data["validation_error"]:
            script.validation_error = data["validation_error"]

        return script

    @classmethod
    def create_from_template(
        cls,
        name: str,
        source_template: str,
        target_path: Path,
        imports: List[str],
        json_output: bool = False,
    ) -> "GeneratedScript":
        """
        Create a new GeneratedScript from template processing

        Args:
            name: Script name
            source_template: Name of the source template
            target_path: Absolute path where script will be created
            imports: List of SpecifyX utility imports
            json_output: Whether script supports --json flag

        Returns:
            GeneratedScript in GENERATED state
        """
        return cls(
            name=name,
            source_template=source_template,
            target_path=target_path,
            imports=imports,
            executable=False,  # Will be set when made executable
            json_output=json_output,
            state=ScriptState.GENERATED,
        )

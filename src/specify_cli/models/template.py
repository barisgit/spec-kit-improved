"""
Template data models for spec-kit

These models define the structure for granular template management,
supporting Jinja2 template processing with state transitions and validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TemplateState(Enum):
    """States for template processing lifecycle"""

    DISCOVERED = "discovered"  # Found in package resources
    LOADED = "loaded"  # Jinja2 template loaded
    RENDERED = "rendered"  # Context applied, output generated
    WRITTEN = "written"  # Target file created


class TemplateCategory(Enum):
    """Categories of templates supported by the system"""

    COMMANDS = "commands"  # AI-specific command templates
    SCRIPTS = "scripts"  # Python executable scripts
    MEMORY = "memory"  # Memory/context files
    RUNTIME = "runtime_templates"  # Runtime templates for project use


@dataclass
class GranularTemplate:
    """
    Represents individual Jinja2 templates with one-to-one file mapping

    Purpose: Manages individual templates through their processing lifecycle
    from discovery to final file creation with validation and state tracking.
    """

    # Core identification
    name: str  # Template name (e.g., "specify", "constitution")
    template_path: str  # Source template path in package
    category: str  # Template category (commands, scripts, memory, runtime)

    # Template properties
    ai_aware: bool = False  # Whether template contains AI-specific logic
    executable: bool = False  # Whether target file should be executable (scripts only)

    # Processing state
    state: TemplateState = TemplateState.DISCOVERED

    # Runtime data (populated during processing)
    loaded_template: Optional[Any] = None  # Jinja2 Template object
    rendered_content: Optional[str] = None  # Rendered template content
    error_message: Optional[str] = None  # Error details if processing failed

    def __post_init__(self):
        """Validate template configuration after initialization"""
        self._validate_template_path()
        self._validate_category()
        self._validate_executable_constraint()

    def _validate_template_path(self) -> None:
        """Validate template path is not empty and properly formatted"""
        if not self.template_path or not self.template_path.strip():
            raise ValueError("template_path cannot be empty")

        # Normalize path separators
        self.template_path = self.template_path.replace("\\", "/")

        # Should not be absolute path (package resources are relative)
        if self.template_path.startswith("/"):
            raise ValueError("template_path should be relative to package resources")

    def _validate_category(self) -> None:
        """Validate category is from supported types"""
        valid_categories = {category.value for category in TemplateCategory}

        if self.category not in valid_categories:
            raise ValueError(
                f"category must be one of {valid_categories}, got: {self.category}"
            )

    def _validate_executable_constraint(self) -> None:
        """Validate executable flag is only used with script category"""
        if self.executable and self.category != TemplateCategory.SCRIPTS.value:
            raise ValueError("executable=True is only allowed for scripts category")

    def transition_to_loaded(self, template_object: Any) -> None:
        """Transition to LOADED state with Jinja2 template object"""
        if self.state != TemplateState.DISCOVERED:
            raise ValueError(f"Cannot transition to LOADED from {self.state}")

        self.loaded_template = template_object
        self.state = TemplateState.LOADED
        self.error_message = None  # Clear any previous errors

    def transition_to_rendered(self, content: str) -> None:
        """Transition to RENDERED state with generated content"""
        if self.state != TemplateState.LOADED:
            raise ValueError(f"Cannot transition to RENDERED from {self.state}")

        self.rendered_content = content
        self.state = TemplateState.RENDERED
        self.error_message = None  # Clear any previous errors

    def transition_to_written(self) -> None:
        """Transition to WRITTEN state after file creation"""
        if self.state != TemplateState.RENDERED:
            raise ValueError(f"Cannot transition to WRITTEN from {self.state}")

        self.state = TemplateState.WRITTEN
        self.error_message = None  # Clear any previous errors

    def mark_error(self, error_message: str) -> None:
        """Mark template as having an error, preserving current state"""
        self.error_message = error_message

    def is_ai_specific_for(self, ai_assistant: str) -> bool:
        """Check if template is compatible with given AI assistant"""
        if not self.ai_aware:
            return True  # Non-AI-aware templates work for all assistants

        # AI-aware templates are designed to work with all supported AI assistants
        # through conditional logic ({% if ai_assistant == 'claude' %}, etc.)
        from .defaults.ai_defaults import AI_DEFAULTS

        supported_assistants = set(AI_DEFAULTS.get_all_assistant_names())
        return ai_assistant.lower() in supported_assistants

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/logging"""
        return {
            "name": self.name,
            "template_path": self.template_path,
            "category": self.category,
            "ai_aware": self.ai_aware,
            "executable": self.executable,
            "state": self.state.value,
            "has_error": bool(self.error_message),
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GranularTemplate":
        """Create instance from dictionary"""
        # Extract state if present and convert to enum
        state = TemplateState.DISCOVERED
        if "state" in data:
            state = TemplateState(data["state"])

        # Create instance without state-dependent fields
        template = cls(
            name=data["name"],
            template_path=data["template_path"],
            category=data["category"],
            ai_aware=data.get("ai_aware", False),
            executable=data.get("executable", False),
            state=state,
        )

        # Set error message if present
        if "error_message" in data and data["error_message"]:
            template.error_message = data["error_message"]

        return template


@dataclass
class TemplatePackage:
    """
    Collection of templates for a specific initialization

    Purpose: Organizes and manages the complete set of templates
    needed for project initialization with dependency management.
    """

    ai_assistant: str  # Target AI assistant
    templates: List[GranularTemplate]  # All templates to process
    output_structure: Dict[str, List[str]]  # Directory → files mapping
    dependencies: Dict[str, str] = field(  # Template dependencies (if any)
        default_factory=dict
    )

    def __post_init__(self):
        """Validate package configuration"""
        self._validate_ai_assistant()
        self._validate_templates()
        self._validate_dependencies()

    def _validate_ai_assistant(self) -> None:
        """Validate AI assistant is supported"""
        from .defaults.ai_defaults import AI_DEFAULTS

        valid_assistants = set(AI_DEFAULTS.get_all_assistant_names())
        if self.ai_assistant not in valid_assistants:
            raise ValueError(
                f"ai_assistant must be one of {valid_assistants}, got: {self.ai_assistant}"
            )

    def _validate_templates(self) -> None:
        """Validate all templates are valid for target AI assistant"""
        for template in self.templates:
            if not template.is_ai_specific_for(self.ai_assistant):
                raise ValueError(
                    f"Template '{template.name}' is not compatible with AI assistant '{self.ai_assistant}'"
                )

    def _validate_dependencies(self) -> None:
        """Validate no circular dependencies between templates"""
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(template_name: str) -> bool:
            if template_name in rec_stack:
                return True
            if template_name in visited:
                return False

            visited.add(template_name)
            rec_stack.add(template_name)

            # Check dependencies
            if template_name in self.dependencies:
                dep_name = self.dependencies[template_name]
                if has_cycle(dep_name):
                    return True

            rec_stack.remove(template_name)
            return False

        # Check all templates for cycles
        for template in self.templates:
            if template.name not in visited and has_cycle(template.name):
                raise ValueError(
                    f"Circular dependency detected involving template '{template.name}'"
                )

    def get_templates_by_category(
        self, category: TemplateCategory
    ) -> List[GranularTemplate]:
        """Get all templates in a specific category"""
        return [t for t in self.templates if t.category == category.value]

    def get_processing_order(self) -> List[GranularTemplate]:
        """Get templates in dependency-resolved processing order"""
        # Topological sort considering dependencies
        result = []
        visited = set()
        temp_visited = set()

        def visit(template: GranularTemplate):
            if template.name in temp_visited:
                raise ValueError(
                    f"Circular dependency detected at template '{template.name}'"
                )
            if template.name in visited:
                return

            temp_visited.add(template.name)

            # Visit dependencies first
            if template.name in self.dependencies:
                dep_name = self.dependencies[template.name]
                dep_template = next(
                    (t for t in self.templates if t.name == dep_name), None
                )
                if dep_template:
                    visit(dep_template)

            temp_visited.remove(template.name)
            visited.add(template.name)
            result.append(template)

        # Visit all templates
        for template in self.templates:
            if template.name not in visited:
                visit(template)

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "ai_assistant": self.ai_assistant,
            "templates": [t.to_dict() for t in self.templates],
            "output_structure": {k: v.copy() for k, v in self.output_structure.items()},
            "dependencies": self.dependencies.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplatePackage":
        """Create instance from dictionary"""
        templates = [
            GranularTemplate.from_dict(t_data) for t_data in data.get("templates", [])
        ]

        return cls(
            ai_assistant=data["ai_assistant"],
            templates=templates,
            output_structure=data.get("output_structure", {}),
            dependencies=data.get("dependencies", {}),
        )

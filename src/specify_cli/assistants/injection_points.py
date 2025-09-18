"""
Centralized injection point definitions with no duplication.

This module defines all injection points as class attributes with embedded metadata,
eliminating the need for separate enums, description dicts, and categorization sets
while preserving the familiar InjectionPoint.SOMETHING syntax.
"""

from typing import Dict, List, Set


class InjectionPointMeta:
    """
    Metadata container for an injection point.

    Contains all information about an injection point in one place,
    providing IDE-friendly access to names, descriptions, and requirements.
    """

    def __init__(self, name: str, description: str, required: bool = False):
        """
        Initialize injection point metadata.

        Args:
            name: Template variable name (e.g., "assistant_command_prefix")
            description: Description for IDE help and documentation
            required: Whether this injection point is required
        """
        if not name.startswith("assistant_"):
            raise ValueError(
                f"Injection point name must start with 'assistant_': {name}"
            )

        self.name = name
        self.description = description
        self.required = required

    @property
    def value(self) -> str:
        """Get the injection point name (for enum-like compatibility)."""
        return self.name

    def __str__(self) -> str:
        """Return the injection point name for template usage."""
        return self.name

    def __repr__(self) -> str:
        """Return a detailed representation."""
        return f"<InjectionPoint: {self.name} ({'required' if self.required else 'optional'})>"

    def startswith(self, prefix: str) -> bool:
        """Check if the injection point name starts with the given prefix."""
        return self.name.startswith(prefix)

    def endswith(self, suffix: str) -> bool:
        """Check if the injection point name ends with the given suffix."""
        return self.name.endswith(suffix)

    def __contains__(self, item: str) -> bool:
        """Check if the injection point name contains the given substring."""
        return item in self.name


class InjectionPointRegistry:
    """
    Registry that provides InjectionPoint.SOMETHING syntax with consolidated metadata.

    All injection points are defined here with their metadata in one place,
    eliminating duplication across multiple constants and dictionaries.
    """

    # Required injection points
    COMMAND_PREFIX = InjectionPointMeta(
        name="assistant_command_prefix",
        description="Command prefix for the AI assistant (e.g., 'claude ', 'cursor '). Used in CLI command examples and documentation.",
        required=True,
    )

    SETUP_INSTRUCTIONS = InjectionPointMeta(
        name="assistant_setup_instructions",
        description="Step-by-step setup instructions for getting the AI assistant ready for use in the project.",
        required=True,
    )

    CONTEXT_FILE_PATH = InjectionPointMeta(
        name="assistant_context_file_path",
        description="Path to the main context file where the AI assistant stores project-specific configuration and instructions.",
        required=True,
    )

    # Optional injection points
    CONTEXT_FILE_DESCRIPTION = InjectionPointMeta(
        name="assistant_context_file_description",
        description="Brief description of the context file format and purpose for the AI assistant.",
        required=False,
    )

    MEMORY_CONFIGURATION = InjectionPointMeta(
        name="assistant_memory_configuration",
        description="Description of how the AI assistant manages project memory, context, and persistent information.",
        required=False,
    )

    REVIEW_COMMAND = InjectionPointMeta(
        name="assistant_review_command",
        description="Specific command used to trigger code review functionality with the AI assistant.",
        required=False,
    )

    DOCUMENTATION_URL = InjectionPointMeta(
        name="assistant_documentation_url",
        description="Official documentation URL for the AI assistant, providing comprehensive usage guides and API references.",
        required=False,
    )

    WORKFLOW_INTEGRATION = InjectionPointMeta(
        name="assistant_workflow_integration",
        description="Description of how the AI assistant integrates with development workflows, CI/CD, and automation tools.",
        required=False,
    )

    CUSTOM_COMMANDS = InjectionPointMeta(
        name="assistant_custom_commands",
        description="List of custom or specialized commands available with this AI assistant beyond basic functionality.",
        required=False,
    )

    CONTEXT_FRONTMATTER = InjectionPointMeta(
        name="assistant_context_frontmatter",
        description="YAML frontmatter or metadata block that should be included at the top of the assistant's context files.",
        required=False,
    )

    IMPORT_SYNTAX = InjectionPointMeta(
        name="assistant_import_syntax",
        description="Syntax used by the AI assistant to import or reference external files within its context system.",
        required=False,
    )

    BEST_PRACTICES = InjectionPointMeta(
        name="assistant_best_practices",
        description="Recommended best practices and usage patterns for getting optimal results from the AI assistant.",
        required=False,
    )

    TROUBLESHOOTING = InjectionPointMeta(
        name="assistant_troubleshooting",
        description="Common troubleshooting steps and solutions for issues that may arise when using the AI assistant.",
        required=False,
    )

    LIMITATIONS = InjectionPointMeta(
        name="assistant_limitations",
        description="Known limitations, constraints, or considerations when using the AI assistant in development workflows.",
        required=False,
    )

    FILE_EXTENSIONS = InjectionPointMeta(
        name="assistant_file_extensions",
        description="File extensions and formats that the AI assistant works best with or has specialized support for.",
        required=False,
    )

    @classmethod
    def get_all_injection_points(cls) -> List[InjectionPointMeta]:
        """Get all injection point metadata objects."""
        return [
            getattr(cls, attr)
            for attr in dir(cls)
            if isinstance(getattr(cls, attr), InjectionPointMeta)
        ]

    @classmethod
    def get_required_injection_points(cls) -> List[InjectionPointMeta]:
        """Get all required injection point metadata objects."""
        return [point for point in cls.get_all_injection_points() if point.required]

    @classmethod
    def get_optional_injection_points(cls) -> List[InjectionPointMeta]:
        """Get all optional injection point metadata objects."""
        return [point for point in cls.get_all_injection_points() if not point.required]

    @classmethod
    def get_injection_point_names(cls) -> Set[str]:
        """Get all injection point names."""
        return {point.name for point in cls.get_all_injection_points()}

    @classmethod
    def get_required_injection_point_names(cls) -> Set[str]:
        """Get required injection point names."""
        return {
            point.name for point in cls.get_all_injection_points() if point.required
        }

    @classmethod
    def get_optional_injection_point_names(cls) -> Set[str]:
        """Get optional injection point names."""
        return {
            point.name for point in cls.get_all_injection_points() if not point.required
        }

    @classmethod
    def get_injection_point_descriptions(cls) -> Dict[str, str]:
        """Get mapping of injection point names to descriptions."""
        return {
            point.name: point.description for point in cls.get_all_injection_points()
        }

    @classmethod
    def find_injection_point_by_name(cls, name: str) -> InjectionPointMeta | None:
        """Find injection point metadata by name."""
        for point in cls.get_all_injection_points():
            if point.name == name:
                return point
        return None

    @classmethod
    def __iter__(cls):
        """Make the class iterable like an enum."""
        return iter(cls.get_all_injection_points())

    @classmethod
    def __contains__(cls, item):
        """Check if an injection point is in the registry."""
        if isinstance(item, InjectionPointMeta):
            return item in cls.get_all_injection_points()
        return False

    @classmethod
    def get_members(cls):
        """Provide enum-like __members__ interface."""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if isinstance(getattr(cls, attr), InjectionPointMeta)
        }


# Create the InjectionPoint interface that provides the familiar syntax
class InjectionPointType(InjectionPointRegistry):
    """Wrapper to make InjectionPointRegistry work like an enum."""

    def __iter__(self):
        """Make instance iterable."""
        return iter(self.get_all_injection_points())

    def __contains__(self, item):
        """Make instance support 'in' operator."""
        if isinstance(item, InjectionPointMeta):
            return item in self.get_all_injection_points()
        return False

    def __getattr__(self, name):
        """Delegate attribute access to class attributes."""
        if hasattr(InjectionPointRegistry, name):
            return getattr(InjectionPointRegistry, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


# Create singleton instance that acts like a class
InjectionPoint = InjectionPointType()

# Note: __members__ attribute is available via the get_members() method instead of direct assignment

# Type alias for isinstance checks
InjectionPointInstance = InjectionPointMeta


# Computed properties (no duplication!) - for backward compatibility
def get_all_injection_points() -> List[InjectionPointMeta]:
    """Get all injection point metadata objects."""
    return InjectionPoint.get_all_injection_points()


def get_required_injection_points() -> List[InjectionPointMeta]:
    """Get all required injection point metadata objects."""
    return InjectionPoint.get_required_injection_points()


def get_optional_injection_points() -> List[InjectionPointMeta]:
    """Get all optional injection point metadata objects."""
    return InjectionPoint.get_optional_injection_points()


def get_injection_point_names() -> Set[str]:
    """Get all injection point names."""
    return InjectionPoint.get_injection_point_names()


def get_required_injection_point_names() -> Set[str]:
    """Get required injection point names."""
    return InjectionPoint.get_required_injection_point_names()


def get_optional_injection_point_names() -> Set[str]:
    """Get optional injection point names."""
    return InjectionPoint.get_optional_injection_point_names()


def get_injection_point_descriptions() -> Dict[str, str]:
    """Get mapping of injection point names to descriptions."""
    return InjectionPoint.get_injection_point_descriptions()


# Type aliases for better type safety and readability
InjectionValues = Dict[InjectionPointMeta, str]

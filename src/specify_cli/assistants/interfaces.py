"""
Abstract Base Class interfaces for AI assistant system components.

This module provides comprehensive ABC-based interfaces that define clear contracts
for all AI assistant implementations, replacing loose Protocol approach with
explicit abstract methods and built-in validation support.

Benefits of ABC Approach:
    - **Explicit Contracts**: Each assistant must implement all abstract methods
    - **IDE Support**: Better autocomplete and error detection
    - **Runtime Checks**: Python enforces implementation of abstract methods
    - **Clear Documentation**: Abstract methods document the interface
    - **Type Safety**: pyrefly can validate implementations
    - **Extensibility**: Easy to add new abstract methods
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .types import (
    AssistantConfig,
    AssistantName,
    InjectionValues,
)


class ValidationResult(BaseModel):
    """
    Pydantic model for validation results with comprehensive status tracking.

    Provides structured validation feedback with errors, warnings, and
    overall status tracking for assistant setup and configuration.
    """

    is_valid: bool = Field(..., description="Overall validation status")
    errors: List[str] = Field(
        default_factory=list, description="Blocking errors that prevent assistant usage"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-blocking warnings for potential issues"
    )

    @property
    def has_errors(self) -> bool:
        """Check if validation found any blocking errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation found any non-blocking warnings."""
        return len(self.warnings) > 0

    def add_error(self, error: str) -> "ValidationResult":
        """Add a blocking error and mark validation as invalid."""
        new_errors = self.errors + [error]
        return self.model_copy(update={"errors": new_errors, "is_valid": False})

    def add_warning(self, warning: str) -> "ValidationResult":
        """Add a non-blocking warning (doesn't affect validity)."""
        new_warnings = self.warnings + [warning]
        return self.model_copy(update={"warnings": new_warnings})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["API key not configured - some features may not work"],
            }
        }
    )


class AssistantProvider(ABC):
    """
    Abstract base class that all AI assistants must implement.

    This interface defines the core contract that every assistant provider
    must fulfill, including configuration, template injection, validation,
    and setup instructions.

    Each assistant implementation must inherit from this class and implement
    all abstract methods to provide a consistent interface for the registry
    and template system.
    """

    @property
    @abstractmethod
    def config(self) -> AssistantConfig:
        """
        Return the immutable configuration for this assistant.

        Returns:
            AssistantConfig: Type-safe configuration with all required paths
            and settings for this assistant implementation.

        Example:
            AssistantConfig(
                name="claude",
                display_name="Claude Code",
                description="Anthropic's AI assistant with code capabilities",
                base_directory=".claude",
                context_file=".claude/CLAUDE.md",
                commands_directory=".claude/commands",
                memory_directory=".claude/memory"
            )
        """
        pass

    @abstractmethod
    def get_injection_values(self) -> InjectionValues:
        """
        Return injection point values for template rendering.

        Must provide all required injection points and may optionally provide
        enhanced injection points for additional functionality.

        Returns:
            InjectionValues: Dict mapping injection point names to string values.
            All values must be safe for Jinja2 template rendering.

        Required injection points:
            - assistant_command_prefix: CLI command prefix
            - assistant_setup_instructions: Human-readable setup steps
            - assistant_context_file_path: Path to main context file

        Optional injection points:
            - assistant_memory_configuration: Memory/constitution content
            - assistant_review_command: Code review command
            - assistant_documentation_url: Official documentation URL
            - assistant_workflow_integration: CI/CD integration details
            - assistant_custom_commands: Assistant-specific commands

        Example:
            {
                InjectionPoint.COMMAND_PREFIX: "claude ",
                InjectionPoint.SETUP_INSTRUCTIONS: "Run 'claude auth' to authenticate",
                InjectionPoint.CONTEXT_FILE_PATH: ".claude/CLAUDE.md",
                InjectionPoint.REVIEW_COMMAND: "claude review --comprehensive"
            }
        """
        pass

    @abstractmethod
    def validate_setup(self) -> ValidationResult:
        """
        Validate that the assistant is properly set up and configured.

        Performs comprehensive validation of:
        - Required dependencies and tools
        - Configuration files and paths
        - Authentication and API access
        - Template injection point completeness

        Returns:
            ValidationResult: Structured validation results with errors/warnings.

        Validation should check:
        - CLI tool availability (if required)
        - Authentication status
        - Configuration file existence
        - Required injection points presence
        - Path accessibility and permissions

        Example:
            ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["API key not configured - some features may not work"]
            )
        """
        pass

    @abstractmethod
    def get_setup_instructions(self) -> List[str]:
        """
        Return step-by-step setup instructions for this assistant.

        Provides human-readable instructions that guide users through
        the complete setup process from installation to configuration.

        Returns:
            List[str]: Ordered list of setup steps with clear instructions.
            Each step should be actionable and specific.

        Instructions should cover:
        - Tool installation (if required)
        - Authentication/API key setup
        - Initial configuration
        - Verification steps

        Example:
            [
                "Install Claude Code CLI: pip install claude-cli",
                "Authenticate with Anthropic: claude auth",
                "Verify setup: claude --version",
                "Test functionality: claude help"
            ]
        """
        pass

    @property
    @abstractmethod
    def imports_supported(self) -> bool:
        """
        Check if this assistant supports file imports in templates.

        Returns:
            bool: True if the assistant supports @file.md style imports, False otherwise.

        Example:
            if provider.imports_supported:
                import_syntax = provider.format_import(Path.cwd(), Path("docs/guide.md"))
        """
        pass

    @abstractmethod
    def format_import(self, current_dir: Path, target_file: Path) -> str:
        """
        Format a file import statement for this assistant.

        Args:
            current_dir: Current working directory (where the template is being processed)
            target_file: Absolute path to the file being imported

        Returns:
            str: Formatted import statement for this assistant's syntax.
            Should return empty string if imports are not supported.

        Examples:
            Claude: "@file.md" or "@/absolute/path/file.md"
            Cursor: "@file:./relative/path/file.md"
            Copilot: "<!-- @import file.md -->"

        Note:
            Each assistant decides whether to use relative or absolute paths
            based on their import syntax requirements and preferences.
        """
        pass


class AssistantFactory(ABC):
    """
    Abstract factory for creating and managing assistant instances.

    Provides a factory pattern interface for creating assistant providers,
    checking availability, and managing the lifecycle of assistant instances.
    This enables dependency injection and testability.
    """

    @abstractmethod
    def create_assistant(self, name: AssistantName) -> Optional[AssistantProvider]:
        """
        Create an assistant provider instance by name.

        Args:
            name: Unique identifier for the assistant (e.g., "claude", "gemini")

        Returns:
            AssistantProvider instance if available, None if not found or unavailable.

        The factory should:
        - Validate the assistant name
        - Check if the assistant is available
        - Create and return a properly configured instance
        - Return None for unknown or unavailable assistants

        Example:
            assistant = factory.create_assistant("claude")
            if assistant:
                config = assistant.config
                injections = assistant.get_injection_values()
        """
        pass

    @abstractmethod
    def get_available_assistants(self) -> List[AssistantName]:
        """
        Return list of all available assistant names.

        Returns:
            List[AssistantName]: Names of all assistants that can be created
            by this factory, whether currently configured or not.

        Example:
            ["claude", "gemini", "copilot", "cursor"]
        """
        pass

    @abstractmethod
    def is_assistant_available(self, name: AssistantName) -> bool:
        """
        Check if a specific assistant is available for creation.

        Args:
            name: Assistant name to check

        Returns:
            bool: True if the assistant can be created, False otherwise.

        This should be a fast check that doesn't create the assistant instance.

        Example:
            if factory.is_assistant_available("claude"):
                assistant = factory.create_assistant("claude")
        """
        pass


class AssistantRegistry(ABC):
    """
    Abstract registry for managing assistant provider instances.

    Provides a centralized registry pattern for managing active assistant
    instances, validation, and lifecycle management. Separates instance
    management from creation concerns.
    """

    @abstractmethod
    def register_assistant(self, assistant: AssistantProvider) -> None:
        """
        Register an assistant provider instance in the registry.

        Args:
            assistant: Fully configured AssistantProvider instance

        The registry should:
        - Validate the assistant configuration
        - Store the instance for future retrieval
        - Handle name conflicts appropriately
        - Maintain type safety

        Raises:
            ValueError: If assistant configuration is invalid
            TypeError: If assistant doesn't implement AssistantProvider

        Example:
            assistant = ClaudeAssistant()
            registry.register_assistant(assistant)
        """
        pass

    @abstractmethod
    def get_assistant(self, name: AssistantName) -> Optional[AssistantProvider]:
        """
        Retrieve a registered assistant by name.

        Args:
            name: Unique identifier for the assistant

        Returns:
            AssistantProvider instance if registered, None otherwise.

        Example:
            assistant = registry.get_assistant("claude")
            if assistant:
                injections = assistant.get_injection_values()
        """
        pass

    @abstractmethod
    def get_all_assistants(self) -> List[AssistantProvider]:
        """
        Get all currently registered assistant instances.

        Returns:
            List[AssistantProvider]: All registered assistant instances.

        Useful for:
        - Bulk operations across all assistants
        - Validation of all registered assistants
        - Registry inspection and debugging

        Example:
            for assistant in registry.get_all_assistants():
                result = assistant.validate_setup()
                if not result.is_valid:
                    print(f"Issues with {assistant.config.name}")
        """
        pass

    @abstractmethod
    def validate_all(self) -> Dict[AssistantName, ValidationResult]:
        """
        Validate all registered assistants and return comprehensive results.

        Returns:
            Dict mapping assistant names to their validation results.
            This enables bulk validation and reporting across all assistants.

        Example:
            results = registry.validate_all()
            for name, result in results.items():
                if not result.is_valid:
                    print(f"{name} has errors: {result.errors}")
                if result.has_warnings:
                    print(f"{name} has warnings: {result.warnings}")
        """
        pass

    @abstractmethod
    def unregister_assistant(self, name: AssistantName) -> bool:
        """
        Remove an assistant from the registry.

        Args:
            name: Name of assistant to remove

        Returns:
            bool: True if assistant was found and removed, False otherwise.

        Example:
            if registry.unregister_assistant("claude"):
                print("Claude assistant removed from registry")
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all assistants from the registry.

        Useful for:
        - Testing cleanup
        - Registry reset operations
        - Memory management in long-running processes
        """
        pass


# Backward compatibility aliases
InjectionProvider = AssistantProvider
InjectionPoints = InjectionValues

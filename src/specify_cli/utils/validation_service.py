"""
Validation Service - centralized validation logic and patterns.

This service handles:
- Common validation patterns and rules
- Input validation for various data types
- Template and configuration validation
- Error message generation
- Validation result aggregation
"""

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from specify_cli.core.constants import CONSTANTS

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation operation."""

    def __init__(
        self,
        is_valid: bool = True,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        """Initialize validation result.

        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        """Add an error to the result.

        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning to the result.

        Args:
            warning: Warning message to add
        """
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one.

        Args:
            other: ValidationResult to merge
        """
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ValidationService:
    """Centralized service for validation operations."""

    @staticmethod
    def validate_project_name(project_name: str) -> ValidationResult:
        """Validate a project name.

        Args:
            project_name: Project name to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        if not project_name:
            result.add_error("Project name cannot be empty")
            return result

        if len(project_name) > CONSTANTS.VALIDATION.MAX_PROJECT_NAME_LENGTH:
            result.add_error(
                f"Project name cannot exceed {CONSTANTS.VALIDATION.MAX_PROJECT_NAME_LENGTH} characters"
            )

        # Check for invalid characters
        if not re.match(r"^[a-zA-Z0-9_-]+$", project_name):
            result.add_error(
                "Project name can only contain letters, numbers, hyphens, and underscores"
            )

        # Check if starts with letter or number
        if not re.match(r"^[a-zA-Z0-9]", project_name):
            result.add_error("Project name must start with a letter or number")

        return result

    @staticmethod
    def validate_template_name(template_name: str) -> ValidationResult:
        """Validate a template name.

        Args:
            template_name: Template name to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        if not template_name:
            result.add_error("Template name cannot be empty")
            return result

        if len(template_name) > CONSTANTS.VALIDATION.MAX_TEMPLATE_NAME_LENGTH:
            result.add_error(
                f"Template name cannot exceed {CONSTANTS.VALIDATION.MAX_TEMPLATE_NAME_LENGTH} characters"
            )

        # Allow template extensions
        allowed_extensions = [
            CONSTANTS.FILE.TEMPLATE_J2_EXTENSION,
            CONSTANTS.FILE.MARKDOWN_EXTENSION,
            CONSTANTS.FILE.PYTHON_EXTENSION,
        ]
        has_allowed_extension = any(
            template_name.endswith(ext) for ext in allowed_extensions
        )

        if not has_allowed_extension and not re.match(
            r"^[a-zA-Z0-9_-]+$", template_name
        ):
            # Validate as identifier if no extension
            result.add_error(
                "Template name can only contain letters, numbers, hyphens, and underscores"
            )

        return result

    @staticmethod
    def validate_ai_assistant_name(ai_assistant: str) -> ValidationResult:
        """Validate an AI assistant name.

        Args:
            ai_assistant: AI assistant name to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        if not ai_assistant:
            result.add_error("AI assistant name cannot be empty")
            return result

        # Known AI assistants
        known_assistants = ["claude", "copilot", "cursor", "gemini"]

        if ai_assistant.lower() not in known_assistants:
            result.add_warning(
                f"Unknown AI assistant '{ai_assistant}'. Known assistants: {', '.join(known_assistants)}"
            )

        # Validate format
        if not re.match(r"^[a-z][a-z0-9]*$", ai_assistant.lower()):
            result.add_error(
                "AI assistant name must be lowercase letters and numbers only"
            )

        return result

    @staticmethod
    def validate_agent_name(agent_name: str) -> ValidationResult:
        """Validate an agent name.

        Args:
            agent_name: Agent name to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        if not agent_name:
            result.add_error("Agent name cannot be empty")
            return result

        # Agent names should use kebab-case
        if not re.match(CONSTANTS.PATTERNS.AGENT_NAME_PATTERN, agent_name):
            result.add_error(
                "Agent name must be in kebab-case (lowercase letters, numbers, and hyphens)"
            )

        # Check length
        if len(agent_name) < 2:
            result.add_error("Agent name must be at least 2 characters long")

        if len(agent_name) > 50:
            result.add_error("Agent name cannot exceed 50 characters")

        return result

    @staticmethod
    def validate_file_path(
        file_path: Union[str, Path],
        must_exist: bool = False,
        must_be_file: bool = False,
    ) -> ValidationResult:
        """Validate a file path.

        Args:
            file_path: File path to validate
            must_exist: Whether file must exist
            must_be_file: Whether path must be a file (not directory)

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()
        path = Path(file_path)

        if must_exist and not path.exists():
            result.add_error(f"File does not exist: {file_path}")
            return result

        if path.exists() and must_be_file and not path.is_file():
            result.add_error(f"Path is not a file: {file_path}")

        # Check for dangerous path patterns
        if ".." in str(path):
            result.add_warning("Path contains '..' which may be unsafe")

        return result

    @staticmethod
    def validate_directory_path(
        directory_path: Union[str, Path], must_exist: bool = False
    ) -> ValidationResult:
        """Validate a directory path.

        Args:
            directory_path: Directory path to validate
            must_exist: Whether directory must exist

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()
        path = Path(directory_path)

        if must_exist and not path.exists():
            result.add_error(f"Directory does not exist: {directory_path}")
            return result

        if path.exists() and not path.is_dir():
            result.add_error(f"Path is not a directory: {directory_path}")

        return result

    @staticmethod
    def validate_template_category(category: str) -> ValidationResult:
        """Validate a template category.

        Args:
            category: Category to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        if not category:
            result.add_error("Template category cannot be empty")
            return result

        if category not in CONSTANTS.PATTERNS.TEMPLATE_CATEGORIES:
            result.add_warning(
                f"Unknown template category '{category}'. Known categories: {', '.join(CONSTANTS.PATTERNS.TEMPLATE_CATEGORIES)}"
            )

        return result

    @staticmethod
    def validate_template_variables(
        template_content: str, required_variables: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate template variables.

        Args:
            template_content: Template content to analyze
            required_variables: List of variables that must be present

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        # Extract variables from template
        variables = re.findall(r"\{\{\s*(\w+)", template_content)
        found_variables = set(variables)

        if required_variables:
            missing_variables = set(required_variables) - found_variables
            for var in missing_variables:
                result.add_error(
                    f"Required template variable '{var}' not found in template"
                )

        # Check for potentially undefined variables
        # This is basic - real implementation would use Jinja2 AST parsing
        potentially_undefined = []
        for var in found_variables:
            # Common variables that might be undefined
            if var not in [
                "project_name",
                "ai_assistant",
                "created_date",
                "platform_system",
            ]:
                potentially_undefined.append(var)

        if potentially_undefined:
            result.add_warning(
                f"Template uses variables that might be undefined: {', '.join(potentially_undefined)}"
            )

        return result

    @staticmethod
    def validate_configuration_data(
        config_data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate configuration data.

        Args:
            config_data: Configuration data to validate
            schema: Optional schema to validate against

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        if not isinstance(config_data, dict):
            result.add_error("Configuration data must be a dictionary")
            return result

        # Basic validation without schema
        if not schema:
            # Check for common required fields
            if "ai_assistant" in config_data:
                ai_result = ValidationService.validate_ai_assistant_name(
                    config_data["ai_assistant"]
                )
                result.merge(ai_result)

            if "project_name" in config_data:
                project_result = ValidationService.validate_project_name(
                    config_data["project_name"]
                )
                result.merge(project_result)

        # TODO: Implement schema validation if provided

        return result

    @staticmethod
    def validate_injection_point_value(value: str) -> ValidationResult:
        """Validate an injection point value.

        Args:
            value: Value to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        if len(value) > CONSTANTS.VALIDATION.MAX_INJECTION_VALUE_LENGTH:
            result.add_error(
                f"Injection point value cannot exceed {CONSTANTS.VALIDATION.MAX_INJECTION_VALUE_LENGTH} characters"
            )

        # Check for potentially dangerous content
        dangerous_patterns = ["<script", "javascript:", "eval(", "exec("]
        for pattern in dangerous_patterns:
            if pattern.lower() in value.lower():
                result.add_warning(
                    f"Injection point value contains potentially dangerous content: {pattern}"
                )

        return result

    @staticmethod
    def validate_multiple_items(
        items: List[Tuple[str, Any]], validator_func: Callable, item_type: str = "item"
    ) -> ValidationResult:
        """Validate multiple items using a validator function.

        Args:
            items: List of (name, value) tuples to validate
            validator_func: Function to validate each item
            item_type: Type of items being validated (for error messages)

        Returns:
            Aggregated ValidationResult
        """
        result = ValidationResult()

        for name, value in items:
            try:
                item_result = validator_func(value)
                if not item_result.is_valid:
                    for error in item_result.errors:
                        result.add_error(f"{item_type} '{name}': {error}")
                for warning in item_result.warnings:
                    result.add_warning(f"{item_type} '{name}': {warning}")
            except Exception as e:
                result.add_error(f"{item_type} '{name}': Validation failed - {str(e)}")

        return result

    @staticmethod
    def create_validation_summary(results: List[ValidationResult]) -> str:
        """Create a summary of multiple validation results.

        Args:
            results: List of validation results to summarize

        Returns:
            Summary string
        """
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        valid_count = sum(1 for r in results if r.is_valid)

        summary = f"Validation Summary: {valid_count}/{len(results)} items valid"

        if total_errors > 0:
            summary += f", {total_errors} errors"

        if total_warnings > 0:
            summary += f", {total_warnings} warnings"

        return summary

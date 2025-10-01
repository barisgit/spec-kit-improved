"""Security utilities for template rendering and input validation."""

import re
from pathlib import Path
from typing import Any, Dict, Set


class TemplateSecurityError(Exception):
    """Exception raised for template security violations."""

    pass


class TemplateSanitizer:
    """Handles sanitization of template inputs to prevent injection attacks."""

    # Patterns that could be used for template injection attacks
    DANGEROUS_PATTERNS: Set[str] = {
        "{{",
        "{%",
        "%}",
        "}}",  # Jinja2 delimiters
        "<script",
        "</script>",  # Script tags
        "javascript:",
        "data:",  # Dangerous URLs
        "__import__",
        "eval",
        "exec",  # Python execution
        "os.system",
        "subprocess",  # System commands
        "open(",
        "file(",  # File operations
    }

    # Safe common template values that shouldn't be rejected
    SAFE_COMMON_VALUES: Set[str] = {
        "world",
        "hello",
        "test",
        "example",
        "demo",
        "sample",
        "claude",
        "gemini",
        "copilot",
        "cursor",
        "assistant",
        "project",
        "feature",
        "spec",
        "plan",
        "task",
        "implementation",
    }

    # Maximum length for injection values
    MAX_INJECTION_VALUE_LENGTH = 10000
    MAX_TEMPLATE_SIZE = 1_000_000  # 1MB
    MAX_VARIABLES = 1000
    MAX_LOOPS = 100
    MAX_INCLUDES = 50

    @classmethod
    def sanitize_injection_value(cls, value: Any) -> str:
        """Sanitize injection point values to prevent template injection.

        Args:
            value: The injection value to sanitize

        Returns:
            Sanitized value safe for template rendering

        Raises:
            TemplateSecurityError: If value contains dangerous patterns
        """
        if not isinstance(value, str):
            # Convert to string
            value = str(value)

        # Check length limits
        if len(value) > cls.MAX_INJECTION_VALUE_LENGTH:
            raise TemplateSecurityError(
                f"Injection value too long: {len(value)} > {cls.MAX_INJECTION_VALUE_LENGTH}"
            )

        # Check for dangerous patterns (but allow safe common values)
        value_lower = value.lower().strip()

        # Allow safe common template values
        if value_lower in cls.SAFE_COMMON_VALUES:
            return value

        # Check for dangerous patterns in non-safe values
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern in value_lower:
                raise TemplateSecurityError(
                    f"Dangerous pattern detected in injection value: {pattern}"
                )

        # Remove any remaining potential template delimiters
        sanitized = value
        for pattern in ["{%", "{{", "%}", "}}"]:
            sanitized = sanitized.replace(pattern, "")

        return sanitized

    @classmethod
    def sanitize_context_dict(cls, context_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize entire context dictionary for template rendering.

        Args:
            context_dict: Context dictionary to sanitize

        Returns:
            Sanitized context dictionary

        Raises:
            TemplateSecurityError: If context contains dangerous values
        """
        if len(context_dict) > cls.MAX_VARIABLES:
            raise TemplateSecurityError(
                f"Too many template variables: {len(context_dict)} > {cls.MAX_VARIABLES}"
            )

        sanitized = {}
        for key, value in context_dict.items():
            # Sanitize key names
            if not isinstance(key, str) or not re.match(
                r"^[a-zA-Z_][a-zA-Z0-9_]*$", key
            ):
                raise TemplateSecurityError(f"Invalid variable name: {key}")

            # Sanitize values based on type
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_injection_value(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, (list, tuple)):
                # Sanitize list elements
                sanitized[key] = [
                    cls.sanitize_injection_value(str(item))
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries (with depth limit)
                sanitized[key] = cls._sanitize_nested_dict(value, depth=1, max_depth=3)
            elif value is None:
                sanitized[key] = value
            else:
                # Convert other types to string and sanitize
                sanitized[key] = cls.sanitize_injection_value(str(value))

        return sanitized

    @classmethod
    def _sanitize_nested_dict(
        cls, nested_dict: Dict[str, Any], depth: int, max_depth: int
    ) -> Dict[str, Any]:
        """Sanitize nested dictionary with depth limit.

        Args:
            nested_dict: Dictionary to sanitize
            depth: Current nesting depth
            max_depth: Maximum allowed depth

        Returns:
            Sanitized nested dictionary
        """
        if depth > max_depth:
            raise TemplateSecurityError(
                f"Template context nesting too deep: {depth} > {max_depth}"
            )

        sanitized = {}
        for key, value in nested_dict.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_injection_value(value)
            elif isinstance(value, dict):
                sanitized[key] = cls._sanitize_nested_dict(value, depth + 1, max_depth)
            else:
                sanitized[key] = value

        return sanitized

    @classmethod
    def validate_template_complexity(cls, template_content: str) -> None:
        """Validate template complexity to prevent resource exhaustion.

        Args:
            template_content: Template content to validate

        Raises:
            TemplateSecurityError: If template is too complex
        """
        if len(template_content) > cls.MAX_TEMPLATE_SIZE:
            raise TemplateSecurityError(
                f"Template too large: {len(template_content)} > {cls.MAX_TEMPLATE_SIZE}"
            )

        # Count template constructs
        loop_count = len(re.findall(r"{%\s*for\s+", template_content))
        if loop_count > cls.MAX_LOOPS:
            raise TemplateSecurityError(
                f"Too many loops in template: {loop_count} > {cls.MAX_LOOPS}"
            )

        include_count = len(re.findall(r"{%\s*include\s+", template_content))
        if include_count > cls.MAX_INCLUDES:
            raise TemplateSecurityError(
                f"Too many includes in template: {include_count} > {cls.MAX_INCLUDES}"
            )


class PathValidator:
    """Validates file paths to prevent path traversal attacks."""

    @classmethod
    def validate_safe_path(cls, base_path: Path, target_path: Path) -> bool:
        """Ensure target path is within base directory.

        Args:
            base_path: Base directory that should contain the target
            target_path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        try:
            resolved_target = target_path.resolve()
            resolved_base = base_path.resolve()

            # Check if target is within base directory
            return str(resolved_target).startswith(str(resolved_base))
        except (OSError, ValueError):
            return False

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename

        Raises:
            TemplateSecurityError: If filename contains dangerous patterns
        """
        # Remove path separators and dangerous characters
        dangerous_chars = ["/", "\\", "..", "~", "$", "`", ";", "|", "&"]

        sanitized = filename
        for char in dangerous_chars:
            if char in sanitized:
                raise TemplateSecurityError(f"Dangerous character in filename: {char}")

        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip(" .")

        if not sanitized or len(sanitized) > 255:
            raise TemplateSecurityError(f"Invalid filename: {filename}")

        return sanitized


class TemplateSecurityValidator:
    """Comprehensive template security validation."""

    def __init__(self):
        self.sanitizer = TemplateSanitizer()
        self.path_validator = PathValidator()

    def validate_template_render(
        self,
        template_content: str,
        context_dict: Dict[str, Any],
        output_path: Path,
        base_path: Path,
    ) -> Dict[str, Any]:
        """Comprehensive validation before template rendering.

        Args:
            template_content: Template content to validate
            context_dict: Context dictionary to validate
            output_path: Target output path
            base_path: Base directory for path validation

        Returns:
            Sanitized context dictionary

        Raises:
            TemplateSecurityError: If validation fails
        """
        # Validate template complexity
        self.sanitizer.validate_template_complexity(template_content)

        # Validate output path
        if not self.path_validator.validate_safe_path(base_path, output_path):
            raise TemplateSecurityError(f"Unsafe output path: {output_path}")

        # Sanitize context
        return self.sanitizer.sanitize_context_dict(context_dict)

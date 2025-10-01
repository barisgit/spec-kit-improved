"""
Constants and utilities for AI assistant template injection system.

This module provides type-safe utilities for working with injection points
using the enum system from types.py, replacing hardcoded string constants
with proper enum-based validation and manipulation.
"""

import re
from typing import Dict, List, Optional, Set

from specify_cli.core.constants import CONSTANTS

from .injection_points import (
    InjectionPoint,
    InjectionPointMeta,
    get_all_injection_points,
    get_optional_injection_points,
    get_required_injection_points,
)
from .interfaces import ValidationResult

# Computed injection point sets for backward compatibility
REQUIRED_INJECTION_POINTS = set(get_required_injection_points())
OPTIONAL_INJECTION_POINTS = set(get_optional_injection_points())
ALL_INJECTION_POINTS = set(get_all_injection_points())
"""All valid injection points (both required and optional)."""

# Names for backward compatibility
InjectionPointNames = InjectionPoint


# Re-export from types for backward compatibility
__all__ = [
    "InjectionPoint",
    "REQUIRED_INJECTION_POINTS",
    "OPTIONAL_INJECTION_POINTS",
    "ALL_INJECTION_POINTS",
    "InjectionPointNames",
    "get_all_injection_points",
    "validate_injection_values",
    "get_injection_point_by_value",
    "validate_assistant_injections",
    "validate_injection_point_name",
]


def get_all_injection_points() -> Set[InjectionPointMeta]:
    """
    Get all available injection points.

    Returns:
        Set of all injection points (both required and optional)
    """
    return REQUIRED_INJECTION_POINTS | OPTIONAL_INJECTION_POINTS


def validate_injection_values(
    injection_values: Dict[InjectionPointMeta, str],
) -> List[str]:
    """
    Validate injection point values and return any errors.

    Args:
        injection_values: Dictionary mapping injection points to their values

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check required injection points
    missing_required = REQUIRED_INJECTION_POINTS - set(injection_values.keys())
    if missing_required:
        errors.append(
            f"Missing required injection points: {[p.name for p in missing_required]}"
        )

    # Check for empty values
    empty_values = [p.name for p, v in injection_values.items() if not v.strip()]
    if empty_values:
        errors.append(f"Empty injection point values: {empty_values}")

    # Check value lengths
    long_values = [
        p.name
        for p, v in injection_values.items()
        if len(v) > CONSTANTS.VALIDATION.MAX_INJECTION_VALUE_LENGTH
    ]
    if long_values:
        errors.append(
            f"Injection point values exceed maximum length ({CONSTANTS.VALIDATION.MAX_INJECTION_VALUE_LENGTH}): {long_values}"
        )

    return errors


def get_injection_point_by_value(value: str) -> Optional[InjectionPointMeta]:
    """
    Get injection point by its string value.

    Args:
        value: String value of the injection point

    Returns:
        InjectionPointMeta if found, None otherwise
    """
    return InjectionPoint.find_injection_point_by_name(value)


def validate_assistant_injections(
    assistant_name: str, injection_values: Dict[InjectionPointMeta, str]
) -> ValidationResult:
    """
    Validate that an assistant provides proper injection values.

    Args:
        assistant_name: Name of the assistant for error reporting
        injection_values: Dictionary mapping injection points to their values

    Returns:
        ValidationResult with validation status, errors, and warnings
    """
    errors = validate_injection_values(injection_values)
    warnings = []

    # Check if optional injection points are provided
    provided_optional = set(injection_values.keys()) & OPTIONAL_INJECTION_POINTS
    missing_optional = OPTIONAL_INJECTION_POINTS - provided_optional

    if missing_optional:
        warnings.append(
            f"Assistant '{assistant_name}' doesn't provide optional injection points: "
            f"{[p.name for p in missing_optional]}"
        )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_injection_point_name(name: str) -> bool:
    """
    Validate that an injection point name follows naming conventions.

    Args:
        name: Injection point name to validate

    Returns:
        True if name is valid, False otherwise

    Examples:
        >>> validate_injection_point_name("assistant_command_prefix")
        True
        >>> validate_injection_point_name("invalid_name")
        False
        >>> validate_injection_point_name("assistant_")
        False
    """
    return bool(re.match(CONSTANTS.ASSISTANT.INJECTION_POINT_NAME_PATTERN, name))

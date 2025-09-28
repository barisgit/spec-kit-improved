"""Test enum-based injection point validation according to spec task T026."""

from specify_cli.assistants.injection_points import (
    InjectionPoint,
    get_all_injection_points,
)
from specify_cli.assistants.types import InjectionValues


class TestInjectionPointEnumValidation:
    """Test enum-based injection point validation features."""

    def test_injection_point_enum_values_are_strings(self) -> None:
        """Test that all injection point values are strings."""
        for injection_point in get_all_injection_points():
            assert isinstance(injection_point.name, str)
            assert len(injection_point.name) > 0

    def test_injection_point_enum_names_match_values(self) -> None:
        """Test that registry attribute names follow consistent naming convention."""
        # Test a few key examples to ensure registry attributes match expected patterns
        assert InjectionPoint.COMMAND_PREFIX.name == "assistant_command_prefix"
        assert InjectionPoint.SETUP_INSTRUCTIONS.name == "assistant_setup_instructions"
        assert InjectionPoint.CONTEXT_FILE_PATH.name == "assistant_context_file_path"

        # All injection point names should start with assistant_
        for injection_point in get_all_injection_points():
            assert injection_point.name.startswith("assistant_")

    def test_injection_values_type_validation(self) -> None:
        """Test that InjectionValues type alias enforces string values."""
        # Valid injection values
        valid_values: InjectionValues = {
            InjectionPoint.COMMAND_PREFIX: "claude ",
            InjectionPoint.SETUP_INSTRUCTIONS: "Follow these steps...",
        }
        assert isinstance(valid_values, dict)

        # Check all keys are InjectionPointMeta objects
        from specify_cli.assistants.injection_points import InjectionPointMeta

        for key in valid_values:
            assert isinstance(key, InjectionPointMeta)

        # Check all values are strings
        for value in valid_values.values():
            assert isinstance(value, str)

    def test_injection_point_membership_validation(self) -> None:
        """Test membership checks for injection points."""
        # Test valid membership
        assert InjectionPoint.COMMAND_PREFIX in InjectionPoint
        assert InjectionPoint.SETUP_INSTRUCTIONS in InjectionPoint

        # Test string values can be found
        command_prefix_value = InjectionPoint.COMMAND_PREFIX.value
        assert any(ip.value == command_prefix_value for ip in InjectionPoint)

    def test_injection_point_comparison_operations(self) -> None:
        """Test comparison operations work correctly."""
        point1 = InjectionPoint.COMMAND_PREFIX
        point2 = InjectionPoint.COMMAND_PREFIX
        point3 = InjectionPoint.SETUP_INSTRUCTIONS

        # Test equality
        assert point1 == point2
        assert point1 != point3

        # Test string comparison
        assert point1.value == "assistant_command_prefix"
        assert (
            point1.value == "assistant_command_prefix"
        )  # Test via .value instead of str()

    def test_injection_point_enum_immutability(self) -> None:
        """Test that injection point enums cannot be modified."""
        # The value property is read-only, so attempts to set it should fail
        # This is a design feature to ensure injection points remain immutable
        try:
            InjectionPoint.COMMAND_PREFIX.value = "modified"  # type: ignore[misc]
            raise AssertionError("Should not be able to modify injection point value")
        except AttributeError:
            pass  # Expected behavior

    def test_injection_point_iteration_consistency(self) -> None:
        """Test that iteration over injection points is consistent."""
        points_list1 = list(InjectionPoint)
        points_list2 = list(InjectionPoint)

        assert points_list1 == points_list2
        assert len(points_list1) > 0

    def test_injection_values_dict_key_validation(self) -> None:
        """Test that injection values dictionaries use proper enum keys."""
        # This should work
        valid_dict: InjectionValues = {}
        valid_dict[InjectionPoint.COMMAND_PREFIX] = "claude "

        assert InjectionPoint.COMMAND_PREFIX in valid_dict
        assert valid_dict[InjectionPoint.COMMAND_PREFIX] == "claude "

    def test_injection_point_string_serialization(self) -> None:
        """Test string serialization and deserialization of injection points."""
        original_point = InjectionPoint.COMMAND_PREFIX
        string_value = str(original_point)

        # Find the same enum by string value
        found_point = None
        for point in InjectionPoint:
            if str(point) == string_value:
                found_point = point
                break

        assert found_point is not None
        assert found_point == original_point

    def test_injection_point_enum_completeness(self) -> None:
        """Test that all expected injection points are present."""
        required_points = {
            "assistant_command_prefix",
            "assistant_context_file_path",
            "assistant_setup_instructions",
        }

        available_points = {ip.value for ip in InjectionPoint}

        # All required points should be available
        assert required_points.issubset(available_points)

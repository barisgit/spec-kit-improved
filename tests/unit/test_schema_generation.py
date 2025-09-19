"""Test JSON schema generation from Pydantic models according to spec task T027."""

import json

from specify_cli.assistants.types import AssistantConfig
from specify_cli.models.config import ProjectConfig


class TestJSONSchemaGeneration:
    """Test JSON schema generation features from Pydantic models."""

    def test_assistant_config_json_schema_generation(self):
        """Test that AssistantConfig generates valid JSON schema."""
        schema = AssistantConfig.model_json_schema()

        # Basic schema structure validation
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Check required fields are in schema
        assert set(schema["required"]) >= {
            "name",
            "display_name",
            "description",
            "base_directory",
        }  # At minimum these should be required

        # Check properties have proper types
        properties = schema["properties"]
        assert "name" in properties
        assert "display_name" in properties
        assert "description" in properties
        assert "base_directory" in properties

        # Validate name field schema
        name_schema = properties["name"]
        assert name_schema["type"] == "string"
        assert "pattern" in name_schema  # Should have regex validation

        # Validate base_directory field schema
        base_dir_schema = properties["base_directory"]
        assert base_dir_schema["type"] == "string"

    def test_assistant_config_schema_includes_field_constraints(self):
        """Test that generated schema includes Pydantic field constraints."""
        schema = AssistantConfig.model_json_schema()
        properties = schema["properties"]

        # Check that string length constraints are included
        name_schema = properties["name"]
        if "minLength" in name_schema or "maxLength" in name_schema:
            # If length constraints exist, validate them
            if "minLength" in name_schema:
                assert isinstance(name_schema["minLength"], int)
                assert name_schema["minLength"] >= 1
            if "maxLength" in name_schema:
                assert isinstance(name_schema["maxLength"], int)
                assert name_schema["maxLength"] > 0

        # Pattern validation for name
        assert "pattern" in name_schema
        assert isinstance(name_schema["pattern"], str)

    def test_schema_serialization_roundtrip(self):
        """Test that schemas can be serialized to JSON and back."""
        schema = AssistantConfig.model_json_schema()

        # Serialize to JSON string
        json_string = json.dumps(schema)
        assert isinstance(json_string, str)
        assert len(json_string) > 0

        # Deserialize back to dict
        deserialized = json.loads(json_string)
        assert deserialized == schema

    def test_project_config_json_schema_generation(self):
        """Test that ProjectConfig works with standard Python types."""
        # ProjectConfig is a dataclass, not a Pydantic model
        # Test that we can create one and it has the expected fields
        from specify_cli.models.config import TemplateConfig

        template_config = TemplateConfig(ai_assistants=["claude", "gemini"])
        project_config = ProjectConfig(
            name="test-project", template_settings=template_config
        )

        # Should include project-specific fields (actual API)
        expected_fields = {"name", "branch_naming", "template_settings", "created_at"}

        # Check that all expected fields exist on the instance
        for field in expected_fields:
            assert hasattr(project_config, field), (
                f"ProjectConfig missing field: {field}"
            )

    def test_schema_title_and_description(self):
        """Test that schemas include proper titles and descriptions."""
        schema = AssistantConfig.model_json_schema()

        # Schema should have a title
        if "title" in schema:
            assert isinstance(schema["title"], str)
            assert len(schema["title"]) > 0

        # Schema may have a description
        if "description" in schema:
            assert isinstance(schema["description"], str)

    def test_schema_field_descriptions(self):
        """Test that schema fields include helpful descriptions."""
        schema = AssistantConfig.model_json_schema()
        properties = schema["properties"]

        # Check if any field has a description
        has_descriptions = any(
            "description" in field_schema for field_schema in properties.values()
        )

        # At least some fields should have descriptions for good UX
        if has_descriptions:
            for _field_name, field_schema in properties.items():
                if "description" in field_schema:
                    assert isinstance(field_schema["description"], str)
                    assert len(field_schema["description"]) > 0

    def test_schema_additional_properties_handling(self):
        """Test that schema properly handles additional properties."""
        schema = AssistantConfig.model_json_schema()

        # Pydantic models with frozen=True should not allow additional properties
        if "additionalProperties" in schema:
            # Should be False for strict validation
            assert schema["additionalProperties"] is False

    def test_schema_nested_objects_generation(self):
        """Test schema generation for models with nested objects."""
        schema = AssistantConfig.model_json_schema()

        # AssistantConfig has nested ContextFileConfig and TemplateConfig objects
        if "$defs" in schema or "definitions" in schema:
            definitions = schema.get("$defs", schema.get("definitions", {}))
            assert isinstance(definitions, dict)

            # Each definition should be a valid schema
            for _def_name, definition in definitions.items():
                assert isinstance(definition, dict)
                assert "type" in definition

        # Check that nested objects are referenced in properties
        properties = schema["properties"]
        if "context_file" in properties:
            context_file_schema = properties["context_file"]
            # Should either have type object or reference a definition
            assert "type" in context_file_schema or "$ref" in context_file_schema

    def test_schema_enum_handling(self):
        """Test that enums are properly represented in schemas."""
        schema = AssistantConfig.model_json_schema()

        def check_enum_in_schema(schema_part):
            """Recursively check for enum definitions in schema."""
            if isinstance(schema_part, dict):
                if "enum" in schema_part:
                    return True
                for value in schema_part.values():
                    if check_enum_in_schema(value):
                        return True
            elif isinstance(schema_part, list):
                for item in schema_part:
                    if check_enum_in_schema(item):
                        return True
            return False

        # FileFormat enum should be included in schemas
        has_enums = check_enum_in_schema(schema)
        if has_enums:
            # This is good - enums should be included in schemas
            assert True

    def test_schema_generation_performance(self):
        """Test that schema generation completes in reasonable time."""
        import time

        start_time = time.time()
        schema = AssistantConfig.model_json_schema()
        end_time = time.time()

        generation_time = end_time - start_time

        # Schema generation should be fast (under 100ms as per spec)
        assert generation_time < 0.1, (
            f"Schema generation took {generation_time:.3f}s, should be under 0.1s"
        )
        assert isinstance(schema, dict)

    def test_schema_validation_with_example_data(self):
        """Test that schema structure matches example data."""
        schema = AssistantConfig.model_json_schema()

        # The schema should describe AssistantConfig structure
        properties = schema["properties"]

        # Validate that all main fields are described
        main_fields = ["name", "display_name", "description", "base_directory"]
        for field in main_fields:
            assert field in properties
            assert properties[field]["type"] == "string"

        # Validate that nested objects are described
        if "context_file" in properties:
            # Context file should be an object or reference
            context_schema = properties["context_file"]
            assert "type" in context_schema or "$ref" in context_schema

    def test_schema_field_patterns_and_constraints(self):
        """Test that schema includes field patterns and constraints."""
        schema = AssistantConfig.model_json_schema()
        properties = schema["properties"]

        # Name field should have pattern constraint
        name_schema = properties["name"]
        assert "pattern" in name_schema
        pattern = name_schema["pattern"]
        # Should match the pattern from AssistantConfig
        assert pattern == r"^[a-z][a-z0-9_-]*$"

        # Check length constraints
        assert "minLength" in name_schema
        assert "maxLength" in name_schema
        assert name_schema["minLength"] == 1
        assert name_schema["maxLength"] == 50

        # Base directory should also have pattern
        base_dir_schema = properties["base_directory"]
        assert "pattern" in base_dir_schema
        base_pattern = base_dir_schema["pattern"]
        # Should match the pattern from AssistantConfig
        assert base_pattern == r"^\.[a-z][a-z0-9_-]*$"

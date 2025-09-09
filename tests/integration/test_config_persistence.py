"""
Integration test for configuration persistence functionality (TDD)

This test is designed to FAIL initially since the functionality isn't implemented yet.
Tests the complete persistence workflow for ProjectConfig with enhanced fields.
"""

import shutil
import tempfile
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest

# These imports will fail initially since the models/services aren't fully implemented
try:
    from specify_cli.models.config import (
        BranchNamingConfig,
        ProjectConfig,
        TemplateConfig,
    )
    from specify_cli.services.config_service import ConfigService, TomlConfigService

    # ConfigValidator doesn't exist yet - this will be implemented later
    class ConfigValidator:
        """Placeholder ConfigValidator for TDD - WILL FAIL until implemented"""

        def validate_branch_naming_config(self, config):
            raise NotImplementedError("ConfigValidator not implemented yet")

        def validate_template_config(self, config):
            raise NotImplementedError("ConfigValidator not implemented yet")

        def validate_project_config(self, config):
            raise NotImplementedError("ConfigValidator not implemented yet")

    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)

    # Create placeholder classes for the test structure
    class BranchNamingConfig:
        pass

    class ProjectConfig:
        pass

    class TemplateConfig:
        pass

    class ConfigService:
        pass

    class TomlConfigService:
        pass

    class ConfigValidator:
        pass


def dump_toml(data: Dict[str, Any], file_path: Path) -> None:
    """Helper function to write TOML data to file (basic implementation for testing)"""

    def _format_value(value: Any, indent: int = 0) -> str:
        """Format a value for TOML output"""
        if isinstance(value, dict):
            if not value:
                return "{}"
            lines = []
            for k, v in value.items():
                if isinstance(v, dict):
                    lines.append(f"[{k}]")
                    for sub_k, sub_v in v.items():
                        lines.append(f"{sub_k} = {_format_value(sub_v)}")
                else:
                    lines.append(f"{k} = {_format_value(v)}")
            return "\n".join(lines)
        elif isinstance(value, list):
            formatted_items = [_format_value(item) for item in value]
            return f"[{', '.join(formatted_items)}]"
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        else:
            return str(value)

    content = _format_value(data)
    file_path.write_text(content)


@pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason=f"Required modules not implemented: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}",
)
class TestConfigurationPersistence:
    """Integration tests for configuration persistence with enhanced data models"""

    @pytest.fixture
    def temp_project_dir(self) -> Path:
        """Create temporary project directory for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def config_service(self) -> ConfigService:
        """Create ConfigService instance (will fail initially)"""
        return TomlConfigService()

    @pytest.fixture
    def sample_enhanced_config(self) -> ProjectConfig:
        """Create sample ProjectConfig with all enhanced fields"""
        branch_naming = BranchNamingConfig(
            default_pattern="feature/{feature-name}",
            patterns=[
                "feature/{feature-name}",
                "fix/{feature-name}",
                "chore/{feature-name}",
                "hotfix/{bug-id}",
                "epic/{epic-name}-{component}",
            ],
            custom_types={
                "refactor": "refactor/{feature-name}",
                "docs": "docs/{section}",
                "test": "test/{test-category}",
            },
        )

        template_config = TemplateConfig(
            ai_assistant="claude",
            custom_templates_dir="./custom_templates",
            template_cache_enabled=True,
            template_variables={
                "default_author": "Test User",
                "organization": "TestOrg",
                "license": "MIT",
                "python_version": "3.11",
            },
        )

        return ProjectConfig(
            name="test-enhanced-project",
            branch_naming=branch_naming,
            template_settings=template_config,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )

    def test_enhanced_project_config_saves_to_toml(
        self,
        temp_project_dir: Path,
        config_service: ConfigService,
        sample_enhanced_config: ProjectConfig,
    ):
        """Test that ProjectConfig with enhanced fields persists to .specify/config.toml"""
        # This test will fail initially because:
        # 1. Enhanced data models aren't fully implemented
        # 2. TOML serialization methods don't exist
        # 3. ConfigService implementation is incomplete

        # Save configuration
        success = config_service.save_project_config(
            temp_project_dir, sample_enhanced_config
        )
        assert success, "Configuration should save successfully"

        # Verify config file exists
        config_file = temp_project_dir / ".specify" / "config.toml"
        assert config_file.exists(), "Configuration file should be created"

        # Verify TOML structure
        config_data = tomllib.loads(config_file.read_text())

        # Check project section
        assert "project" in config_data
        assert config_data["project"]["name"] == "test-enhanced-project"
        assert "created_at" in config_data["project"]

        # Check branch naming configuration
        assert "branch_naming" in config_data["project"]
        branch_config = config_data["project"]["branch_naming"]
        assert branch_config["default_pattern"] == "feature/{feature-name}"
        assert len(branch_config["patterns"]) == 5
        assert "epic/{epic-name}-{component}" in branch_config["patterns"]

        # Check custom types (enhanced field)
        assert "custom_types" in branch_config
        assert branch_config["custom_types"]["refactor"] == "refactor/{feature-name}"
        assert branch_config["custom_types"]["docs"] == "docs/{section}"

        # Check template configuration
        assert "template_settings" in config_data["project"]
        template_config = config_data["project"]["template_settings"]
        assert template_config["ai_assistant"] == "claude"
        assert template_config["custom_templates_dir"] == "./custom_templates"
        assert template_config["template_cache_enabled"] is True

        # Check template variables (enhanced field)
        assert "template_variables" in template_config
        variables = template_config["template_variables"]
        assert variables["default_author"] == "Test User"
        assert variables["organization"] == "TestOrg"

    def test_toml_serialization_deserialization_roundtrip(
        self,
        temp_project_dir: Path,
        config_service: ConfigService,
        sample_enhanced_config: ProjectConfig,
    ):
        """Test that configuration can be saved and loaded back correctly"""
        # This test will fail initially because serialization methods aren't implemented

        # Save configuration
        success = config_service.save_project_config(
            temp_project_dir, sample_enhanced_config
        )
        assert success

        # Load configuration back
        loaded_config = config_service.load_project_config(temp_project_dir)
        assert loaded_config is not None, "Configuration should be loadable"

        # Verify all fields match
        assert loaded_config.name == sample_enhanced_config.name
        assert loaded_config.created_at == sample_enhanced_config.created_at

        # Verify branch naming config
        assert (
            loaded_config.branch_naming.default_pattern
            == sample_enhanced_config.branch_naming.default_pattern
        )
        assert (
            loaded_config.branch_naming.patterns
            == sample_enhanced_config.branch_naming.patterns
        )
        assert (
            loaded_config.branch_naming.custom_types
            == sample_enhanced_config.branch_naming.custom_types
        )

        # Verify template config
        assert (
            loaded_config.template_settings.ai_assistant
            == sample_enhanced_config.template_settings.ai_assistant
        )
        assert (
            loaded_config.template_settings.custom_templates_dir
            == sample_enhanced_config.template_settings.custom_templates_dir
        )
        assert (
            loaded_config.template_settings.template_cache_enabled
            == sample_enhanced_config.template_settings.template_cache_enabled
        )
        assert (
            loaded_config.template_settings.template_variables
            == sample_enhanced_config.template_settings.template_variables
        )

    def test_default_values_applied_for_missing_fields(
        self, temp_project_dir: Path, config_service: ConfigService
    ):
        """Test that defaults are properly applied when config is missing or incomplete"""
        # This test will fail initially because default factory methods aren't implemented

        # Create minimal TOML file with missing enhanced fields
        config_dir = temp_project_dir / ".specify"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"

        # Write minimal config missing enhanced fields
        minimal_config = {"project": {"name": "minimal-project"}}
        dump_toml(minimal_config, config_file)

        # Load configuration
        loaded_config = config_service.load_project_config(temp_project_dir)
        assert loaded_config is not None

        # Verify defaults are applied
        assert loaded_config.name == "minimal-project"

        # Check branch naming defaults
        assert loaded_config.branch_naming.default_pattern == "feature/{feature-name}"
        assert "feature/{feature-name}" in loaded_config.branch_naming.patterns
        assert isinstance(loaded_config.branch_naming.custom_types, dict)

        # Check template defaults
        assert loaded_config.template_settings.ai_assistant == "claude"
        assert loaded_config.template_settings.template_cache_enabled is True
        assert isinstance(loaded_config.template_settings.template_variables, dict)

    def test_configuration_validation_catches_invalid_values(
        self, temp_project_dir: Path, config_service: ConfigService
    ):
        """Test that validation catches invalid configuration values"""
        # This test will fail initially because validation isn't implemented

        validator = ConfigValidator()

        # Test invalid branch patterns
        invalid_branch_config = BranchNamingConfig(
            default_pattern="invalid-pattern",  # Missing {feature-name}
            patterns=[
                "no-placeholder",
                "spaces in pattern",
                "too/many/special/chars!@#",
            ],
            custom_types={},
        )

        is_valid, error = validator.validate_branch_naming_config(invalid_branch_config)
        assert not is_valid
        assert "feature-name" in error

        # Test invalid AI assistant
        invalid_template_config = TemplateConfig(
            ai_assistant="invalid-assistant",  # Not in allowed list
            custom_templates_dir="/nonexistent/path",
            template_cache_enabled=True,
            template_variables={},
        )

        is_valid, error = validator.validate_template_config(invalid_template_config)
        assert not is_valid
        assert "ai_assistant" in error

        # Test invalid project name
        invalid_project_config = ProjectConfig(
            name="",  # Empty name
            branch_naming=BranchNamingConfig(),
            template_settings=TemplateConfig(),
        )

        is_valid, error = validator.validate_project_config(invalid_project_config)
        assert not is_valid
        assert "name" in error

    def test_configuration_persists_across_init_command_execution(
        self, temp_project_dir: Path, config_service: ConfigService
    ):
        """Test that configuration persists when init command is executed"""
        # This test will fail initially because init command integration isn't implemented

        from specify_cli.commands.init.init import InitCommand
        from specify_cli.models.project import ProjectContext

        # Create init command
        init_command = InitCommand(config_service=config_service)

        # Setup project context with enhanced configuration
        context = ProjectContext(
            project_name="persistent-test-project",
            target_directory=temp_project_dir,
            branch_pattern="feature/{feature-name}",
            ai_assistant="claude",
            custom_template_variables={
                "author": "Integration Test",
                "license": "Apache-2.0",
            },
        )

        # Execute init command
        result = init_command.execute(context)
        assert result.success, "Init command should succeed"

        # Verify configuration was persisted
        config_file = temp_project_dir / ".specify" / "config.toml"
        assert config_file.exists(), "Configuration file should be created by init"

        # Load and verify persisted configuration
        loaded_config = config_service.load_project_config(temp_project_dir)
        assert loaded_config is not None
        assert loaded_config.name == "persistent-test-project"
        assert loaded_config.template_settings.ai_assistant == "claude"
        assert (
            loaded_config.template_settings.template_variables["author"]
            == "Integration Test"
        )

    def test_configuration_migration_from_old_format(
        self, temp_project_dir: Path, config_service: ConfigService
    ):
        """Test configuration migration from old format to new enhanced format"""
        # This test will fail initially because migration logic isn't implemented

        # Create old format configuration file
        config_dir = temp_project_dir / ".specify"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"

        # Write old format (missing enhanced fields)
        old_config = {
            "name": "legacy-project",
            "branch_pattern": "001-{feature-name}",  # Old single pattern format
            "ai_assistant": "claude",
        }
        dump_toml(old_config, config_file)

        # Load configuration (should trigger migration)
        migrated_config = config_service.load_project_config(temp_project_dir)
        assert migrated_config is not None

        # Verify migration to new format
        assert migrated_config.name == "legacy-project"

        # Check that old branch_pattern was migrated to new structure
        assert migrated_config.branch_naming.default_pattern == "001-{feature-name}"
        assert "001-{feature-name}" in migrated_config.branch_naming.patterns

        # Check that enhanced fields were added with defaults
        assert isinstance(migrated_config.branch_naming.custom_types, dict)
        assert isinstance(migrated_config.template_settings.template_variables, dict)
        assert migrated_config.template_settings.template_cache_enabled is True

        # Verify migration created backup
        backup_file = config_dir / "config.toml.backup"
        assert backup_file.exists(), "Migration should create backup of old config"

        # Verify new format was saved
        updated_config_data = tomllib.loads(config_file.read_text())
        assert "project" in updated_config_data
        assert "branch_naming" in updated_config_data["project"]
        assert "template_settings" in updated_config_data["project"]

    def test_configuration_backup_and_restore(
        self,
        temp_project_dir: Path,
        config_service: ConfigService,
        sample_enhanced_config: ProjectConfig,
    ):
        """Test configuration backup and restore functionality"""
        # This test will fail initially because backup/restore methods aren't implemented

        # Save initial configuration
        success = config_service.save_project_config(
            temp_project_dir, sample_enhanced_config
        )
        assert success

        # Create backup
        backup_path = config_service.backup_config(temp_project_dir)
        assert backup_path.exists(), "Backup file should be created"
        assert backup_path.name.endswith(".backup"), (
            "Backup should have .backup extension"
        )

        # Modify configuration
        modified_config = sample_enhanced_config
        modified_config.name = "modified-project"
        modified_config.template_settings.ai_assistant = "gemini"

        success = config_service.save_project_config(temp_project_dir, modified_config)
        assert success

        # Verify modification
        loaded_config = config_service.load_project_config(temp_project_dir)
        assert loaded_config.name == "modified-project"
        assert loaded_config.template_settings.ai_assistant == "gemini"

        # Restore from backup
        success = config_service.restore_config(temp_project_dir, backup_path)
        assert success

        # Verify restoration
        restored_config = config_service.load_project_config(temp_project_dir)
        assert restored_config.name == sample_enhanced_config.name
        assert restored_config.template_settings.ai_assistant == "claude"

    def test_global_and_project_config_merge(
        self, temp_project_dir: Path, config_service: ConfigService
    ):
        """Test merging of global and project-specific configurations"""
        # This test will fail initially because config merging isn't implemented

        # Create global configuration
        global_config = ProjectConfig(
            name="global-defaults",
            branch_naming=BranchNamingConfig(
                default_pattern="global/{feature-name}",
                patterns=["global/{feature-name}", "global-fix/{bug-id}"],
                custom_types={"global": "global/{type}"},
            ),
            template_settings=TemplateConfig(
                ai_assistant="claude",
                template_cache_enabled=True,
                template_variables={"global_var": "global_value", "shared": "global"},
            ),
        )

        # Save global config
        success = config_service.save_global_config(global_config)
        assert success

        # Create project-specific configuration (partial override)
        project_config = ProjectConfig(
            name="project-specific",
            branch_naming=BranchNamingConfig(
                default_pattern="project/{feature-name}",  # Override
                patterns=["project/{feature-name}"],  # Override
                custom_types={"project": "project/{type}"},  # Merge
            ),
            template_settings=TemplateConfig(
                ai_assistant="gemini",  # Override
                template_cache_enabled=True,  # Same as global
                template_variables={
                    "project_var": "project_value",
                    "shared": "project",
                },  # Merge with override
            ),
        )

        # Save project config
        success = config_service.save_project_config(temp_project_dir, project_config)
        assert success

        # Get merged configuration
        merged_config = config_service.get_merged_config(temp_project_dir)

        # Verify merging behavior
        assert merged_config.name == "project-specific"  # Project overrides global

        # Branch naming should use project values
        assert merged_config.branch_naming.default_pattern == "project/{feature-name}"
        assert "project/{feature-name}" in merged_config.branch_naming.patterns

        # Custom types should be merged
        assert "global" in merged_config.branch_naming.custom_types
        assert "project" in merged_config.branch_naming.custom_types

        # Template settings should merge appropriately
        assert (
            merged_config.template_settings.ai_assistant == "gemini"
        )  # Project override
        assert (
            merged_config.template_settings.template_cache_enabled is True
        )  # Same in both

        # Template variables should merge with project override
        variables = merged_config.template_settings.template_variables
        assert variables["global_var"] == "global_value"  # From global
        assert variables["project_var"] == "project_value"  # From project
        assert variables["shared"] == "project"  # Project overrides global

    def test_concurrent_config_access_handling(
        self,
        temp_project_dir: Path,
        config_service: ConfigService,
        sample_enhanced_config: ProjectConfig,
    ):
        """Test handling of concurrent configuration access"""
        # This test will fail initially because concurrency handling isn't implemented

        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Save initial configuration
        success = config_service.save_project_config(
            temp_project_dir, sample_enhanced_config
        )
        assert success

        def modify_config(modification_id: int) -> bool:
            """Function to modify config in separate thread"""
            try:
                # Load config
                config = config_service.load_project_config(temp_project_dir)
                if config is None:
                    return False

                # Modify config
                config.name = f"modified-by-thread-{modification_id}"
                config.template_settings.template_variables[
                    f"thread_{modification_id}"
                ] = f"value_{modification_id}"

                # Add small delay to increase chance of race condition
                time.sleep(0.01)

                # Save config
                return config_service.save_project_config(temp_project_dir, config)
            except Exception:
                return False

        # Execute concurrent modifications
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(modify_config, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]

        # At least some modifications should succeed
        assert any(results), "At least some concurrent modifications should succeed"

        # Final configuration should be valid and loadable
        final_config = config_service.load_project_config(temp_project_dir)
        assert final_config is not None
        assert final_config.name.startswith("modified-by-thread-")

        # Config file should not be corrupted
        config_file = temp_project_dir / ".specify" / "config.toml"
        assert config_file.exists()

        # Should be valid TOML
        config_data = tomllib.loads(config_file.read_text())
        assert "project" in config_data
        assert "name" in config_data["project"]

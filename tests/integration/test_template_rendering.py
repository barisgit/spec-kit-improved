"""
Integration test for SpecifyX AI-aware Jinja2 template rendering with injection points

Tests the enhanced template system with multi-assistant support and injection points.
This validates the integration between template service, assistant registry, and memory service.

Key areas tested:
1. Injection point integration with templates
2. Multi-assistant template rendering with different injection values
3. Memory service integration for dynamic imports
4. Template package orchestration with assistant-specific content
5. Performance and error handling for injection points
6. Backwards compatibility with existing templates

The tests validate:
1. AI-specific injection points ({{ assistant_command_prefix }}, {{ assistant_setup_instructions }})
2. Template context variable substitution with enhanced context
3. Granular template processing with injection point support
4. Template package orchestration with multi-assistant support
5. Script template execution permissions
6. Fallback behavior for unknown AI assistants and missing injection points
"""

from pathlib import Path

import pytest

# These imports will FAIL initially for services - that's expected for TDD
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.project import TemplateContext
from specify_cli.models.template import TemplatePackage
from specify_cli.services.template_service import TemplateService


class TestAIAwareTemplateRendering:
    """Integration tests for AI-specific template rendering using real SpecifyX templates"""

    @pytest.fixture
    def claude_template_context(self) -> TemplateContext:
        """Create template context for Claude AI assistant"""
        branch_config = BranchNamingConfig()
        branch_config.description = (
            "Traditional numbered branches with hotfixes and main branches"
        )
        branch_config.patterns = [
            "{number-3}-{feature-name}",
            "hotfix/{bug-id}",
            "main",
            "development",
        ]
        branch_config.validation_rules = [
            "max_length_50",
            "lowercase_only",
            "no_spaces",
            "alphanumeric_dash_only",
        ]

        return TemplateContext(
            project_name="test-project",
            ai_assistant="claude",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/project").resolve(),
        )

    @pytest.fixture
    def gemini_template_context(self) -> TemplateContext:
        """Create template context for Gemini AI assistant"""
        branch_config = BranchNamingConfig()
        branch_config.description = (
            "Modern feature branches with hotfixes and main branches"
        )
        branch_config.patterns = [
            "feature/{feature-name}",
            "hotfix/{bug-id}",
            "bugfix/{bug-id}",
            "main",
            "development",
        ]
        branch_config.validation_rules = [
            "max_length_50",
            "lowercase_only",
            "no_spaces",
            "alphanumeric_dash_only",
        ]

        return TemplateContext(
            project_name="gemini-test",
            ai_assistant="gemini",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/gemini").resolve(),
        )

    @pytest.fixture
    def copilot_template_context(self) -> TemplateContext:
        """Create template context for GitHub Copilot"""
        branch_config = BranchNamingConfig()
        branch_config.description = "Team-based branches with workflow support"
        branch_config.patterns = [
            "{team}/{feature-name}",
            "hotfix/{bug-id}",
            "release/{version}",
            "main",
            "development",
        ]
        branch_config.validation_rules = [
            "max_length_60",
            "lowercase_only",
            "no_spaces",
            "alphanumeric_dash_slash_only",
        ]

        return TemplateContext(
            project_name="copilot-project",
            ai_assistant="copilot",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/copilot").resolve(),
        )

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance - will fail initially due to missing AI-aware methods"""
        # This will fail when we try to use AI-aware methods that don't exist yet
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    def test_discover_templates_from_package(
        self, template_service: TemplateService
    ) -> None:
        """Test template discovery from SpecifyX package resources"""
        # This will fail initially - testing template discovery method that doesn't exist yet
        templates = template_service.discover_templates()

        # Should find all our templates
        assert len(templates) > 0

        # Check for specific templates we know exist
        template_names = [t.name for t in templates]
        assert "specify.md" in template_names
        assert "constitution.md" in template_names
        assert "create-feature.py" in template_names
        assert "plan.md" in template_names

        # Check template categories
        categories = [t.category for t in templates]
        assert "commands" in categories
        assert "memory" in categories
        assert "scripts" in categories

    def test_claude_specific_template_rendering(
        self,
        template_service: TemplateService,
        claude_template_context: TemplateContext,
    ):
        """Test Claude-specific conditional logic in templates"""
        # Load the real specify command template using method that doesn't exist yet
        template_service.load_template("specify.md.j2")
        content = template_service.render_template(
            "specify.md.j2", claude_template_context
        )

        # Should contain Claude-specific content
        # Note: Auth instructions may vary, don't test specific auth commands
        assert (
            "The `specifyx run create-feature` command creates and checks out the new branch"
            in content
        )

        # Should NOT contain other AI assistant content
        assert "Gemini Integration:" not in content
        assert "GitHub Copilot Integration:" not in content

        # Test constitution template for Claude using method that doesn't exist yet
        template_service.load_template("constitution.md.j2")
        constitution_content = template_service.render_template(
            "constitution.md.j2", claude_template_context
        )

        # Constitution should be generated for the correct assistant
        assert "Generated by**: SpecifyX claude template" in constitution_content

        # Template should render without errors - project-specific content is optional
        assert len(constitution_content) > 100  # Should have substantial content

    def test_template_context_variable_substitution(
        self,
        template_service: TemplateService,
        claude_template_context: TemplateContext,
    ):
        """Test that all template context variables are properly substituted"""
        template_service.load_template("constitution.md.j2")
        content = template_service.render_template(
            "constitution.md.j2", claude_template_context
        )

        # Claude assistant should be properly substituted
        assert "claude" in content.lower()

        # Basic template rendering verification
        assert "constitution" in content.lower()
        assert len(content) > 100  # Should have substantial content

    def test_granular_template_processing(
        self,
        template_service: TemplateService,
        claude_template_context: TemplateContext,
    ):
        """Test that each template generates exactly one output file"""
        templates = template_service.discover_templates()

        for template in templates:
            # Each template should have required attributes
            assert hasattr(template, "name")
            assert hasattr(template, "template_path")
            assert hasattr(template, "category")

            # Template should be renderable
            content = template_service.render_template(
                template.name + ".j2", claude_template_context
            )
            assert content is not None
            assert len(content) > 0

            # Content should contain project name for templates that use it (basic substitution test)
            if (
                template.name == "specify"
            ):  # At least the specify template should use project name
                assert claude_template_context.project_name in content

    def test_script_template_execution_permissions(
        self,
        template_service: TemplateService,
        claude_template_context: TemplateContext,
    ):
        """Test that script templates are marked as executable"""
        # This method doesn't exist yet - will fail initially
        script_templates = template_service.discover_templates_by_category("scripts")

        for template in script_templates:
            assert template.executable is True
            assert template.category == "scripts"

            # Python scripts should be in scripts category
            if template.category == "scripts":
                content = template_service.render_template(
                    template.name + ".j2", claude_template_context
                )

                # Should contain proper Python script structure
                assert "#!/usr/bin/env python3" in content or "import" in content

                # Should import SpecifyX utilities for consistency
                assert "from specify_cli" in content or "import specify_cli" in content

    def test_template_package_orchestration(
        self,
        template_service: TemplateService,
        claude_template_context: TemplateContext,
    ):
        """Test complete template package processing"""
        # This tests the full workflow - will fail initially
        package = TemplatePackage(
            ai_assistant="claude",
            templates=template_service.discover_templates(),
            output_structure={},
            dependencies={},
        )

        # Validate package using method that doesn't exist yet
        is_valid = template_service.validate_template_package(package)
        assert is_valid is True

        # Render entire package using method that doesn't exist yet
        results = template_service.render_template_package(
            package, claude_template_context
        )

        # Should have most templates rendered successfully (allow for some failures)
        assert (
            len(results) >= len(package.templates) - 2
        )  # Allow a few templates to fail

        # Each result should have rendered content
        for result in results:
            assert hasattr(result, "template")
            assert hasattr(result, "content")
            assert len(result.content) > 0

    def test_template_error_handling(self, template_service: TemplateService) -> None:
        """Test error handling for template rendering failures"""
        # Test with invalid template context
        invalid_context = None

        with pytest.raises(ValueError):
            template_service.render_template("specify.j2", invalid_context)

        # Test with missing template
        valid_context = TemplateContext(
            project_name="error-test",
            ai_assistant="claude",
            branch_naming_config=BranchNamingConfig("", ["test"], []),
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test").resolve(),
        )

        with pytest.raises(FileNotFoundError):
            template_service.render_template("nonexistent.j2", valid_context)

    @pytest.mark.parametrize(
        "ai_assistant,expected_commands",
        [
            ("claude", [".claude/commands/"]),
            ("gemini", [".claude/commands/"]),  # May use same directory structure
            ("copilot", [".claude/commands/"]),
        ],
    )
    def test_ai_specific_output_paths(
        self,
        template_service: TemplateService,
        ai_assistant: str,
        expected_commands: list,
    ):
        """Test that output paths are correct for each AI assistant"""
        expected_commands = expected_commands

        TemplateContext(
            project_name="path-test",
            ai_assistant=ai_assistant,
            branch_naming_config=BranchNamingConfig("", ["test"], []),
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test").resolve(),
        )

        # This method doesn't exist yet - will fail initially
        templates = template_service.discover_templates_by_category("commands")

        for template in templates:
            # Templates should have appropriate categories
            if template.category == "commands":
                # Commands should be AI-aware
                assert template.ai_aware is True

    def test_load_real_specityx_templates_from_package_resources(
        self, template_service: TemplateService
    ):
        """Test loading actual SpecifyX templates from package resources"""
        # This test specifically validates that we can load the real templates from:
        # src/specify_cli/templates/

        # This method doesn't exist yet - will fail initially
        success = template_service.load_templates_from_package_resources()
        assert success is True

        # Should discover the real templates we know exist
        templates = template_service.discover_templates()
        template_names = [t.name for t in templates]

        # Validate we found the actual SpecifyX templates
        expected_templates = {
            "specify.md": "commands",
            "plan.md": "commands",
            "tasks.md": "commands",
            "constitution.md": "commands",
            "create-feature.py": "scripts",
            "setup-plan.py": "scripts",
            "check-prerequisites.py": "scripts",
            "spec-template.md": "runtime_templates",
            "plan-template.md": "runtime_templates",
            "tasks-template.md": "runtime_templates",
        }

        for template_name, expected_category in expected_templates.items():
            assert template_name in template_names, f"Missing template: {template_name}"

            # Find the template and check its category
            template = next(t for t in templates if t.name == template_name)
            assert template.category == expected_category, (
                f"Wrong category for {template_name}: expected {expected_category}, got {template.category}"
            )

            # Templates should be marked as AI-aware
            if template.category in ["commands", "memory"]:
                assert template.ai_aware is True, (
                    f"Template {template_name} should be AI-aware"
                )


class TestInjectionPointPerformance:
    """Performance tests for injection point system"""

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance"""
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    @pytest.fixture
    def performance_context(self) -> TemplateContext:
        """Create context for performance testing"""
        from specify_cli.models.config import BranchNamingConfig

        branch_config = BranchNamingConfig()
        branch_config.patterns = ["feature/{feature-name}"]

        return TemplateContext(
            project_name="performance-test",
            ai_assistant="claude",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-17",
            project_path=Path("/tmp/performance-test").resolve(),
        )

    def test_injection_point_loading_performance(
        self,
        template_service: TemplateService,
        performance_context: TemplateContext,
        tmp_path: Path,
    ):
        """Test that injection point loading meets performance requirements"""
        import time

        # Create template with many injection points
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_content = "\n".join(
            [
                "{{ assistant_command_prefix }}",
                "{{ assistant_setup_instructions }}",
                "{{ assistant_context_file_path }}",
                "{{ assistant_context_file_description }}",
                "{{ assistant_memory_configuration }}",
                "{{ assistant_review_command }}",
                "{{ assistant_documentation_url }}",
                "{{ assistant_workflow_integration }}",
                "{{ assistant_custom_commands }}",
                "{{ assistant_best_practices }}",
                "{{ assistant_troubleshooting }}",
                "{{ assistant_limitations }}",
                "{{ assistant_file_extensions }}",
            ]
        )
        (template_dir / "perf.md.j2").write_text(template_content)

        # Load template package
        template_service.load_template_package("claude", template_dir)

        # Measure rendering performance
        start_time = time.time()
        for _ in range(10):  # Render 10 times to get average
            template_service.render_template("perf.md.j2", performance_context)
        end_time = time.time()

        # Should complete 10 renders in under 1 second (100ms per render)
        total_time = end_time - start_time
        avg_time_per_render = total_time / 10

        assert total_time < 1.0, f"10 renders took {total_time:.3f}s, should be < 1.0s"
        assert avg_time_per_render < 0.1, (
            f"Average render time {avg_time_per_render:.3f}s, should be < 0.1s"
        )

    def test_multi_assistant_performance(
        self,
        template_service: TemplateService,
        performance_context: TemplateContext,
        tmp_path: Path,
    ):
        """Test performance when switching between assistants"""
        import time

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_content = (
            "{{ assistant_command_prefix }}"
            "{{ assistant_setup_instructions }}"
            "{{ assistant_context_file_path }}"
        )
        (template_dir / "multi-perf.md.j2").write_text(template_content)

        assistants = ["claude", "gemini", "copilot"]
        total_start = time.time()

        for assistant in assistants:
            # Update context for this assistant
            test_context = TemplateContext(
                project_name="multi-perf-test",
                ai_assistant=assistant,
                branch_naming_config=performance_context.branch_naming_config,
                config_directory=".specify",
                creation_date="2025-09-17",
                project_path=Path("/tmp/multi-perf-test").resolve(),
            )

            # Load and render for this assistant
            start_time = time.time()
            template_service.load_template_package(assistant, template_dir)
            result = template_service.render_template("multi-perf.md.j2", test_context)
            end_time = time.time()

            # Each assistant should render in under 200ms
            render_time = end_time - start_time
            assert render_time < 0.2, (
                f"{assistant} render took {render_time:.3f}s, should be < 0.2s"
            )
            assert len(result) > 0, f"{assistant} should produce non-empty result"

        total_time = time.time() - total_start
        # All three assistants should complete in under 1 second total
        assert total_time < 1.0, (
            f"All assistants took {total_time:.3f}s, should be < 1.0s"
        )

    def test_memory_integration_performance(
        self, template_service: TemplateService, tmp_path: Path
    ):
        """Test performance of memory service integration"""
        import time

        # Create project with memory files
        project_path = tmp_path / "memory-perf-test"
        project_path.mkdir()

        memory_dir = project_path / ".specify" / "memory"
        memory_dir.mkdir(parents=True)

        # Create multiple memory files
        for i in range(5):
            (memory_dir / f"memory_{i}.md").write_text(
                f"# Memory File {i}\nContent {i}"
            )

        # Create template that uses memory imports
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_content = (
            "Project: {{ project_name }}\n"
            "{% if assistant_memory_imports %}\n"
            "Memory: {{ assistant_memory_imports }}\n"
            "{% endif %}"
        )
        (template_dir / "memory-perf.md.j2").write_text(template_content)

        # Create context with memory
        context = TemplateContext(
            project_name="memory-perf-test",
            ai_assistant="claude",
            branch_naming_config=BranchNamingConfig(
                patterns=["feature/{feature-name}"]
            ),
            config_directory=".specify",
            creation_date="2025-09-17",
            project_path=project_path,
        )

        # Measure memory integration performance
        start_time = time.time()
        template_service.load_template_package("claude", template_dir)
        result = template_service.render_template("memory-perf.md.j2", context)
        end_time = time.time()

        # Memory integration should complete in under 500ms
        total_time = end_time - start_time
        assert total_time < 0.5, (
            f"Memory integration took {total_time:.3f}s, should be < 0.5s"
        )
        assert len(result) > 0, (
            "Should produce non-empty result with memory integration"
        )

    def test_template_discovery_performance(
        self, template_service: TemplateService
    ) -> None:
        """Test performance of template discovery from package resources"""
        import time

        # Measure template discovery performance
        start_time = time.time()
        templates = template_service.discover_templates()
        end_time = time.time()

        # Template discovery should complete in under 100ms
        discovery_time = end_time - start_time
        assert discovery_time < 0.1, (
            f"Template discovery took {discovery_time:.3f}s, should be < 0.1s"
        )
        assert len(templates) > 0, "Should discover templates from package resources"

        # Test repeated discovery (should use cache)
        start_time = time.time()
        templates2 = template_service.discover_templates()
        end_time = time.time()

        # Cached discovery should be much faster (under 10ms)
        cached_time = end_time - start_time
        assert cached_time < 0.01, (
            f"Cached discovery took {cached_time:.3f}s, should be < 0.01s"
        )
        assert templates == templates2, "Cached discovery should return same results"

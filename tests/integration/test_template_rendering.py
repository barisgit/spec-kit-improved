"""
Integration test for SpecifyX AI-aware Jinja2 template rendering

This test follows TDD principles and will FAIL initially since the AI-aware services aren't implemented yet.
Tests the actual SpecifyX templates with AI-specific conditional logic.

MISSING METHODS that need to be implemented in JinjaTemplateService:
- discover_templates() -> List[GranularTemplate]: Discover templates from package resources
- discover_templates_by_category(category: str) -> List[GranularTemplate]: Filter templates by category
- load_template(template_name: str) -> GranularTemplate: Load individual template object
- load_templates_from_package_resources() -> bool: Load templates from src/specify_cli/init_templates/
- validate_template_package(package: TemplatePackage) -> bool: Validate template package
- render_template_package(package: TemplatePackage, context: TemplateContext) -> List[...]: Render full package

CURRENT FUNCTIONALITY that exists but needs enhancement:
- render_template(template_name: str, context: TemplateContext) -> str: Needs AI-aware context handling
- load_template_package(ai_assistant: str, template_dir: Path) -> bool: Needs package resource support

The tests validate:
1. AI-specific conditional logic ({% if ai_assistant == 'claude' %})
2. Template context variable substitution
3. Granular template processing (one template -> one file)
4. Template package orchestration
5. Script template execution permissions
6. Fallback behavior for unknown AI assistants
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
        branch_config = BranchNamingConfig(
            description="Traditional numbered branches with hotfixes and main branches",
            patterns=[
                "{number-3}-{feature-name}",
                "hotfix/{bug-id}",
                "main",
                "development",
            ],
            validation_rules=[
                "max_length_50",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_only",
            ],
        )

        return TemplateContext(
            project_name="test-project",
            ai_assistant="claude",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/project"),
            target_paths={
                "specify.j2": Path("/test/project/.claude/commands/specify"),
                "constitution.j2": Path(
                    "/test/project/.specify/memory/constitution.md"
                ),
                "create-feature.j2": Path(
                    "/test/project/.specify/scripts/create-feature.py"
                ),
            },
        )

    @pytest.fixture
    def gemini_template_context(self) -> TemplateContext:
        """Create template context for Gemini AI assistant"""
        branch_config = BranchNamingConfig(
            description="Modern feature branches with hotfixes and main branches",
            patterns=[
                "feature/{feature-name}",
                "hotfix/{bug-id}",
                "bugfix/{bug-id}",
                "main",
                "development",
            ],
            validation_rules=[
                "max_length_50",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_only",
            ],
        )

        return TemplateContext(
            project_name="gemini-test",
            ai_assistant="gemini",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/gemini"),
            target_paths={
                "specify.j2": Path("/test/gemini/.claude/commands/specify"),
                "constitution.j2": Path("/test/gemini/.specify/memory/constitution.md"),
            },
        )

    @pytest.fixture
    def copilot_template_context(self) -> TemplateContext:
        """Create template context for GitHub Copilot"""
        branch_config = BranchNamingConfig(
            description="Team-based branches with workflow support",
            patterns=[
                "{team}/{feature-name}",
                "hotfix/{bug-id}",
                "release/{version}",
                "main",
                "development",
            ],
            validation_rules=[
                "max_length_60",
                "lowercase_only",
                "no_spaces",
                "alphanumeric_dash_slash_only",
            ],
        )

        return TemplateContext(
            project_name="copilot-project",
            ai_assistant="copilot",
            branch_naming_config=branch_config,
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/copilot"),
            target_paths={},
        )

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance - will fail initially due to missing AI-aware methods"""
        # This will fail when we try to use AI-aware methods that don't exist yet
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    def test_discover_templates_from_package(self, template_service: TemplateService):
        """Test template discovery from SpecifyX package resources"""
        # This will fail initially - testing template discovery method that doesn't exist yet
        templates = template_service.discover_templates()

        # Should find all our templates
        assert len(templates) > 0

        # Check for specific templates we know exist
        template_names = [t.name for t in templates]
        assert "specify" in template_names
        assert "constitution" in template_names
        assert "create-feature" in template_names
        assert "plan" in template_names

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
        specify_template = template_service.load_template("specify.j2")
        content = template_service.render_template(
            specify_template, claude_template_context
        )

        # Should contain Claude-specific content
        assert "Claude Code Integration:" in content
        assert "Use this command with `/specify` in any file" in content
        assert (
            "Generated specifications follow the project's configured branch naming pattern"
            in content
        )

        # Should NOT contain other AI assistant content
        assert "Gemini Integration:" not in content
        assert "GitHub Copilot Integration:" not in content

        # Test constitution template for Claude using method that doesn't exist yet
        constitution_template = template_service.load_template("constitution.j2")
        constitution_content = template_service.render_template(
            constitution_template, claude_template_context
        )

        # Should contain Claude-specific workflow
        assert (
            "Claude Code commands (specify, plan, tasks) drive the workflow"
            in constitution_content
        )
        assert (
            "All templates support Claude-specific features and syntax"
            in constitution_content
        )

        # Should contain project-specific info
        assert "test-project" in constitution_content
        assert (
            "{number-3}-{feature-name}" in constitution_content
            or "001-feature-name" in constitution_content
        )

    def test_gemini_specific_template_rendering(
        self,
        template_service: TemplateService,
        gemini_template_context: TemplateContext,
    ):
        """Test Gemini-specific conditional logic in templates"""
        specify_template = template_service.load_template("specify.j2")
        content = template_service.render_template(
            specify_template, gemini_template_context
        )

        # Should contain Gemini-specific content
        assert "Gemini Integration:" in content
        assert "Templates optimized for Gemini's interaction patterns" in content

        # Should NOT contain other AI assistant content
        assert "Claude Code Integration:" not in content
        assert "GitHub Copilot Integration:" not in content

        # Test constitution for different branch pattern
        constitution_template = template_service.load_template("constitution.j2")
        constitution_content = template_service.render_template(
            constitution_template, gemini_template_context
        )

        assert (
            "Gemini CLI integration for specification and planning workflows"
            in constitution_content
        )
        assert "feature/{feature-name}" in constitution_content

    def test_copilot_specific_template_rendering(
        self,
        template_service: TemplateService,
        copilot_template_context: TemplateContext,
    ):
        """Test GitHub Copilot-specific conditional logic in templates"""
        specify_template = template_service.load_template("specify.j2")
        content = template_service.render_template(
            specify_template, copilot_template_context
        )

        # Should contain Copilot-specific content
        assert "GitHub Copilot Integration:" in content
        assert "Use this command in your IDE or terminal" in content
        assert "Works with your configured branch naming patterns" in content

        # Should NOT contain other AI assistant content
        assert "Claude Code Integration:" not in content
        assert "Gemini Integration:" not in content

    def test_fallback_for_unknown_ai_assistant(self, template_service: TemplateService):
        """Test fallback behavior for unknown AI assistant"""
        unknown_context = TemplateContext(
            project_name="unknown-test",
            ai_assistant="unknown-ai",
            branch_naming_config=BranchNamingConfig(
                description="Default pattern",
                patterns=["001-{feature-name}"],
                validation_rules=["max_length_50"],
            ),
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test/unknown"),
            target_paths={},
        )

        specify_template = template_service.load_template("specify.j2")
        content = template_service.render_template(specify_template, unknown_context)

        # Should contain generic fallback content
        assert "Generic AI Assistant:" in content
        assert "Use this command to create feature specifications" in content
        assert "Configurable branch naming patterns supported" in content

    def test_template_context_variable_substitution(
        self,
        template_service: TemplateService,
        claude_template_context: TemplateContext,
    ):
        """Test that all template context variables are properly substituted"""
        constitution_template = template_service.load_template("constitution.j2")
        content = template_service.render_template(
            constitution_template, claude_template_context
        )

        # Project name should be substituted everywhere
        assert "test-project" in content.lower() or "Test-Project" in content

        # Date should be substituted
        assert "2025-09-08" in content

        # AI assistant should be referenced
        assert "claude" in content.lower()

        # Branch pattern should be included
        assert "{number-3}-{feature-name}" in content or "001-feature-name" in content

        # Config directory should be referenced
        assert ".specify" in content

    def test_granular_template_processing(
        self,
        template_service: TemplateService,
        claude_template_context: TemplateContext,
    ):
        """Test that each template generates exactly one output file"""
        templates = template_service.discover_templates()

        for template in templates:
            # Each template should have exactly one target path
            assert hasattr(template, "target_path")
            assert template.target_path is not None
            assert isinstance(template.target_path, str)

            # Template should be renderable
            content = template_service.render_template(
                template, claude_template_context
            )
            assert content is not None
            assert len(content) > 0

            # Content should contain project name (basic substitution test)
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

            # Python scripts should have .py extension in target path
            if template.target_path.endswith(".py"):
                content = template_service.render_template(
                    template, claude_template_context
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

        # Should have results for each template
        assert len(results) == len(package.templates)

        # Each result should have rendered content
        for result in results:
            assert hasattr(result, "template")
            assert hasattr(result, "content")
            assert hasattr(result, "target_path")
            assert len(result.content) > 0

    def test_template_conditional_logic_complexity(
        self, template_service: TemplateService
    ):
        """Test complex conditional logic with multiple AI assistants"""
        contexts = [
            ("claude", "Claude Code Integration"),
            ("gemini", "Gemini Integration"),
            ("copilot", "GitHub Copilot Integration"),
            ("unknown", "Generic AI Assistant"),
        ]

        specify_template = template_service.load_template("specify.j2")

        for ai_assistant, expected_text in contexts:
            context = TemplateContext(
                project_name="conditional-test",
                ai_assistant=ai_assistant,
                branch_naming_config=BranchNamingConfig(
                    description="Test pattern",
                    patterns=["test-{name}"],
                    validation_rules=[],
                ),
                config_directory=".specify",
                creation_date="2025-09-08",
                project_path=Path("/test"),
                target_paths={},
            )

            content = template_service.render_template(specify_template, context)

            # Should contain AI-specific content
            assert expected_text in content

            # Should not contain other AI assistant markers
            other_markers = [
                marker for _, marker in contexts if marker != expected_text
            ]
            for other_marker in other_markers:
                assert other_marker not in content

    def test_template_error_handling(self, template_service: TemplateService):
        """Test error handling for template rendering failures"""
        # Test with invalid template context
        invalid_context = None

        with pytest.raises(Exception):
            template_service.render_template("specify.j2", invalid_context)

        # Test with missing template
        valid_context = TemplateContext(
            project_name="error-test",
            ai_assistant="claude",
            branch_naming_config=BranchNamingConfig("", ["test"], []),
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test"),
            target_paths={},
        )

        with pytest.raises(Exception):
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
        TemplateContext(
            project_name="path-test",
            ai_assistant=ai_assistant,
            branch_naming_config=BranchNamingConfig("", ["test"], []),
            config_directory=".specify",
            creation_date="2025-09-08",
            project_path=Path("/test"),
            target_paths={},
        )

        # This method doesn't exist yet - will fail initially
        templates = template_service.discover_templates_by_category("commands")

        for template in templates:
            # Target paths should be appropriate for AI assistant
            if template.target_path:
                # Commands should go in AI-specific directories or generic locations
                assert (
                    any(
                        expected_path in template.target_path
                        for expected_path in expected_commands
                    )
                    or ".specify/" in template.target_path
                )

    def test_load_real_specityx_templates_from_package_resources(
        self, template_service: TemplateService
    ):
        """Test loading actual SpecifyX templates from package resources"""
        # This test specifically validates that we can load the real templates from:
        # src/specify_cli/init_templates/

        # This method doesn't exist yet - will fail initially
        success = template_service.load_templates_from_package_resources()
        assert success is True

        # Should discover the real templates we know exist
        templates = template_service.discover_templates()
        template_names = [t.name for t in templates]

        # Validate we found the actual SpecifyX templates
        expected_templates = {
            "specify": "commands",
            "plan": "commands",
            "tasks": "commands",
            "constitution": "memory",
            "create-feature": "scripts",
            "setup-plan": "scripts",
            "check-prerequisites": "scripts",
            "spec-template": "runtime_templates",
            "plan-template": "runtime_templates",
            "tasks-template": "runtime_templates",
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

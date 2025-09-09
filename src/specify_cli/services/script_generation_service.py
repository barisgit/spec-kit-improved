"""
Script generation service for SpecifyX Python script creation

This service generates Python scripts from Jinja2 templates, sets proper
executable permissions, and validates SpecifyX utility imports.
"""

import ast
import os
import stat
import sys
from pathlib import Path
from typing import Dict, List, Optional

from specify_cli.models.project import TemplateContext
from specify_cli.models.script import GeneratedScript, ScriptState
from specify_cli.models.template import GranularTemplate, TemplateCategory
from specify_cli.services.template_service import TemplateService

# FIXME: CRITICAL - This can probably be removed


class ScriptGenerationService:
    """Service for generating Python scripts from Jinja2 templates"""

    def __init__(self, template_service: Optional[TemplateService] = None):
        """
        Initialize script generation service

        Args:
            template_service: Optional template service for template operations
        """
        self.template_service = template_service
        self._script_imports_cache: Dict[str, List[str]] = {}

    def generate_scripts_from_templates(
        self,
        template_context: TemplateContext,
        output_directory: Path,
        ai_assistant: Optional[str] = None,
    ) -> List[GeneratedScript]:
        """
        Generate Python scripts from script templates

        Args:
            template_context: Template context with variables
            output_directory: Directory where scripts should be created
            ai_assistant: AI assistant for template filtering (defaults to context.ai_assistant)

        Returns:
            List of GeneratedScript objects in GENERATED state

        Raises:
            ValueError: If template_context is None or output_directory is invalid
            RuntimeError: If script generation fails
        """
        if template_context is None:
            raise ValueError("template_context cannot be None")

        if not output_directory:
            raise ValueError("output_directory cannot be empty")

        # Create output directory if it doesn't exist
        try:
            output_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create output directory: {e}") from e

        if not output_directory.exists() or not output_directory.is_dir():
            raise ValueError("output_directory must be a valid directory path")

        # Use AI assistant from context if not provided
        if ai_assistant is None:
            ai_assistant = template_context.ai_assistant

        generated_scripts = []

        # Discover script templates from package resources
        script_templates = self._discover_script_templates(ai_assistant)

        for template in script_templates:
            try:
                # Generate script from template
                script = self._generate_single_script(
                    template, template_context, output_directory
                )
                if script:
                    generated_scripts.append(script)

            except Exception as e:
                # Log error but continue with other scripts
                print(
                    f"Warning: Failed to generate script from template '{template.name}': {e}",
                    file=sys.stderr,
                )
                continue

        return generated_scripts

    def set_script_permissions(self, scripts: List[GeneratedScript]) -> bool:
        """
        Set executable permissions on generated scripts

        Args:
            scripts: List of GeneratedScript objects

        Returns:
            True if all permissions were set successfully, False otherwise
        """
        if not scripts:
            return True

        success_count = 0

        for script in scripts:
            try:
                if self._set_single_script_permissions(script):
                    script.make_executable()  # Transition to MADE_EXECUTABLE state
                    success_count += 1
                else:
                    script.mark_validation_error("Failed to set executable permissions")

            except Exception as e:
                script.mark_validation_error(f"Permission error: {e}")
                continue

        return success_count == len(scripts)

    def validate_script_imports(self, scripts: List[GeneratedScript]) -> bool:
        """
        Validate that scripts have valid syntax and SpecifyX imports

        Args:
            scripts: List of GeneratedScript objects

        Returns:
            True if all scripts are valid, False otherwise
        """
        if not scripts:
            return True

        success_count = 0

        for script in scripts:
            try:
                if self._validate_single_script(script):
                    # Only transition to VALIDATED if script is already MADE_EXECUTABLE
                    if script.state == ScriptState.MADE_EXECUTABLE:
                        script.mark_validated()
                    success_count += 1
                else:
                    # Error message already set by _validate_single_script
                    pass

            except Exception as e:
                script.mark_validation_error(f"Validation error: {e}")
                continue

        return success_count == len(scripts)

    def test_script_execution(self, scripts: List[GeneratedScript]) -> bool:
        """
        Test script execution and --json flag support

        Args:
            scripts: List of GeneratedScript objects to test

        Returns:
            True if all scripts execute without syntax errors, False otherwise
        """
        if not scripts:
            return True

        success_count = 0

        for script in scripts:
            try:
                if self._test_single_script_execution(script):
                    success_count += 1
                else:
                    # Error already logged by _test_single_script_execution
                    pass

            except Exception as e:
                script.mark_validation_error(f"Execution test error: {e}")
                continue

        return success_count == len(scripts)

    def _discover_script_templates(self, ai_assistant: str) -> List[GranularTemplate]:
        """Discover script templates from package resources"""
        if self.template_service:
            # Use template service to discover script templates
            try:
                return self.template_service.discover_templates_by_category("scripts")
            except AttributeError:
                # Fallback if discover_templates_by_category is not implemented
                try:
                    all_templates = self.template_service.discover_templates()
                    return [t for t in all_templates if t.category == "scripts"]
                except AttributeError:
                    # Template service doesn't have discovery methods yet
                    pass

        # Fallback: create templates based on known script templates
        # FIXME: HARDCODED - All script template paths and target paths hardcoded
        # TODO: Move to configuration-driven template discovery
        script_templates = [
            GranularTemplate(
                name="create-feature",
                template_path="scripts/create-feature.j2",
                target_path=".specify/scripts/create-feature.py",
                category=TemplateCategory.SCRIPTS.value,
                ai_aware=False,  # Changed to False since all AI assistants can use these
                executable=True,
            ),
            GranularTemplate(
                name="setup-plan",
                template_path="scripts/setup-plan.j2",
                target_path=".specify/scripts/setup-plan.py",
                category=TemplateCategory.SCRIPTS.value,
                ai_aware=False,  # Changed to False since all AI assistants can use these
                executable=True,
            ),
            GranularTemplate(
                name="check-prerequisites",
                template_path="scripts/check-prerequisites.j2",
                target_path=".specify/scripts/check-prerequisites.py",
                category=TemplateCategory.SCRIPTS.value,
                ai_aware=False,  # Changed to False since all AI assistants can use these
                executable=True,
            ),
        ]

        # Since ai_aware=False, all templates are compatible with any AI assistant
        return script_templates

    def _generate_single_script(
        self,
        template: GranularTemplate,
        context: TemplateContext,
        output_directory: Path,
    ) -> Optional[GeneratedScript]:
        """Generate a single script from template"""
        try:
            # Determine target path
            target_path = output_directory / f"{template.name}.py"

            # Generate script content (using a mock template for now)
            script_content = self._generate_script_content(template, context)

            # Write script to file
            target_path.write_text(script_content, encoding="utf-8")

            # Extract imports from generated content
            imports = self._extract_script_imports(script_content)

            # Determine if script supports JSON output
            json_output = "--json" in script_content and "json.dumps" in script_content

            # Create GeneratedScript object (inheriting executable from template)
            script = GeneratedScript(
                name=template.name,
                source_template=template.template_path,
                target_path=target_path,
                imports=imports,
                executable=template.executable,  # Inherit from template
                json_output=json_output,
                state=ScriptState.GENERATED,
            )

            return script

        except Exception as e:
            raise RuntimeError(
                f"Failed to generate script '{template.name}': {e}"
            ) from e

    def _generate_script_content(
        self, template: GranularTemplate, context: TemplateContext
    ) -> str:
        """Generate script content from template using template service"""
        if self.template_service:
            try:
                # Use template service to render the script
                return self.template_service.render_template(template, context)
            except Exception:
                # Fallback to mock implementation if template service fails
                pass

        # Fallback: generate based on template type and context
        if template.name == "create-feature":
            return self._generate_create_feature_script(context)
        elif template.name == "setup-plan":
            return self._generate_setup_plan_script(context)
        elif template.name == "check-prerequisites":
            return self._generate_check_prerequisites_script(context)
        else:
            return self._generate_generic_script(template, context)

    def _generate_create_feature_script(self, context: TemplateContext) -> str:
        """Generate create-feature script content"""
        return f'''#!/usr/bin/env python3
"""
Create a new feature with branch, directory structure, and template.
Generated by SpecifyX init command on {context.creation_date} for {context.ai_assistant}.
Project: {context.project_name}
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Import SpecifyX utilities for consistency
try:
    from specify_cli.services import CommandLineGitService, TomlConfigService
    from specify_cli.utils.validators import validate_feature_description
except ImportError:
    # Fallback if running outside SpecifyX context
    print("Warning: SpecifyX utilities not available, using basic implementation", file=sys.stderr)
    CommandLineGitService = None
    TomlConfigService = None
    validate_feature_description = lambda x: (True, None)


def get_repo_root() -> Path:
    """Get repository root directory."""
    try:
        import subprocess
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                              capture_output=True, text=True, check=True)
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to current directory if not in git repo
        return Path.cwd()


def get_branch_pattern() -> str:
    """Get branch naming pattern from project config."""
    config = load_project_config()
    if config and hasattr(config, 'branch_naming'):
        return config.branch_naming.default_pattern
    return "{{number-3}}-{{feature-name}}"  # Default pattern


def apply_branch_pattern(pattern: str, feature_num: str, feature_name: str) -> str:
    """Apply branch naming pattern with variable substitution."""
    # Simple template substitution
    result = pattern.replace('{{{{number-3}}}}', feature_num)
    result = result.replace('{{{{feature-name}}}}', feature_name)
    result = result.replace('{{number-3}}', feature_num)
    result = result.replace('{{feature-name}}', feature_name)
    return result


def create_branch_name(description: str, feature_num: str) -> str:
    """Create branch name from feature description using project patterns."""
    # Convert to lowercase and replace non-alphanumeric with hyphens
    clean = re.sub(r'[^a-z0-9]', '-', description.lower())
    # Remove multiple consecutive hyphens
    clean = re.sub(r'-+', '-', clean)
    # Remove leading/trailing hyphens  
    clean = clean.strip('-')
    
    # Extract 2-3 meaningful words for feature name
    words = [w for w in clean.split('-') if w and len(w) > 2][:3]
    if not words:
        words = ['feature']
    
    feature_name = '-'.join(words)
    
    # Get branch pattern and create branch name
    pattern = get_branch_pattern()
    branch_name = apply_branch_pattern(pattern, feature_num, feature_name)
    
    return branch_name


def create_feature(description: str, json_mode: bool = False) -> Tuple[bool, Dict[str, str]]:
    """Create new feature with branch and spec file."""
    # Validate feature description
    is_valid, error = validate_feature_description(description)
    if not is_valid:
        return False, {{"error": f"Invalid feature description: {{error}}"}}
    
    repo_root = get_repo_root()
    specs_dir = repo_root / "specs"
    specs_dir.mkdir(exist_ok=True)
    
    # Get next feature number
    highest = 0
    if specs_dir.exists():
        for dir_path in specs_dir.iterdir():
            if dir_path.is_dir():
                match = re.match(r'^(\\d+)', dir_path.name)
                if match:
                    number = int(match.group(1))
                    highest = max(highest, number)
    
    feature_num = f"{{highest + 1:03d}}"
    
    # Create feature name for directory
    feature_words = re.sub(r'[^a-z0-9]', '-', description.lower()).strip('-')
    feature_words = re.sub(r'-+', '-', feature_words)
    words = [w for w in feature_words.split('-') if w and len(w) > 2][:3]
    feature_name = '-'.join(words) if words else 'feature'
    
    # Create branch name using pattern
    branch_name = create_branch_name(description, feature_num)
    
    # Create directory name (always use numbered format for specs)
    dir_name = f"{{feature_num}}-{{feature_name}}"
    feature_dir = specs_dir / dir_name
    
    try:
        # Create and switch to new branch
        if CommandLineGitService:
            git_service = CommandLineGitService()
            if not git_service.create_branch(branch_name, repo_root):
                return False, {{"error": f"Failed to create branch: {{branch_name}}"}}
        else:
            # Fallback git command
            import subprocess
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True, cwd=repo_root)
        
        # Create feature directory
        feature_dir.mkdir(exist_ok=True)
        
        # Create basic spec file
        spec_file = feature_dir / "spec.md"
        spec_file.write_text(f"# Feature Specification: {{description}}\\n\\n**Status**: Draft\\n")
        
        result = {{
            "BRANCH_NAME": branch_name,
            "SPEC_FILE": str(spec_file.absolute()),
            "FEATURE_NUM": feature_num,
            "FEATURE_DIR": str(feature_dir.absolute())
        }}
        
        return True, result
        
    except Exception as e:
        return False, {{"error": str(e)}}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create a new feature with branch and spec file")
    parser.add_argument("description", help="Feature description")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    if not args.description.strip():
        print("Error: Feature description cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    success, result = create_feature(args.description, args.json)
    
    if not success:
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Error: {{result.get('error', 'Unknown error')}}", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(json.dumps(result))
    else:
        for key, value in result.items():
            print(f"{{key}}: {{value}}")


if __name__ == "__main__":
    main()
'''

    def _generate_setup_plan_script(self, context: TemplateContext) -> str:
        """Generate setup-plan script content"""
        return f'''#!/usr/bin/env python3
"""
Setup project planning structure and templates.
Generated by SpecifyX init command on {context.creation_date} for {context.ai_assistant}.
Project: {context.project_name}
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Import SpecifyX utilities for consistency
try:
    from specify_cli.services import ProjectManager, TemplateService
    from specify_cli.utils.file_operations import ensure_directory_exists
except ImportError:
    # Fallback if running outside SpecifyX context
    print("Warning: SpecifyX utilities not available, using basic implementation", file=sys.stderr)
    ProjectManager = None
    TemplateService = None
    
    def ensure_directory_exists(path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False


def setup_planning_structure(project_path: Path, json_mode: bool = False) -> Tuple[bool, Dict[str, List[str]]]:
    """Setup project planning directory structure."""
    try:
        # Create planning directories
        directories = [
            project_path / "specs",
            project_path / "docs" / "planning", 
            # FIXME: HARDCODED - Directory paths hardcoded
            # TODO: Make configurable via configuration system
            project_path / ".specify" / "templates",
            project_path / ".specify" / "scripts",
            project_path / ".claude" / "commands"
        ]
        
        created = []
        for directory in directories:
            if ensure_directory_exists(directory):
                created.append(str(directory))
        
        # FIXME: HARDCODED - Plan file path hardcoded to 'plan.md'
        # TODO: Make configurable via configuration system
        # Create plan.md if it doesn't exist
        plan_file = project_path / "plan.md"
        if not plan_file.exists():
            plan_content = f"""# {context.project_name} - Project Plan

## Overview
Project planning document for {context.project_name}.

## Architecture

## Implementation Plan

## Next Steps

"""
            plan_file.write_text(plan_content)
            created.append(str(plan_file))
        
        return True, {{"created": created}}
        
    except Exception as e:
        return False, {{"error": str(e)}}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup project planning structure")
    parser.add_argument("--path", type=Path, default=Path.cwd(), help="Project path (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    success, result = setup_planning_structure(args.path, args.json)
    
    if not success:
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Error: {{result.get('error', 'Unknown error')}}", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(json.dumps(result))
    else:
        created_files = result.get("created", [])
        for file_path in created_files:
            print(f"Created: {{file_path}}")


if __name__ == "__main__":
    main()
'''

    def _generate_check_prerequisites_script(self, context: TemplateContext) -> str:
        """Generate check-prerequisites script content"""
        return f'''#!/usr/bin/env python3
"""
Check project prerequisites and environment setup.
Generated by SpecifyX init command on {context.creation_date} for {context.ai_assistant}.
Project: {context.project_name}
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Import SpecifyX utilities for consistency  
try:
    from specify_cli.services import ConfigService
    from specify_cli.utils.validators import validate_git_repository
except ImportError:
    # Fallback if running outside SpecifyX context
    print("Warning: SpecifyX utilities not available, using basic implementation", file=sys.stderr)
    ConfigService = None
    
    def validate_git_repository(path: Path) -> Tuple[bool, str]:
        try:
            subprocess.run(['git', 'status'], cwd=path, capture_output=True, check=True)
            return True, "Git repository is valid"
        except Exception as e:
            return False, f"Git repository check failed: {{e}}"


def check_prerequisites(project_path: Path, json_mode: bool = False) -> Tuple[bool, Dict[str, any]]:
    """Check project prerequisites."""
    checks = {{}}
    all_passed = True
    
    try:
        # Check git repository
        git_valid, git_message = validate_git_repository(project_path)
        checks["git"] = {{"passed": git_valid, "message": git_message}}
        if not git_valid:
            all_passed = False
        
        # Check Python version
        python_version = sys.version_info
        python_ok = python_version >= (3, 8)
        checks["python"] = {{
            "passed": python_ok,
            "version": f"{{python_version.major}}.{{python_version.minor}}.{{python_version.micro}}",
            "message": "Python 3.8+ required" if not python_ok else "Python version OK"
        }}
        if not python_ok:
            all_passed = False
        
        # Check required directories
        required_dirs = [".specify", ".specify/scripts", ".claude/commands"]  # FIXME: HARDCODED - Required directories hardcoded
        dir_checks = {{}}
        for req_dir in required_dirs:
            dir_path = project_path / req_dir
            exists = dir_path.exists() and dir_path.is_dir()
            dir_checks[req_dir] = {{"exists": exists}}
            if not exists:
                all_passed = False
                
        checks["directories"] = dir_checks
        
        # Check project configuration
        config_file = project_path / ".specify" / "config.toml"  # FIXME: HARDCODED - Config file path hardcoded
        config_exists = config_file.exists()
        checks["config"] = {{
            "exists": config_exists,
            "path": str(config_file),
            "message": "Project configuration found" if config_exists else "Project configuration missing"
        }}
        
        return all_passed, checks
        
    except Exception as e:
        return False, {{"error": str(e)}}


def main():
    """Main entry point.""" 
    parser = argparse.ArgumentParser(description="Check project prerequisites")
    parser.add_argument("--path", type=Path, default=Path.cwd(), help="Project path (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    success, result = check_prerequisites(args.path, args.json)
    
    if args.json:
        print(json.dumps(result))
    else:
        if success:
            print("✅ All prerequisites passed")
        else:
            print("❌ Some prerequisites failed")
            
        # Print check details
        for check_name, check_result in result.items():
            if check_name == "error":
                print(f"Error: {{check_result}}")
            elif isinstance(check_result, dict):
                if "passed" in check_result:
                    status = "✅" if check_result["passed"] else "❌"
                    message = check_result.get("message", "")
                    print(f"{{status}} {{check_name}}: {{message}}")
                elif check_name == "directories":
                    for dir_name, dir_result in check_result.items():
                        status = "✅" if dir_result.get("exists", False) else "❌"
                        print(f"{{status}} Directory {{dir_name}}: {{'exists' if dir_result.get('exists') else 'missing'}}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
'''

    def _generate_generic_script(
        self, template: GranularTemplate, context: TemplateContext
    ) -> str:
        """Generate generic script content"""
        return f'''#!/usr/bin/env python3
"""
{template.name.replace("-", " ").title()} script.
Generated by SpecifyX init command on {context.creation_date} for {context.ai_assistant}.
Project: {context.project_name}
"""

import argparse
import json
import sys
from pathlib import Path

# Import SpecifyX utilities for consistency
try:
    from specify_cli.services import ConfigService
    from specify_cli.utils.validators import validate_git_repository
except ImportError:
    # Fallback if running outside SpecifyX context
    print("Warning: SpecifyX utilities not available, using basic implementation", file=sys.stderr)
    ConfigService = None
    validate_git_repository = lambda x: (True, None)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="{template.name.replace("-", " ").title()} script")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    result = {{"script": "{template.name}", "project": "{context.project_name}"}}
    
    if args.json:
        print(json.dumps(result))
    else:
        print(f"Running {template.name} for project {context.project_name}")


if __name__ == "__main__":
    main()
'''

    def _set_single_script_permissions(self, script: GeneratedScript) -> bool:
        """Set executable permissions for a single script"""
        try:
            target_path = script.target_path
            if not target_path.exists():
                return False

            # Get current permissions
            current_stat = target_path.stat()
            current_mode = current_stat.st_mode

            # Set executable permissions based on platform
            if os.name == "posix":
                # Unix-like systems: set 755 permissions (rwxr-xr-x)
                new_mode = (
                    current_mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                )  # User: rwx
                new_mode |= stat.S_IRGRP | stat.S_IXGRP  # Group: r-x
                new_mode |= stat.S_IROTH | stat.S_IXOTH  # Other: r-x
            else:
                # Windows: just ensure user has all permissions
                new_mode = current_mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

            target_path.chmod(new_mode)
            return True

        except Exception:
            return False

    def _validate_single_script(self, script: GeneratedScript) -> bool:
        """Validate syntax and imports for a single script"""
        try:
            if not script.target_path.exists():
                script.mark_validation_error("Script file does not exist")
                return False

            # Read script content
            try:
                content = script.target_path.read_text(encoding="utf-8")
            except Exception as e:
                script.mark_validation_error(f"Cannot read script file: {e}")
                return False

            # Validate Python syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                script.mark_validation_error(f"Python syntax error: {e}")
                return False

            # Check for required imports
            if not script.imports:
                script.mark_validation_error("No SpecifyX imports found")
                return False

            # Check that imports exist in content
            import_found = False
            for import_stmt in script.imports:
                # Check if any part of the import statement is in the content
                import_parts = (
                    import_stmt.replace("from ", "").replace("import ", "").split()
                )
                if any(
                    part in content for part in import_parts if part and len(part) > 3
                ):
                    import_found = True
                    break

            if not import_found:
                script.mark_validation_error(
                    "SpecifyX imports not found in script content"
                )
                return False

            # Check for main function or entry point
            if (
                "def main(" not in content
                and 'if __name__ == "__main__"' not in content
            ):
                script.mark_validation_error("No main entry point found")
                return False

            return True

        except Exception as e:
            script.mark_validation_error(f"Validation failed: {e}")
            return False

    def _test_single_script_execution(self, script: GeneratedScript) -> bool:
        """Test execution of a single script"""
        try:
            if not script.target_path.exists():
                return False

            # Test Python syntax compilation
            content = script.target_path.read_text(encoding="utf-8")
            try:
                compile(content, str(script.target_path), "exec")
                return True
            except SyntaxError:
                return False

        except Exception:
            return False

    def _extract_script_imports(self, content: str) -> List[str]:
        """Extract SpecifyX import statements from script content"""
        imports = []

        # Find import lines that reference specify_cli
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if (
                line.startswith("from specify_cli")
                or line.startswith("import specify_cli")
            ) and "specify_cli" in line:
                imports.append(line)

        return imports

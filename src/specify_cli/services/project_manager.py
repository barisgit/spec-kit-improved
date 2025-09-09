"""
Project Manager service for orchestrating project initialization workflow.

This service coordinates other services (TemplateService, ConfigService, GitService,
DownloadService) to provide a complete project initialization experience.
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console

from ..models.config import BranchNamingConfig, ProjectConfig, TemplateConfig
from ..models.project import (
    ProjectInitOptions,
    ProjectInitResult,
    ProjectInitStep,
    TemplateContext,
)
from ..models.script import GeneratedScript
from ..models.template import TemplatePackage
from .config_service import ConfigService
from .download_service import DownloadService
from .git_service import GitService
from .script_generation_service import ScriptGenerationService
from .template_service import TemplateService


class ProjectManager(ABC):
    """Abstract base class for project management operations."""

    @abstractmethod
    def initialize_project(self, options: ProjectInitOptions) -> ProjectInitResult:
        """Initialize a new project with the given options."""
        pass

    @abstractmethod
    def validate_project_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """Validate project name according to project naming rules."""
        pass

    @abstractmethod
    def validate_project_directory(
        self, path: Path, use_current_dir: bool
    ) -> Tuple[bool, Optional[str]]:
        """Validate project directory for initialization."""
        pass

    @abstractmethod
    def setup_project_structure(self, project_path: Path, ai_assistant: str) -> bool:
        """Setup basic project structure and directories."""
        pass

    @abstractmethod
    def configure_branch_naming(
        self, project_path: Path, interactive: bool = True
    ) -> bool:
        """Configure branch naming patterns for the project."""
        pass

    @abstractmethod
    def migrate_existing_project(self, project_path: Path) -> bool:
        """Migrate an existing project to use spec-kit structure."""
        pass

    @abstractmethod
    def get_project_info(self, project_path: Path) -> Optional[Dict]:
        """Get information about an existing project."""
        pass

    @abstractmethod
    def cleanup_failed_init(
        self, project_path: Path, completed_steps: List[ProjectInitStep]
    ) -> bool:
        """Clean up after a failed initialization attempt."""
        pass

    @abstractmethod
    def generate_python_scripts(
        self, project_config: ProjectConfig, project_path: Path
    ) -> List[GeneratedScript]:
        """Generate Python scripts from templates with SpecifyX utility access."""
        pass


class SpecifyProjectManager(ProjectManager):
    """Default implementation of ProjectManager using dependency injection."""

    def __init__(
        self,
        template_service: Optional[TemplateService] = None,
        config_service: Optional[ConfigService] = None,
        git_service: Optional[GitService] = None,
        download_service: Optional[DownloadService] = None,
        script_generation_service: Optional[ScriptGenerationService] = None,
    ):
        """Initialize with service dependencies.

        Args:
            template_service: Service for template operations
            config_service: Service for configuration management
            git_service: Service for git operations
            download_service: Service for downloading templates
        """
        # Use default implementations if not provided
        if template_service is None:
            from .template_service import JinjaTemplateService

            template_service = JinjaTemplateService()

        if config_service is None:
            from .config_service import TomlConfigService

            config_service = TomlConfigService()

        if git_service is None:
            from .git_service import CommandLineGitService

            git_service = CommandLineGitService()

        if download_service is None:
            from .download_service import HttpxDownloadService

            download_service = HttpxDownloadService()

        self._template_service = template_service
        self._config_service = config_service
        self._git_service = git_service
        self._download_service = download_service
        
        # Initialize script generation service
        if script_generation_service is None:
            script_generation_service = ScriptGenerationService(self._template_service)
        self._script_generation_service = script_generation_service
        
        self._console = Console()

    def initialize_project(self, options: ProjectInitOptions) -> ProjectInitResult:
        """Initialize a new project with the given options."""
        completed_steps = []
        warnings = []
        project_path: Path = Path.cwd()

        try:
            # Step 1: Validation
            if options.use_current_dir:
                project_path = Path.cwd()
                if options.project_name:
                    warnings.append("Project name ignored when using current directory")
            else:
                if not options.project_name:
                    return ProjectInitResult(
                        success=False,
                        project_path=Path.cwd(),
                        error_message="Project name is required when not using current directory",
                    )

                # Validate project name
                is_valid, error = self.validate_project_name(options.project_name)
                if not is_valid:
                    return ProjectInitResult(
                        success=False,
                        project_path=Path.cwd(),
                        error_message=f"Invalid project name: {error}",
                    )

                project_path = Path.cwd() / options.project_name

            # Validate directory
            is_valid, error = self.validate_project_directory(
                project_path, options.use_current_dir
            )
            if not is_valid:
                return ProjectInitResult(
                    success=False,
                    project_path=project_path,
                    error_message=f"Directory validation failed: {error}",
                )

            completed_steps.append(ProjectInitStep.VALIDATION)

            # Step 2: Create directory if needed
            if not options.use_current_dir:
                project_path.mkdir(parents=True, exist_ok=True)
                completed_steps.append(ProjectInitStep.DIRECTORY_CREATION)

            # Step 3: Setup project structure
            if not self.setup_project_structure(project_path, options.ai_assistant):
                return ProjectInitResult(
                    success=False,
                    project_path=project_path,
                    completed_steps=completed_steps,
                    error_message="Failed to setup project structure",
                )
            completed_steps.append(ProjectInitStep.STRUCTURE_SETUP)

            # Step 4: Initialize git repository (if not skipped)
            if not options.skip_git:
                if not self._git_service.is_git_repository(project_path):
                    if self._git_service.init_repository(project_path):
                        completed_steps.append(ProjectInitStep.GIT_INIT)
                    else:
                        warnings.append("Failed to initialize git repository")
                else:
                    warnings.append("Directory is already a git repository")

            # Step 5: Create project configuration
            # Use provided branch naming config or create simple default
            branch_naming = options.branch_naming_config
            if not branch_naming:
                # Simple fallback default - should rarely be used since UI provides the config
                branch_naming = BranchNamingConfig()
                    
            config = ProjectConfig(
                name=options.project_name or project_path.name,
                branch_naming=branch_naming,
                template_settings=TemplateConfig(ai_assistant=options.ai_assistant),
            )

            if self._config_service.save_project_config(project_path, config):
                completed_steps.append(ProjectInitStep.CONFIG_SAVE)
            else:
                warnings.append("Failed to save project configuration")

            # Step 6: Apply template package system
            context = TemplateContext.create_default(
                project_name=options.project_name or project_path.name
            )
            context.ai_assistant = options.ai_assistant
            context.project_path = project_path
            context.branch_naming_config = config.branch_naming
            
            # Set AI-specific target paths for templates
            context.target_paths = self._build_ai_specific_target_paths(options.ai_assistant, project_path)
            
            try:
                # Use enhanced template package system
                template_package = self._create_template_package(options.ai_assistant)
                
                # Render template package
                render_results = self._template_service.render_template_package(
                    template_package, context
                )
                
                # Write rendered templates to disk
                written_files = self._write_template_results(
                    render_results, project_path
                )
                
                if written_files:
                    completed_steps.append(ProjectInitStep.TEMPLATE_RENDER)
                else:
                    warnings.append("No templates were rendered")
                    
            except Exception as e:
                warnings.append(f"Template package rendering failed: {str(e)}")

            # Step 7: Create initial branch (if git is enabled and branch pattern is configured)
            if not options.skip_git and self._git_service.is_git_repository(
                project_path
            ):
                branch_context = {"feature_name": "initial-setup"}
                branch_name = self._config_service.expand_branch_name(
                    config.branch_naming.default_pattern, branch_context
                )
                if self._git_service.create_branch(branch_name, project_path):
                    completed_steps.append(ProjectInitStep.BRANCH_CREATION)
                else:
                    warnings.append(f"Failed to create initial branch: {branch_name}")

            # Step 8: Generate Python scripts
            try:
                generated_scripts = self._script_generation_service.generate_scripts_from_templates(
                    context, project_path / ".specify" / "scripts", options.ai_assistant
                )
                
                if generated_scripts:
                    # Set executable permissions
                    permissions_success = self._script_generation_service.set_script_permissions(generated_scripts)
                    if not permissions_success:
                        warnings.append("Failed to set script permissions")
                        
                    # Validate scripts
                    validation_success = self._script_generation_service.validate_script_imports(generated_scripts)
                    if not validation_success:
                        warnings.append("Script validation failed")
                        
                    completed_steps.append(ProjectInitStep.FINALIZATION)
                else:
                    warnings.append("No scripts were generated")
                    
            except Exception as e:
                warnings.append(f"Script generation failed: {str(e)}")
                completed_steps.append(ProjectInitStep.FINALIZATION)

            return ProjectInitResult(
                success=True,
                project_path=project_path,
                completed_steps=completed_steps,
                warnings=warnings if warnings else None,
            )

        except Exception as e:
            return ProjectInitResult(
                success=False,
                project_path=project_path,
                completed_steps=completed_steps,
                error_message=f"Project initialization failed: {str(e)}",
            )

    def validate_project_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """Validate project name according to project naming rules."""
        if not name:
            return False, "Project name cannot be empty"

        if name.strip() != name:
            return False, "Project name cannot have leading or trailing whitespace"

        if len(name.strip()) == 0:
            return False, "Project name cannot be only whitespace"

        # Check for invalid characters
        if not re.match(r"^[a-z0-9_-]+$", name):
            return (
                False,
                "Project name must only contain lowercase letters, numbers, hyphens, and underscores",
            )

        # Check for invalid patterns
        if name.startswith("-") or name.endswith("-"):
            return False, "Project name cannot start or end with a hyphen"

        if name.startswith("_") or name.endswith("_"):
            return False, "Project name cannot start or end with an underscore"

        # Check length
        if len(name) < 1:
            return False, "Project name must be at least 1 character long"

        if len(name) > 100:
            return False, "Project name cannot be longer than 100 characters"

        # Disallow certain patterns
        if "/" in name or "\\" in name:
            return False, "Project name cannot contain slashes"

        if ":" in name:
            return False, "Project name cannot contain colons"

        if " " in name:
            return False, "Project name cannot contain spaces"

        if "." in name:
            return False, "Project name cannot contain dots"

        # Disallow uppercase letters
        if name != name.lower():
            return False, "Project name must be lowercase"

        return True, None

    def validate_project_directory(
        self, path: Path, use_current_dir: bool
    ) -> Tuple[bool, Optional[str]]:
        """Validate project directory for initialization."""
        if use_current_dir:
            # Current directory validation
            if not path.exists():
                return False, "Current directory does not exist"

            if not path.is_dir():
                return False, "Path is not a directory"

            # Check if already initialized
            if (path / ".specify").exists():
                return False, "Directory is already initialized as a spec-kit project"

            return True, None

        else:
            # New project directory validation
            if path.exists():
                if not path.is_dir():
                    return False, f"Path exists but is not a directory: {path}"

                # Check if directory is empty
                try:
                    if any(path.iterdir()):
                        return False, f"Directory is not empty: {path}"
                except PermissionError:
                    return False, f"Permission denied accessing directory: {path}"

                # Check if already initialized
                if (path / ".specify").exists():
                    return (
                        False,
                        "Directory is already initialized as a spec-kit project",
                    )

            # Check if parent directory exists and is writable
            parent = path.parent
            if not parent.exists():
                return False, f"Parent directory does not exist: {parent}"

            if not parent.is_dir():
                return False, f"Parent path is not a directory: {parent}"

            try:
                # Test if we can write to parent directory
                test_file = parent / ".specify_test"
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError):
                return False, f"No write permission to parent directory: {parent}"

            return True, None

    def setup_project_structure(self, project_path: Path, ai_assistant: str) -> bool:
        """Setup basic project structure and directories."""
        try:
            # Create .specify directory and subdirectories
            specify_dir = project_path / ".specify"
            specify_dir.mkdir(exist_ok=True)
            (specify_dir / "templates").mkdir(exist_ok=True)
            (specify_dir / "scripts").mkdir(exist_ok=True)
            (specify_dir / "memory").mkdir(exist_ok=True)

            # Create AI-specific directories
            if ai_assistant == "claude":
                claude_dir = project_path / ".claude"
                claude_dir.mkdir(exist_ok=True)
                (claude_dir / "commands").mkdir(exist_ok=True)
            elif ai_assistant == "gemini":
                gemini_dir = project_path / ".gemini"  
                gemini_dir.mkdir(exist_ok=True)
                (gemini_dir / "commands").mkdir(exist_ok=True)
            elif ai_assistant == "copilot":
                copilot_dir = project_path / ".github"
                copilot_dir.mkdir(exist_ok=True)
                (copilot_dir / "copilot").mkdir(exist_ok=True)

            # Create basic spec directory structure
            specs_dir = project_path / "specs"
            specs_dir.mkdir(exist_ok=True)

            # Create basic README if it doesn't exist
            readme_path = project_path / "README.md"
            if not readme_path.exists():
                readme_content = f"# {project_path.name}\n\nProject initialized with spec-kit for {ai_assistant}.\n"
                readme_path.write_text(readme_content)

            return True

        except Exception as e:
            self._console.print(f"[red]Failed to setup project structure: {e}[/red]")
            return False

    def configure_branch_naming(
        self, project_path: Path, interactive: bool = True
    ) -> bool:
        """Configure branch naming patterns for the project."""
        try:
            # Load existing config or create default
            config = self._config_service.load_project_config(project_path)
            if config is None:
                config = ProjectConfig(
                    name=project_path.name,
                    branch_naming=BranchNamingConfig(
                        default_pattern="001-feature-{feature_name}"
                    ),
                    template_settings=TemplateConfig(ai_assistant="claude"),
                )

            if interactive:
                # In a real implementation, this would prompt the user
                # For testing purposes, we'll use non-interactive defaults
                pass

            # Save updated configuration
            return self._config_service.save_project_config(project_path, config)

        except Exception as e:
            self._console.print(f"[red]Failed to configure branch naming: {e}[/red]")
            return False

    def migrate_existing_project(self, project_path: Path) -> bool:
        """Migrate an existing project to use spec-kit structure."""
        try:
            if not project_path.exists() or not project_path.is_dir():
                return False

            # Setup spec-kit structure in existing project
            return self.setup_project_structure(project_path, "claude")

        except Exception as e:
            self._console.print(f"[red]Failed to migrate project: {e}[/red]")
            return False

    def get_project_info(self, project_path: Path) -> Optional[Dict]:
        """Get information about an existing project."""
        try:
            if not project_path.exists() or not project_path.is_dir():
                return None

            info = {
                "path": str(project_path),
                "name": project_path.name,
                "is_spec_project": (project_path / ".specify").exists(),
                "is_git_repo": self._git_service.is_git_repository(project_path),
            }

            # Add config information if available
            config = self._config_service.load_project_config(project_path)
            if config:
                info.update(
                    {
                        "ai_assistant": config.template_settings.ai_assistant,
                        "branch_pattern": config.branch_naming.default_pattern,
                    }
                )

            # Add git information if available
            if info["is_git_repo"]:
                current_branch = self._git_service.get_current_branch(project_path)
                if current_branch:
                    info["current_branch"] = current_branch

                remote_url = self._git_service.get_remote_url(project_path)
                if remote_url:
                    info["remote_url"] = remote_url

            return info

        except Exception:
            return None

    def cleanup_failed_init(
        self, project_path: Path, completed_steps: List[ProjectInitStep]
    ) -> bool:
        """Clean up after a failed initialization attempt."""
        try:
            # Only clean up what was created during initialization
            if ProjectInitStep.STRUCTURE_SETUP in completed_steps:
                # Remove .specify directory
                specify_dir = project_path / ".specify"
                if specify_dir.exists():
                    import shutil

                    shutil.rmtree(specify_dir)

            if (
                ProjectInitStep.DIRECTORY_CREATION in completed_steps
                and project_path.exists()
                and project_path != Path.cwd()
            ):
                # Remove the entire project directory if it was created during init
                import shutil

                shutil.rmtree(project_path)

            return True

        except Exception as e:
            self._console.print(
                f"[red]Failed to cleanup failed initialization: {e}[/red]"
            )
            return False

    def generate_python_scripts(
        self, project_config: ProjectConfig, project_path: Path
    ) -> List[GeneratedScript]:
        """Generate Python scripts from templates with SpecifyX utility access."""
        try:
            # Create template context from project config
            context = TemplateContext(
                project_name=project_config.name,
                ai_assistant=project_config.template_settings.ai_assistant,
                branch_naming_config=project_config.branch_naming,
                config_directory=".specify",
                project_path=project_path,
                target_paths={}
            )
            
            # Generate scripts
            scripts_dir = project_path / ".specify" / "scripts"
            generated_scripts = self._script_generation_service.generate_scripts_from_templates(
                context, scripts_dir, project_config.template_settings.ai_assistant
            )
            
            # Set permissions and validate
            if generated_scripts:
                self._script_generation_service.set_script_permissions(generated_scripts)
                self._script_generation_service.validate_script_imports(generated_scripts)
                
            return generated_scripts
            
        except Exception as e:
            self._console.print(f"[red]Failed to generate Python scripts: {e}[/red]")
            return []
            
    def _create_template_package(self, ai_assistant: str) -> TemplatePackage:
        """Create template package for the given AI assistant."""
        # Discover templates from package resources
        all_templates = self._template_service.discover_templates()
        
        # Filter templates compatible with AI assistant
        compatible_templates = [
            template for template in all_templates
            if template.is_ai_specific_for(ai_assistant)
        ]
        
        # Create output structure mapping
        output_structure = {}
        for template in compatible_templates:
            target_dir = str(Path(template.target_path).parent)
            if target_dir not in output_structure:
                output_structure[target_dir] = []
            output_structure[target_dir].append(template.name)
            
        return TemplatePackage(
            ai_assistant=ai_assistant,
            templates=compatible_templates,
            output_structure=output_structure
        )
        
    def _write_template_results(
        self, render_results: List, project_path: Path
    ) -> List[Path]:
        """Write template render results to disk."""
        from ..utils.file_operations import FileOperations
        
        written_files = []
        
        for result in render_results:
            if result.success:
                try:
                    # Get absolute target path
                    if Path(result.target_path).is_absolute():
                        target_path = Path(result.target_path)
                    else:
                        target_path = project_path / result.target_path
                    
                    # Ensure parent directory exists 
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Use FileOperations for proper permission handling
                    success = FileOperations.write_file_with_permissions(
                        target_path,
                        result.content,
                        executable=result.template.executable
                    )
                    
                    if success:
                        # Mark template as written
                        result.template.transition_to_written()
                        written_files.append(target_path)
                    else:
                        self._console.print(
                            f"[red]Failed to write {result.target_path}[/red]"
                        )
                        
                except Exception as e:
                    self._console.print(
                        f"[red]Failed to write {result.target_path}: {e}[/red]"
                    )
                    continue
                    
        return written_files
    
    def _build_ai_specific_target_paths(self, ai_assistant: str, project_path: Path) -> Dict[str, Path]:
        """Build AI-specific target paths for templates"""
        target_paths = {}
        
        # Commands directory based on AI assistant
        if ai_assistant == "claude":
            commands_base = project_path / ".claude" / "commands"
        elif ai_assistant == "gemini":
            commands_base = project_path / ".gemini" / "commands"
        elif ai_assistant == "copilot":
            commands_base = project_path / ".github" / "copilot"
        else:
            commands_base = project_path / ".claude" / "commands"  # Default
        
        # Common target paths mapping template names to their output locations
        target_paths.update({
            # Command templates (should be .md files)
            "specify.j2": commands_base / "specify.md",
            "plan.j2": commands_base / "plan.md", 
            "tasks.j2": commands_base / "tasks.md",
            
            # Memory templates
            "constitution.j2": project_path / ".specify" / "memory" / "constitution.md",
            
            # Script templates
            "create-feature.j2": project_path / ".specify" / "scripts" / "create-feature.py",
            "setup-plan.j2": project_path / ".specify" / "scripts" / "setup-plan.py",
            "check-prerequisites.j2": project_path / ".specify" / "scripts" / "check-prerequisites.py",
            
            # Runtime templates
            "spec-template.j2": project_path / ".specify" / "templates" / "spec-template.j2",
            "plan-template.j2": project_path / ".specify" / "templates" / "plan-template.j2",
        })
        
        return target_paths

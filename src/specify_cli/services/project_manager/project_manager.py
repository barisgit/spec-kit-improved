"""
Project Manager service with dynamic, configurable template rendering.

100% type safe, 100% configurable, 0% hardcoded.
"""

import logging
from pathlib import Path

# Import types for template service integration
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console

from specify_cli.models.config import BranchNamingConfig, ProjectConfig, TemplateConfig
from specify_cli.models.defaults import PATH_DEFAULTS
from specify_cli.models.project import (
    ProjectInitOptions,
    ProjectInitResult,
    ProjectInitStep,
    TemplateContext,
)
from specify_cli.services.config_service import ConfigService
from specify_cli.services.git_service import GitService

# Import types that we need at runtime
from specify_cli.services.template_service import RenderResult, TemplateFolderMapping
from specify_cli.utils.validators import ValidationError, Validators

if TYPE_CHECKING:
    from specify_cli.services.template_service import JinjaTemplateService


class ProjectManager:
    """Project manager with fully configurable template system"""

    def __init__(
        self,
        config_service: Optional[ConfigService] = None,
        git_service: Optional[GitService] = None,
        folder_mappings: Optional[List[TemplateFolderMapping]] = None,
        template_service: Optional["JinjaTemplateService"] = None,
    ):
        """Initialize with optional service dependencies and custom configurations"""
        # Use provided services or create defaults
        if config_service is None:
            from specify_cli.services.config_service import TomlConfigService

            config_service = TomlConfigService()

        if git_service is None:
            from specify_cli.services.git_service import CommandLineGitService

            git_service = CommandLineGitService()

        if template_service is None:
            from specify_cli.services.template_service import JinjaTemplateService

            template_service = JinjaTemplateService()

        self._config_service = config_service
        self._git_service = git_service
        self._template_service = template_service
        self._console = Console()

        # Use custom configurations or defaults (will be set dynamically)
        self._custom_folder_mappings = folder_mappings

    def _get_default_folder_mappings(
        self, ai_assistant: str = "claude"
    ) -> List[TemplateFolderMapping]:
        """Get default folder mappings for the specified AI assistant using configuration."""
        results = PATH_DEFAULTS.get_folder_mappings(ai_assistant)

        mappings: List[TemplateFolderMapping] = []
        for result in results:
            exec_extensions = (
                PATH_DEFAULTS.EXECUTABLE_EXTENSIONS
                if result.category == "scripts"
                else []
            )

            mappings.append(
                TemplateFolderMapping(
                    source=result.source_path,
                    target_pattern=result.target_path,
                    render=result.should_render,
                    executable_extensions=exec_extensions,
                )
            )

        return mappings

    def initialize_project(self, options: ProjectInitOptions) -> ProjectInitResult:
        """Initialize project with dynamic template rendering"""
        logging.info(f"Initializing project with AI: {options.ai_assistant}")
        completed_steps: List[ProjectInitStep] = []
        warnings: List[str] = []

        try:
            # Determine project path
            project_path = self._resolve_project_path(options)
            logging.debug(f"Project path resolved: {project_path}")

            # Validate project
            is_valid, error = self._validate_project(project_path, options)
            if not is_valid:
                return ProjectInitResult(
                    success=False, project_path=project_path, error_message=error
                )
            completed_steps.append(ProjectInitStep.VALIDATION)

            # Create directories
            if not options.use_current_dir:
                project_path.mkdir(parents=True, exist_ok=True)
                completed_steps.append(ProjectInitStep.DIRECTORY_CREATION)

            # Create basic structure
            self._create_basic_structure(project_path, options.ai_assistant)
            completed_steps.append(ProjectInitStep.STRUCTURE_SETUP)

            # Initialize git if needed
            if not options.skip_git:
                self._init_git(project_path, completed_steps, warnings)

            # Save configuration
            config = self._create_project_config(options, project_path)
            if self._config_service.save_project_config(project_path, config):
                completed_steps.append(ProjectInitStep.CONFIG_SAVE)

            # Render templates dynamically using full TemplateContext
            context = TemplateContext(
                project_name=options.project_name or project_path.name,
                ai_assistant=options.ai_assistant,
                project_path=project_path,
                branch_naming_config=options.branch_naming_config
                or BranchNamingConfig(),
            )

            render_result = self._render_all_templates(context)
            if render_result.success:
                completed_steps.append(ProjectInitStep.TEMPLATE_RENDER)
            else:
                warnings.extend(render_result.errors)

            # Create initial branch if git enabled
            if not options.skip_git and self._git_service.is_git_repository(
                project_path
            ):
                self._create_initial_branch(
                    config, project_path, completed_steps, warnings
                )

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
                project_path=Path.cwd(),
                completed_steps=completed_steps,
                error_message=str(e),
            )

    def _render_all_templates(
        self, context: TemplateContext, verbose: bool = False
    ) -> RenderResult:
        """Render all templates using JinjaTemplateService"""
        # Get folder mappings dynamically based on AI assistant
        folder_mappings = (
            self._custom_folder_mappings
            or self._get_default_folder_mappings(context.ai_assistant)
        )

        logging.debug(f"folder_mappings count: {len(folder_mappings)}")
        for i, mapping in enumerate(folder_mappings):
            logging.debug(
                f"mapping {i}: source={mapping.source}, target={mapping.target_pattern}"
            )

        result = self._template_service.render_all_templates_from_mappings(
            folder_mappings, context, verbose=verbose
        )

        if result.success:
            logging.debug("render result: success")
        else:
            logging.error("Template rendering failed")
            for error in result.errors:
                logging.error(f"Template error: {error}")

        return result

    def _resolve_project_path(self, options: ProjectInitOptions) -> Path:
        """Resolve project path from options"""
        if options.use_current_dir:
            return Path.cwd()
        elif options.project_name:
            return Path.cwd() / options.project_name
        else:
            raise ValueError("Project name required when not using current directory")

    def _validate_project(
        self, project_path: Path, options: ProjectInitOptions
    ) -> tuple[bool, Optional[str]]:
        """Validate project directory"""
        if options.use_current_dir:
            # Only check for existing initialization if force is not used
            if self.is_project_initialized(project_path) and not options.force:
                return False, "Directory already initialized as spec-kit project"
        else:
            if project_path.exists() and any(project_path.iterdir()):
                return False, f"Directory not empty: {project_path}"

        return True, None

    def is_project_initialized(self, project_path: Path) -> bool:
        """Check if a directory is already initialized as a SpecifyX project"""
        return (project_path / ".specify").exists()

    def _create_basic_structure(self, project_path: Path, ai_assistant: str) -> None:
        """Create basic project structure"""
        # Get dynamic project structure paths
        basic_dirs = PATH_DEFAULTS.get_project_structure_paths(ai_assistant)

        # Create all required directories
        for dir_path in basic_dirs:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Create specs directory (always needed)
        (project_path / "specs").mkdir(exist_ok=True)

        # Create basic README if doesn't exist
        readme = project_path / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {project_path.name}\n\nProject initialized with spec-kit for {ai_assistant}.\n"
            )

    def _init_git(
        self,
        project_path: Path,
        completed_steps: List[ProjectInitStep],
        warnings: List[str],
    ) -> None:
        """Initialize git repository if needed"""
        if not self._git_service.is_git_repository(project_path):
            if self._git_service.init_repository(project_path):
                completed_steps.append(ProjectInitStep.GIT_INIT)
            else:
                warnings.append("Failed to initialize git repository")
        else:
            warnings.append("Directory is already a git repository")

    def _create_project_config(
        self, options: ProjectInitOptions, project_path: Path
    ) -> ProjectConfig:
        """Create project configuration"""
        branch_naming = options.branch_naming_config or BranchNamingConfig()

        return ProjectConfig(
            name=options.project_name or project_path.name,
            branch_naming=branch_naming,
            template_settings=TemplateConfig(ai_assistant=options.ai_assistant),
        )

    def _create_initial_branch(
        self,
        _config: ProjectConfig,
        project_path: Path,
        completed_steps: List[ProjectInitStep],
        warnings: List[str],
    ) -> None:
        """Create initial git branch"""
        # Get default context variables
        PATH_DEFAULTS.get_default_context_vars(project_path.name)

        branch_name = "main"

        if self._git_service.create_branch(branch_name, project_path):
            completed_steps.append(ProjectInitStep.BRANCH_CREATION)
        else:
            warnings.append(f"Failed to create initial branch: {branch_name}")

    def validate_project_name(self, name: str) -> tuple[bool, Optional[str]]:
        """Validate project name using existing Validators infrastructure"""
        try:
            Validators.project_name(name)
            return True, None
        except ValidationError as e:
            return False, str(e)

    def validate_project_directory(
        self, project_path: Path, use_current_dir: bool
    ) -> tuple[bool, Optional[str]]:
        """Validate project directory using existing Validators infrastructure"""
        try:
            if use_current_dir:
                # For current directory, just check if it's a valid directory
                Validators.directory_path(project_path, must_exist=True)
                # Additional check for already initialized
                if (project_path / ".specify").exists():
                    return False, "Directory already initialized as spec-kit project"
            else:
                # For new directory, check if it can be created or is empty
                Validators.directory_path(project_path, must_be_empty=True)
            return True, None
        except ValidationError as e:
            return False, str(e)

    def setup_project_structure(self, project_path: Path, ai_assistant: str) -> bool:
        """Set up basic project structure using existing infrastructure"""
        logging.debug(
            f"Setting up project structure for {project_path} with AI: {ai_assistant}"
        )
        try:
            self._create_basic_structure(project_path, ai_assistant)
            logging.debug(f"Successfully set up project structure for {project_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to setup project structure for {project_path}: {e}")
            return False

    def configure_branch_naming(
        self, project_path: Path, interactive: bool = False
    ) -> bool:
        """Configure branch naming using existing config service"""
        logging.debug(
            f"Configuring branch naming for {project_path} (interactive: {interactive})"
        )
        try:
            # Load existing config or create default
            config = self._config_service.load_project_config(project_path)
            if config is None:
                logging.debug(
                    f"No existing config found, creating default for {project_path}"
                )
                config = ProjectConfig(name=project_path.name)
            else:
                logging.debug(f"Loaded existing config for {project_path}")

            # In non-interactive mode, just ensure config exists
            if not interactive:
                logging.debug(
                    f"Saving config in non-interactive mode for {project_path}"
                )
                return self._config_service.save_project_config(project_path, config)

            # In interactive mode, would prompt user (not implemented in tests)
            logging.debug(f"Saving config in interactive mode for {project_path}")
            return self._config_service.save_project_config(project_path, config)
        except Exception as e:
            logging.error(f"Failed to configure branch naming for {project_path}: {e}")
            return False

    def migrate_existing_project(self, project_path: Path) -> bool:
        """Migrate existing project using existing infrastructure"""
        try:
            # Check if already migrated
            if (project_path / ".specify").exists():
                return True

            # Create basic structure
            self._create_basic_structure(project_path, "claude")

            # Create default config
            config = ProjectConfig(name=project_path.name)
            return self._config_service.save_project_config(project_path, config)
        except Exception as e:
            logging.error(f"Failed to migrate existing project: {e}")
            return False

    def get_project_info(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Get project information using existing config service"""
        try:
            if not project_path.exists():
                return None

            config = self._config_service.load_project_config(project_path)
            if config is None:
                return None

            return {
                "name": config.name,
                "ai_assistant": config.template_settings.ai_assistant,
                "branch_naming": config.branch_naming.to_dict(),
                "template_settings": config.template_settings.to_dict(),
                "path": str(project_path),
                "initialized": (project_path / ".specify").exists(),
            }
        except Exception as e:
            logging.error(f"Failed to get project info: {e}")
            return None

    def cleanup_failed_init(
        self, project_path: Path, completed_steps: List[ProjectInitStep]
    ) -> bool:
        """Clean up after failed initialization"""
        try:
            # Remove any created files/directories based on completed steps
            if (
                ProjectInitStep.DIRECTORY_CREATION in completed_steps
                and project_path.exists()
                and not any(project_path.iterdir())
            ):
                # Only remove if we created the directory and it's empty
                project_path.rmdir()

            if ProjectInitStep.STRUCTURE_SETUP in completed_steps:
                # Remove .specify directory if created
                specify_dir = project_path / ".specify"
                if specify_dir.exists():
                    import shutil

                    shutil.rmtree(specify_dir)

            if ProjectInitStep.CONFIG_SAVE in completed_steps:
                # Remove config file if created
                config_file = project_path / "config.toml"
                if config_file.exists():
                    config_file.unlink()

            return True
        except Exception as e:
            logging.error(f"Failed to cleanup failed init: {e}")
            return False

    def initialize_cross_platform_project(self, options: ProjectInitOptions) -> bool:
        """Initialize project with cross-platform compatibility.

        Args:
            options: Project initialization options

        Returns:
            True if successful, False otherwise
        """
        try:
            # Resolve project path from options (same logic as initialize_project)
            project_path = self._resolve_project_path(options)

            # Create cross-platform directory structure
            if not options.use_current_dir:
                project_path.mkdir(parents=True, exist_ok=True)

            # Initialize with standard project structure
            result = self.initialize_project(options)
            return result.success
        except Exception:
            return False

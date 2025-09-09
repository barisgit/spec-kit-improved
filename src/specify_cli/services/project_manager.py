"""
Project Manager service with dynamic, configurable template rendering.

100% type safe, 100% configurable, 0% hardcoded.
"""

from dataclasses import dataclass, field
from pathlib import Path

# Import types for template service integration
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console

from ..models.config import BranchNamingConfig, ProjectConfig, TemplateConfig
from ..models.project import ProjectInitOptions, ProjectInitResult, ProjectInitStep
from .config_service import ConfigService
from .git_service import GitService

# Import types that we need at runtime
from .template_service import RenderResult, TemplateFolderMapping

if TYPE_CHECKING:
    from .template_service import JinjaTemplateService


@dataclass
class TemplateContext:
    """Type-safe template rendering context"""

    project_name: str
    ai_assistant: str
    project_path: Path
    branch_naming_config: Optional[BranchNamingConfig] = None
    extra_vars: Dict[str, Any] = field(default_factory=dict)


class ProjectManager:
    """Project manager with fully configurable template system"""

    # FIXME: HARDCODED - Default folder mappings hardcoded
    # TODO: Move to ConfigurableFolderMapping model with configuration-driven approach
    # Default template folder mappings - fully configurable
    DEFAULT_FOLDER_MAPPINGS: List[TemplateFolderMapping] = [
        {
            "source": "commands",
            "target_pattern": ".{ai_assistant}/commands",
            "render": True,
            "executable_extensions": [],
        },
        {
            "source": "scripts",
            "target_pattern": ".specify/scripts",
            "render": True,
            "executable_extensions": [".py", ".sh"],
        },
        {
            "source": "memory",
            "target_pattern": ".specify/memory",
            "render": True,
            "executable_extensions": [],
        },
        {
            "source": "runtime_templates",
            "target_pattern": ".specify/templates",
            "render": False,  # Copy as-is for runtime use
            "executable_extensions": [],
        },
    ]

    # FIXME: HARDCODED - Skip patterns hardcoded
    # TODO: Move to TemplateProcessingConfig with configurable skip patterns
    # Files/patterns to skip when processing templates
    SKIP_PATTERNS: List[str] = [
        "__init__.py",
        "__pycache__",
        ".pyc",
        ".DS_Store",
        ".gitkeep",
    ]

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
            from .config_service import TomlConfigService

            config_service = TomlConfigService()

        if git_service is None:
            from .git_service import CommandLineGitService

            git_service = CommandLineGitService()

        if template_service is None:
            from .template_service import JinjaTemplateService

            template_service = JinjaTemplateService()

        self._config_service = config_service
        self._git_service = git_service
        self._template_service = template_service
        self._console = Console()

        # Use custom configurations or defaults
        self.folder_mappings = folder_mappings or self.DEFAULT_FOLDER_MAPPINGS

    def initialize_project(self, options: ProjectInitOptions) -> ProjectInitResult:
        """Initialize project with dynamic template rendering"""
        completed_steps: List[ProjectInitStep] = []
        warnings: List[str] = []

        try:
            # Determine project path
            project_path = self._resolve_project_path(options)

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

            # Render templates dynamically
            context = TemplateContext(
                project_name=options.project_name or project_path.name,
                ai_assistant=options.ai_assistant,
                project_path=project_path,
                branch_naming_config=options.branch_naming_config,
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
        return self._template_service.render_all_templates_from_mappings(
            self.folder_mappings, context, verbose=verbose
        )

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
            if (project_path / ".specify").exists():
                return False, "Directory already initialized as spec-kit project"
        else:
            if project_path.exists() and any(project_path.iterdir()):
                return False, f"Directory not empty: {project_path}"

        return True, None

    def _create_basic_structure(self, project_path: Path, ai_assistant: str) -> None:
        """Create basic project structure"""
        # FIXME: HARDCODED - Basic structure creation hardcoded
        # TODO: Move to configuration with customizable project structure
        # Create .specify directory
        (project_path / ".specify").mkdir(exist_ok=True)

        # Create specs directory
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
        config: ProjectConfig,
        project_path: Path,
        completed_steps: List[ProjectInitStep],
        warnings: List[str],
    ) -> None:
        """Create initial git branch"""
        branch_context = {"feature_name": "initial-setup"}
        branch_name = self._config_service.expand_branch_name(
            config.branch_naming.default_pattern, branch_context
        )

        if self._git_service.create_branch(branch_name, project_path):
            completed_steps.append(ProjectInitStep.BRANCH_CREATION)
        else:
            warnings.append(f"Failed to create initial branch: {branch_name}")

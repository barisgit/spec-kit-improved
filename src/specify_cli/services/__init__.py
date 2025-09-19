# Services package
from .assistant_management_service import AssistantManagementService
from .config_service import ConfigService, TomlConfigService
from .download_service import DownloadService, HttpxDownloadService
from .git_service import CommandLineGitService, GitService
from .project_manager import ProjectManager
from .script_discovery_service import ScriptDiscoveryService
from .script_execution_service import (
    ScriptExecutionService,
    SubprocessScriptExecutionService,
)
from .template_service import JinjaTemplateService, TemplateService

__all__ = [
    "AssistantManagementService",
    "ConfigService",
    "TomlConfigService",
    "GitService",
    "CommandLineGitService",
    "ProjectManager",
    "ScriptDiscoveryService",
    "TemplateService",
    "JinjaTemplateService",
    "DownloadService",
    "HttpxDownloadService",
    "ScriptExecutionService",
    "SubprocessScriptExecutionService",
]

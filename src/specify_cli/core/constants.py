"""Centralized constants for SpecifyX CLI.

All constants are organized in a tree-like structure for better organization and IDE hover support.
Access pattern: CONSTANTS.CATEGORY.NAME
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NetworkConstants:
    """Network and HTTP-related constants."""

    DEFAULT_REQUEST_TIMEOUT = 30
    """Default HTTP request timeout in seconds."""

    VERSION_CHECK_TIMEOUT = 10
    """Timeout for version check requests in seconds."""

    UPDATE_PROCESS_TIMEOUT = 300
    """Timeout for update subprocesses in seconds."""


@dataclass(frozen=True)
class DownloadConstants:
    """Download and file transfer constants."""

    DEFAULT_CHUNK_SIZE = 8192
    """Default chunk size for HTTP downloads in bytes."""

    DEFAULT_BRANCH = "main"
    """Default branch for repository operations."""

    EXPECTED_TEMPLATE_ASSETS = ["specifyx-templates", "spec-kit-template"]
    """Expected template asset names for validation."""

    SUPPORTED_ARCHIVE_FORMATS = [".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2"]
    """Supported archive file extensions."""


@dataclass(frozen=True)
class GitConstants:
    """Git configuration and operation constants."""

    DEFAULT_INITIAL_COMMIT = "Initial commit from SpecifyX template"
    """Default commit message for initial repository setup."""

    AUTOCRLF_WINDOWS = "true"
    """autocrlf value for Windows systems."""

    AUTOCRLF_UNIX = "false"
    """autocrlf value for Unix-like systems."""

    SAFECRLF_DEFAULT = "warn"
    """Default safecrlf value for line ending validation."""


@dataclass(frozen=True)
class ValidationConstants:
    """Input validation and constraint constants."""

    MAX_PROJECT_NAME_LENGTH = 50
    """Maximum allowed length for project names."""

    MAX_TEMPLATE_NAME_LENGTH = 100
    """Maximum allowed length for template names."""

    MAX_INJECTION_VALUE_LENGTH = 1000
    """Maximum length for injection point values to prevent template bloat."""


@dataclass(frozen=True)
class ApiConstants:
    """API endpoint and service constants."""

    GITHUB_API_BASE = "https://api.github.com"
    """Base URL for GitHub API endpoints."""

    PYPI_JSON_API = "https://pypi.org/pypi/{package_name}/json"
    """PyPI JSON API endpoint template for package information."""


@dataclass(frozen=True)
class FileConstants:
    """File and path-related constants."""

    EXPECTED_TEMPLATE_FILES = ["README.md", "CONSTITUTION.md"]
    """Expected files that should be present in template repositories."""

    TEMPLATE_J2_EXTENSION = ".j2"
    """Jinja2 template file extension."""

    PYTHON_EXTENSION = ".py"
    """Python source file extension."""

    PYTHON_CACHE_EXTENSION = ".pyc"
    """Python compiled bytecode file extension."""

    PYTHON_CACHE_DIR = "__pycache__"
    """Python cache directory name."""

    EXECUTABLE_PERMISSIONS = 0o755
    """File permissions for executable files."""

    REGULAR_FILE_PERMISSIONS = 0o644
    """File permissions for regular files."""

    # File extensions
    MARKDOWN_EXTENSION = ".md"
    """Markdown file extension."""

    TOML_EXTENSION = ".toml"
    """TOML configuration file extension."""

    JSON_EXTENSION = ".json"
    """JSON file extension."""

    SHELL_EXTENSION = ".sh"
    """Shell script file extension."""

    BATCH_EXTENSION = ".bat"
    """Windows batch file extension."""

    POWERSHELL_EXTENSION = ".ps1"
    """PowerShell script file extension."""

    # Common file patterns
    GITIGNORE_FILE = ".gitignore"
    """Git ignore file name."""

    README_FILE = "README.md"
    """Standard README file name."""


@dataclass(frozen=True)
class DirectoryConstants:
    """Directory and path-related constants."""

    # Project directories
    SPECIFY_DIR = ".specify"
    """SpecifyX configuration directory."""

    CLAUDE_DIR = ".claude"
    """Claude AI assistant directory."""

    GIT_DIR = ".git"
    """Git repository directory."""

    # SpecifyX subdirectories
    SPECIFY_SCRIPTS_DIR = ".specify/scripts"
    """SpecifyX scripts directory."""

    SPECIFY_TEMPLATES_DIR = ".specify/templates"
    """SpecifyX templates directory."""

    SPECIFY_MEMORY_DIR = ".specify/memory"
    """SpecifyX memory directory."""

    SPECIFY_AGENT_TEMPLATES_DIR = ".specify/agent-templates"
    """SpecifyX agent templates directory."""

    # Claude subdirectories
    CLAUDE_COMMANDS_DIR = ".claude/commands"
    """Claude commands directory."""

    CLAUDE_AGENTS_DIR = ".claude/agents"
    """Claude agents directory."""

    CLAUDE_DOC_DIR = ".claude/doc"
    """Claude documentation directory."""

    # Common config files
    SPECIFY_CONFIG_FILE = ".specify/config.toml"
    """SpecifyX configuration file path."""

    CLAUDE_CONFIG_FILE = ".claude/CLAUDE.md"
    """Claude configuration file path."""


@dataclass(frozen=True)
class PatternConstants:
    """Pattern matching and regex constants."""

    # Agent name extraction patterns
    AGENT_MD_J2_SUFFIX = ".md.j2"
    """Agent template file suffix."""

    AGENT_NAME_PATTERN = r"^[a-z][a-z0-9-]*[a-z0-9]$"
    """Valid agent name pattern."""

    # File skip patterns
    SKIP_PATTERNS = [
        "__pycache__",
        "*.pyc",
        ".DS_Store",
        "*.tmp",
        ".git",
        "__init__.py",
        "*.egg-info",
    ]
    """Default file patterns to skip during processing."""

    # Executable file patterns
    EXECUTABLE_EXTENSIONS = [".py", ".sh", ".bat", ".ps1"]
    """File extensions that should be made executable."""

    EXECUTABLE_PATH_PATTERNS = ["**/scripts/**", "**/bin/**"]
    """Path patterns that should be made executable."""

    EXECUTABLE_NAME_PATTERNS = ["run", "start", "stop", "deploy", "build", "test"]
    """Filename patterns that should be made executable."""

    # Template categories
    TEMPLATE_CATEGORIES = [
        "commands",
        "scripts",
        "memory",
        "runtime_templates",
        "context",
        "agent-prompts",
        "agent-templates",
    ]
    """Supported template categories."""


@dataclass(frozen=True)
class ErrorMessageConstants:
    """Common error message templates."""

    TEMPLATE_NOT_FOUND = "Template not found: {template_name}"
    """Template not found error message template."""

    TEMPLATE_CONTEXT_NONE = "Template context cannot be None"
    """Template context validation error."""

    TEMPLATE_NAME_EMPTY = "Template name cannot be empty"
    """Template name validation error."""

    FAILED_LOAD_ENVIRONMENT = "Failed to load template environment"
    """Template environment loading error."""

    TEMPLATE_SYNTAX_ERROR = "Template syntax error in '{template_name}': {error}"
    """Template syntax error message template."""

    FAILED_RENDER_TEMPLATE = "Failed to render template '{template_name}': {error}"
    """Template rendering error message template."""

    UNEXPECTED_TEMPLATE_ERROR = (
        "Unexpected error rendering template '{template_name}': {error}"
    )
    """Unexpected template error message template."""

    TEMPLATE_VALIDATION_ERROR = "Template syntax error: {error}"
    """Template validation error message template."""

    ERROR_VALIDATING_TEMPLATE = "Error validating template: {error}"
    """General template validation error."""


@dataclass(frozen=True)
class AssistantConstants:
    """AI assistant and injection point constants."""

    INJECTION_POINT_NAME_PATTERN = r"^assistant_[a-z][a-z0-9_]*[a-z0-9]$"
    """Regex pattern for valid injection point names (assistant_* with snake_case)."""


@dataclass(frozen=True)
class Constants:
    """Main constants container providing tree-like access to all constants."""

    NETWORK: NetworkConstants = field(default_factory=NetworkConstants)
    """Network and HTTP-related constants."""

    DOWNLOAD: DownloadConstants = field(default_factory=DownloadConstants)
    """Download and file transfer constants."""

    GIT: GitConstants = field(default_factory=GitConstants)
    """Git configuration and operation constants."""

    VALIDATION: ValidationConstants = field(default_factory=ValidationConstants)
    """Input validation and constraint constants."""

    API: ApiConstants = field(default_factory=ApiConstants)
    """API endpoint and service constants."""

    FILE: FileConstants = field(default_factory=FileConstants)
    """File and path-related constants."""

    DIRECTORY: DirectoryConstants = field(default_factory=DirectoryConstants)
    """Directory and path-related constants."""

    PATTERNS: PatternConstants = field(default_factory=PatternConstants)
    """Pattern matching and regex constants."""

    ERRORS: ErrorMessageConstants = field(default_factory=ErrorMessageConstants)
    """Common error message templates."""

    ASSISTANT: AssistantConstants = field(default_factory=AssistantConstants)
    """AI assistant and injection point constants."""


# Main constants instance for tree-like access
CONSTANTS = Constants()

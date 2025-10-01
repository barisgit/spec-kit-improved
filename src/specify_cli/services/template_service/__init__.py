# Import the core interface and implementation
from .interfaces import TemplateService
from .models import (
    RenderResult,
    TemplateChange,
    TemplateChangeType,
    TemplateDiff,
    TemplateFolderMapping,
    TemplateRenderResult,
)

# Import specialized service modules
from .template_comparator import TemplateComparator
from .template_context_processor import TemplateContextProcessor
from .template_discovery import TemplateDiscovery
from .template_file_operations import TemplateFileOperations
from .template_loader import TemplateLoader
from .template_renderer import TemplateRenderer
from .template_service import JinjaTemplateService, get_template_service
from .template_validator import TemplateValidator

__all__ = [
    # Core interfaces and implementations
    "TemplateService",
    "JinjaTemplateService",
    "get_template_service",
    # Data models and types
    "TemplateFolderMapping",
    "RenderResult",
    "TemplateRenderResult",
    "TemplateChange",
    "TemplateChangeType",
    "TemplateDiff",
    # Specialized service modules
    "TemplateLoader",
    "TemplateRenderer",
    "TemplateValidator",
    "TemplateComparator",
    "TemplateDiscovery",
    "TemplateContextProcessor",
    "TemplateFileOperations",
]

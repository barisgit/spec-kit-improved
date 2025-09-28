"""Template Registry Service for centralized template management."""

from .models import CategoryInfo, TemplateInfo, TemplateMetadata, ValidationResult
from .template_registry import TEMPLATE_REGISTRY, TemplateRegistryService

__all__ = [
    "TEMPLATE_REGISTRY",
    "TemplateRegistryService",
    "CategoryInfo",
    "TemplateInfo",
    "TemplateMetadata",
    "ValidationResult",
]

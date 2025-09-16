# Data Model: Pydantic + ABC Architecture for AI Assistant System

**Date**: 2025-09-15
**Feature**: 004-feature-modular-ai-assistant-architecture

## Architecture Overview

The AI Assistant system uses a modern Pydantic + Abstract Base Classes + Enum architecture that provides:

- **Runtime Validation**: Pydantic models catch configuration errors at creation time
- **JSON Schema Generation**: Automatic API documentation and validation schemas
- **Abstract Contracts**: ABC ensures all assistants implement required methods
- **Type Safety**: Enums prevent typos and provide IDE autocomplete
- **Immutability**: Frozen models prevent accidental state mutations
- **Clear Error Messages**: Field-level validation with detailed error context

## Core Entities

### AssistantConfig (Pydantic BaseModel)
**Purpose**: Runtime-validated configuration for AI assistant definitions

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class AssistantConfig(BaseModel):
    name: str = Field(..., regex=r'^[a-z][a-z0-9_-]*$', description="Unique assistant identifier")
    display_name: str = Field(..., min_length=1, description="Human-readable name for UI")
    description: str = Field(..., min_length=1, description="Assistant description for help")
    base_directory: str = Field(..., regex=r'^\.[a-z][a-z0-9_-]*$', description="Target directory")
    context_file: str = Field(..., min_length=1, description="Main context/instruction file")
    commands_directory: str = Field(..., min_length=1, description="Commands directory")
    memory_directory: Optional[str] = Field(None, description="Memory/constitution directory")

    @validator('base_directory')
    def validate_base_directory(cls, v):
        if not v.startswith('.'):
            raise ValueError('Base directory must start with "."')
        return v

    @validator('name')
    def validate_name_uniqueness(cls, v, values):
        # Runtime check against registry would happen here
        return v

    class Config:
        frozen = True  # Immutable after creation
        extra = 'forbid'  # No additional fields allowed
        json_schema_extra = {
            "examples": [{
                "name": "claude",
                "display_name": "Claude",
                "description": "Anthropic's AI assistant",
                "base_directory": ".claude",
                "context_file": "CLAUDE.md",
                "commands_directory": "commands"
            }]
        }
```

**Features**:
- **Field Validation**: Regex patterns, length constraints, and custom validators
- **Immutability**: Frozen config prevents accidental modifications
- **JSON Schema**: Automatic generation for documentation and API validation
- **Clear Errors**: Field-level error messages with validation context
- **Type Safety**: Full type checking with mypy/pyright support

### InjectionPoint (String Enum)
**Purpose**: Type-safe enumeration of template injection points

```python
from enum import Enum

class InjectionPoint(str, Enum):
    """Type-safe injection points for assistant-specific template content."""

    COMMAND_PREFIX = "assistant_command_prefix"
    SETUP_INSTRUCTIONS = "assistant_setup_instructions"
    CONTEXT_FILE_PATH = "assistant_context_file_path"
    MEMORY_CONFIGURATION = "assistant_memory_configuration"
    REVIEW_COMMAND = "assistant_review_command"
    DOCUMENTATION_URL = "assistant_documentation_url"

    def __str__(self) -> str:
        return self.value
```

**Benefits**:
- **Autocomplete**: IDE provides injection point suggestions
- **Typo Prevention**: Invalid injection points cause type errors
- **Refactoring Safety**: Rename injection points across codebase safely
- **Documentation**: Self-documenting enum values with descriptions

### AssistantProvider (Abstract Base Class)
**Purpose**: Abstract contract for AI assistant implementations

```python
from abc import ABC, abstractmethod
from typing import Dict

class AssistantProvider(ABC):
    """Abstract base class defining the contract for AI assistant providers."""

    @abstractmethod
    def get_config(self) -> AssistantConfig:
        """Return validated assistant configuration.

        Returns:
            AssistantConfig: Pydantic-validated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        pass

    @abstractmethod
    def get_injections(self) -> Dict[InjectionPoint, str]:
        """Return enum-based injection points for template rendering.

        Returns:
            Dict[InjectionPoint, str]: Mapping of injection points to values

        Raises:
            ValueError: If injection values are invalid
        """
        pass

    @abstractmethod
    def validate_setup(self) -> List[str]:
        """Validate assistant setup and return any issues.

        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        pass
```

**Contract Benefits**:
- **Guaranteed Interface**: All assistants must implement required methods
- **Type Safety**: Abstract methods ensure correct signatures
- **Documentation**: Clear method contracts with docstrings
- **Testing**: Easy to mock and test abstract interfaces

### AssistantRegistry (Abstract Base Class)
**Purpose**: Abstract registry for managing AI assistant providers

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class AssistantRegistry(ABC):
    """Abstract registry for AI assistant management."""

    @abstractmethod
    def get_available_assistants(self) -> List[AssistantConfig]:
        """Return list of all available assistant configurations.

        Returns:
            List[AssistantConfig]: Validated assistant configurations
        """
        pass

    @abstractmethod
    def get_provider(self, assistant_name: str) -> Optional[AssistantProvider]:
        """Get provider instance for specified assistant.

        Args:
            assistant_name: Name of the assistant to retrieve

        Returns:
            Optional[AssistantProvider]: Provider instance or None if not found
        """
        pass

    @abstractmethod
    def register_provider(self, provider: AssistantProvider) -> None:
        """Register a new assistant provider.

        Args:
            provider: Validated assistant provider instance

        Raises:
            ValueError: If provider configuration is invalid
            DuplicateAssistantError: If assistant name already registered
        """
        pass

    @abstractmethod
    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all registered assistants.

        Returns:
            Dict[str, List[str]]: Mapping of assistant names to error lists
        """
        pass
```

## Validation Architecture

### Pydantic Field Validation
**Automatic Field-Level Validation**:

```python
# Example validation in AssistantConfig
@validator('name')
def validate_assistant_name(cls, v):
    if not v:
        raise ValueError('Assistant name cannot be empty')
    if not v.islower():
        raise ValueError('Assistant name must be lowercase')
    if ' ' in v:
        raise ValueError('Assistant name cannot contain spaces')
    return v

@validator('base_directory')
def validate_base_directory(cls, v):
    if not v.startswith('.'):
        raise ValueError('Base directory must start with "."')
    if '..' in v:
        raise ValueError('Base directory cannot contain ".."')
    return v
```

### Cross-Field Validation
**Validate Relationships Between Fields**:

```python
@validator('commands_directory')
def validate_commands_directory(cls, v, values):
    base_dir = values.get('base_directory')
    if base_dir and v.startswith('/'):
        raise ValueError('Commands directory should be relative to base directory')
    return v
```

### Runtime Error Handling
**Clear Error Messages with Context**:

```python
try:
    config = AssistantConfig(
        name="Invalid Name",  # Validation error: spaces not allowed
        display_name="",       # Validation error: min_length=1
        # ... other fields
    )
except ValidationError as e:
    for error in e.errors():
        print(f"Field '{error['loc'][0]}': {error['msg']}")
        # Output: Field 'name': string does not match regex "^[a-z][a-z0-9_-]*$"
        # Output: Field 'display_name': ensure this value has at least 1 characters
```

### JSON Schema Generation
**Automatic API Documentation**:

```python
# Generate JSON schema for documentation
schema = AssistantConfig.schema()
print(json.dumps(schema, indent=2))

# Schema includes:
# - Field types and constraints
# - Validation rules and patterns
# - Examples and descriptions
# - Required vs optional fields
```

## Service Interfaces

### IAssistantValidator (Abstract Base Class)
**Purpose**: Abstract contract for assistant validation services

```python
from abc import ABC, abstractmethod
from typing import List
from pydantic import ValidationError

class IAssistantValidator(ABC):
    """Abstract validator for AI assistant configurations and providers."""

    @abstractmethod
    def validate_config(self, config: AssistantConfig) -> List[str]:
        """Validate assistant configuration beyond Pydantic field validation.

        Args:
            config: Pydantic-validated AssistantConfig instance

        Returns:
            List[str]: Business logic validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def validate_provider(self, provider: AssistantProvider) -> List[str]:
        """Validate assistant provider implementation.

        Args:
            provider: Assistant provider to validate

        Returns:
            List[str]: Provider validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def validate_injection_points(self, injections: Dict[InjectionPoint, str]) -> List[str]:
        """Validate injection point values for template safety.

        Args:
            injections: Mapping of injection points to string values

        Returns:
            List[str]: Injection validation errors (empty if valid)
        """
        pass
```

### ITemplateEnhancer (Abstract Base Class)
**Purpose**: Abstract contract for template enhancement with injection points

```python
from abc import ABC, abstractmethod
from typing import Dict, List

class ITemplateEnhancer(ABC):
    """Abstract template enhancer for injection point integration."""

    @abstractmethod
    def enhance_template(
        self,
        template_content: str,
        injections: Dict[InjectionPoint, str]
    ) -> str:
        """Enhance template with type-safe injection points.

        Args:
            template_content: Original template content
            injections: Enum-based injection point values

        Returns:
            str: Enhanced template with injection points resolved

        Raises:
            TemplateEnhancementError: If injection points cannot be resolved
        """
        pass

    @abstractmethod
    def validate_injection_usage(self, template_content: str) -> List[str]:
        """Validate that template uses injection points correctly.

        Args:
            template_content: Template content to validate

        Returns:
            List[str]: Validation errors for injection point usage
        """
        pass
```

## Data Flow Architecture

### Provider Registration Flow
```
1. Assistant module defines provider class extending AssistantProvider
2. Provider implements get_config() returning Pydantic-validated AssistantConfig
3. Provider implements get_injections() returning Dict[InjectionPoint, str]
4. Registry validates provider using AbstractValidator contract
5. Pydantic validation occurs automatically on config creation
6. Provider registered in type-safe registry with error handling
```

### Template Injection Flow
```
1. User initiates project with specific AI assistant selection
2. TemplateService requests provider from AbstractRegistry
3. Provider returns validated AssistantConfig and injection points
4. InjectionPoint enum ensures type-safe template variable access
5. Template rendering uses validated, type-safe injection values
6. Pydantic models ensure data integrity throughout pipeline
```

### Validation Pipeline
```
1. Pydantic field validation (automatic on model creation)
2. Cross-field validation (custom validators in model)
3. Business logic validation (via IAssistantValidator ABC)
4. Injection point validation (enum-based type safety)
5. Template compatibility validation (runtime template checks)
6. Build-time type checking (mypy/pyright static analysis)
```

## Error Handling Strategy

### Validation Errors
**Pydantic ValidationError with Field Context**:
```python
try:
    config = AssistantConfig(name="Invalid Name!")
except ValidationError as e:
    # Clear field-level error messages
    for error in e.errors():
        field = error['loc'][0]
        message = error['msg']
        # Log: "Field 'name': string does not match regex '^[a-z][a-z0-9_-]*$'"
```

### Runtime Errors
**Abstract Base Class Contract Violations**:
```python
# Missing method implementation
class IncompleteProvider(AssistantProvider):
    def get_config(self) -> AssistantConfig:
        return AssistantConfig(...)
    # Missing get_injections() - TypeError at instantiation

provider = IncompleteProvider()  # TypeError: Can't instantiate abstract class
```

### Type Safety Errors
**Enum-Based Injection Point Safety**:
```python
# Typo prevention with enums
injections = {
    InjectionPoint.COMMAND_PREFIX: "claude ",  # ✅ Type-safe
    "command_prefix": "claude "  # ❌ Type error - string not allowed
}
```

## Benefits of Pydantic + ABC Architecture

### Runtime Validation Benefits
- **Immediate Error Detection**: Configuration errors caught at model creation
- **Clear Error Messages**: Field-level validation with specific error context
- **Type Coercion**: Automatic conversion of compatible types (str → int, etc.)
- **JSON Schema**: Automatic generation for API documentation and validation

### Abstract Base Class Benefits
- **Guaranteed Contracts**: All providers must implement required methods
- **Type Safety**: Abstract methods ensure correct method signatures
- **Polymorphism**: Treat all providers uniformly through abstract interface
- **Testing**: Easy to create mock implementations for testing

### Enum Type Safety Benefits
- **Autocomplete**: IDE provides injection point suggestions and validation
- **Refactoring Safety**: Rename injection points safely across entire codebase
- **Typo Prevention**: Invalid injection points cause compilation/type errors
- **Documentation**: Self-documenting enum values with descriptions

### Performance Benefits
- **Validation Caching**: Pydantic caches validation results for performance
- **Memory Efficiency**: Frozen models prevent accidental object mutations
- **Fast Serialization**: Built-in JSON serialization optimized for performance
- **Type Checking**: Build-time type checking prevents runtime type errors

### Development Experience Benefits
- **IDE Support**: Full autocomplete and type checking in modern IDEs
- **Error Prevention**: Many errors caught at development time, not runtime
- **Documentation**: JSON Schema generation provides automatic API docs
- **Maintainability**: Clear contracts make code easier to understand and modify

This architecture provides a robust, type-safe foundation for the AI assistant system with comprehensive validation, clear contracts, and excellent developer experience.
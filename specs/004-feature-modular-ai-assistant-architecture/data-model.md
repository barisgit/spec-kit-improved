# Data Model: Type-Safe AI Assistant Organization System

**Date**: 2025-09-15
**Feature**: 004-feature-modular-ai-assistant-architecture

## Core Entities

### AssistantConfig (Dataclass)
**Purpose**: Type-safe configuration for AI assistant definitions with validation
**Attributes**:
- `name: str` - Unique assistant identifier (e.g., "claude", "gemini")
- `display_name: str` - Human-readable name for UI display
- `description: str` - Assistant description for help text
- `base_directory: str` - Target directory for AI files (e.g., ".claude")
- `context_file: str` - Main context/instruction file path
- `commands_directory: str` - Commands directory path
- `memory_directory: str` - Memory/constitution directory path

**Features**:
- Frozen dataclass (immutable after creation)
- Constructor validation in `__post_init__`
- Automatic field validation on instantiation
- Type checking and IDE support

**Relationships**:
- Implemented by assistant modules in `assistants/*/config.py`
- Used by AssistantRegistry for static registration
- Referenced by TemplateContext for injection points

**Validation Rules** (enforced by constructor):
- Name must be unique across all assistants
- Name must be non-empty lowercase
- Base directory must start with "."
- Display name cannot be empty
- Context file and commands directory are required

### InjectionProvider (Protocol)
**Purpose**: Type-safe interface for providing template injection points
**Methods**:
- `get_injections() -> Dict[str, str]` - Return injection point values for templates

**Relationships**:
- Implemented by assistant modules in `assistants/*/injections.py`
- Used by TemplateContext for assistant-specific content
- Referenced by TemplateService for rendering

**Validation Rules**:
- All injection points must return string values
- Injection point names must be valid Jinja2 variable names
- Values must be safe for template rendering (no code injection)

### AssistantRegistry (Static Class)
**Purpose**: Type-safe registry for AI assistant configurations and injections
**Attributes**:
- `ASSISTANTS: List[AssistantConfig]` - Static list of assistant configurations
- `INJECTION_PROVIDERS: Dict[str, InjectionProvider]` - Static mapping of injection providers
- `_validation_cache: Dict[str, bool]` - Cached validation results

**Relationships**:
- Aggregates all assistant configurations from static imports
- Manages injection provider instances
- Used by CLI commands and template service

**State Transitions**:
- Module Load → Validation → Ready
- Validation Error → Error State with clear messages

### TemplateContext (Enhanced)
**Purpose**: Enhanced template context with assistant injection points
**Attributes**:
- `project_name: str` - Project name for templates
- `ai_assistant: str` - Selected assistant name
- `assistant_injections: Dict[str, str]` - Injection point values
- `standard_context: Dict[str, Any]` - Standard template variables

**Relationships**:
- Enhanced by AssistantRegistry with injection points
- Used by TemplateService for rendering
- Contains type-safe assistant-specific content

### InjectionPoint (Enum)
**Purpose**: Enumeration of available injection points for type safety
**Values**:
- `COMMAND_PREFIX` - Assistant command prefix (e.g., "claude ")
- `SETUP_INSTRUCTIONS` - Setup/authentication instructions
- `MEMORY_CONFIGURATION` - Memory/constitution configuration
- `CONTEXT_FILE_PATH` - Path to main context file
- `REVIEW_COMMAND` - Code review command
- `DOCUMENTATION_URL` - Assistant documentation URL

**Relationships**:
- Used by InjectionProvider implementations for type safety
- Referenced in template files for injection points
- Validated by build-time checks

### AssistantValidationResult
**Purpose**: Type-safe validation result for assistant configurations
**Attributes**:
- `assistant_name: str` - Validated assistant name
- `is_valid: bool` - Overall validation status
- `errors: List[str]` - Validation error messages
- `warnings: List[str]` - Non-critical validation issues
- `injection_points_valid: bool` - Injection points validation status

**Relationships**:
- Produced by AssistantValidator
- Used by build-time validation
- Referenced in CI/CD type checking

## Service Interfaces

### IAssistantValidator (Protocol)
**Purpose**: Interface for type-safe assistant validation
**Methods**:
- `validate_config(config: AssistantConfig) -> List[str]` - Validate configuration
- `validate_injections(provider: InjectionProvider) -> List[str]` - Validate injection points
- `validate_templates_compatibility(assistant_name: str) -> bool` - Check template compatibility

### IDocumentationGenerator (Protocol)
**Purpose**: Interface for auto-generating assistant documentation
**Methods**:
- `generate_assistant_list() -> str` - Generate markdown list of assistants
- `generate_injection_point_docs() -> str` - Document available injection points
- `generate_assistant_comparison() -> str` - Compare assistant features

### ITemplateEnhancer (Protocol)
**Purpose**: Interface for enhancing templates with injection points
**Methods**:
- `add_injection_points(template_content: str) -> str` - Add injection points to template
- `validate_injection_usage(template_content: str) -> List[str]` - Validate injection point usage
- `remove_conditionals(template_content: str) -> str` - Remove conditional logic

## Data Flow

### Assistant Registration Flow
1. Module import triggers static registration
2. AssistantRegistry validates all configurations
3. Type checking validates injection provider interfaces
4. Build-time validation ensures consistency
5. Registry ready for template service usage

### Template Injection Flow
1. User requests project initialization with AI assistant
2. TemplateService requests assistant injections from registry
3. Registry looks up injection provider by assistant name
4. Provider returns type-safe injection point values
5. Template service merges injections with standard context
6. Jinja2 renders template with assistant-specific content

### Build-Time Validation Flow
1. Type checker validates all AssistantConfig implementations
2. Protocol conformance checked for InjectionProvider implementations
3. Injection point usage validated in template files
4. Documentation generation tested for completeness
5. Integration tests verify end-to-end functionality

## Migration Strategy

### Code Organization Migration
- Move assistant configurations from `ai_defaults.py` to `assistants/*/config.py`
- Create injection providers in `assistants/*/injections.py`
- Update imports to use static registry
- Maintain backward compatibility during transition

### Template Enhancement Migration
- Identify conditional logic in existing templates
- Replace with assistant-agnostic injection points
- Validate template rendering with all assistants
- Ensure output identical to current system

### Type Safety Integration
- Add type checking to CI/CD pipeline
- Configure mypy/pyright for assistant modules
- Add pre-commit hooks for validation
- Document type requirements for new assistants

## Error Handling

### Build-Time Errors
- Missing assistant configuration → Type error with clear message
- Invalid injection provider → Protocol conformance error
- Missing injection points → Template validation error
- Type mismatches → Static analysis error with fix suggestions

### Runtime Errors
- Assistant not found → Fallback to default with warning
- Injection point missing → Template error with context
- Invalid template syntax → Jinja2 error with line number
- File access errors → Clear error with path information

## Performance Considerations

### Static Registration Benefits
- No discovery overhead (0ms vs 100ms plugin scanning)
- Type checking at build time, not runtime
- Import-time validation prevents runtime errors
- Static analysis enables IDE support and refactoring

### Memory Efficiency
- Assistant configs loaded once at module import
- Injection providers instantiated lazily
- Template cache reused across assistant types
- No dynamic allocation during template rendering

### Build Performance
- Type checking runs in parallel with other CI/CD tasks
- Validation cached based on file modification times
- Incremental validation for changed assistants only
- Documentation generation only when configs change

This data model provides a clean, type-safe foundation for assistant organization while maintaining the simplicity and performance of the current system.
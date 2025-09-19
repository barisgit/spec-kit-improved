# Data Model: Enhanced Commands and Agent Support

## Core Entities

### ImplementationTask
```python
class ImplementationTask:
    id: str                    # Task identifier (e.g., "TASK-001")
    description: str           # Human-readable task description
    status: TaskStatus         # pending, in_progress, completed, failed
    dependencies: List[str]    # Task IDs this task depends on
    is_parallel: bool          # Can run in parallel with other tasks (marked with [P])
    file_paths: List[str]      # Files this task will modify
    test_required: bool        # Whether this task requires TDD approach
    execution_context: Dict[str, Any]  # Runtime metadata
```

### ProjectConstitution
```python
class ProjectConstitution:
    principles: List[Principle]        # Core governing principles
    development_guidelines: Dict       # Development process rules
    decision_framework: Dict           # How decisions should be made
    created_at: datetime
    last_modified: datetime
    version: str
```

### AgentTemplate
```python
class AgentTemplate:
    name: str                  # Template name (e.g., "code-reviewer")
    assistant_type: str        # AI assistant type (claude, copilot, etc.)
    template_content: str      # Jinja2 template content
    variables: Dict[str, Any]  # Template variables and defaults
    output_path: str           # Where generated agent should be placed
    description: str           # Template purpose and usage
```

### AgentScaffoldScript
```python
class AgentScaffoldScript:
    name: str                  # Script name
    template_refs: List[str]   # Agent templates this script can render
    script_content: str        # Python script content
    execution_params: Dict     # Script parameters
    output_directory: str      # Where script places results
```

### AgentContext
```python
class AgentContext:
    project_root: str          # Project root directory
    current_feature: str       # Active feature being worked on
    specs: Dict[str, Any]      # Current specifications
    plans: Dict[str, Any]      # Implementation plans
    tasks: List[ImplementationTask]  # Current tasks
    constitution: ProjectConstitution  # Project governance
    shared_memory: Dict[str, Any]      # Cross-agent shared state
```

### SystemPromptGuide
```python
class SystemPromptGuide:
    assistant_type: str        # Target AI assistant
    base_prompt: str           # Base system prompt template
    injection_points: List[InjectionPoint]  # Where to insert SpecifyX content
    customization_sections: Dict[str, str]  # Customizable prompt sections
    examples: List[str]        # Usage examples
```

### InjectionPoint
```python
class InjectionPoint:
    name: str                  # Injection point identifier
    location: str              # Where in prompt to inject
    content_type: str          # Type of content (project_context, commands, etc.)
    max_tokens: int            # Maximum content size
    priority: int              # Injection priority order
```

## Relationships

### Task Dependencies
- ImplementationTask -> ImplementationTask (dependencies)
- ImplementationTask -> AgentContext (execution context)

### Agent System
- AgentTemplate -> AssistantConfiguration (assistant-specific templates)
- AgentScaffoldScript -> AgentTemplate (renders templates)
- AgentContext -> ProjectConstitution (governance integration)
- AgentContext -> ImplementationTask (current work context)

### Configuration
- SystemPromptGuide -> AssistantConfiguration (assistant-specific prompts)
- ProjectConstitution -> AgentContext (shared governance)

## State Transitions

### ImplementationTask Status Flow
```
pending -> in_progress -> completed
pending -> in_progress -> failed -> pending (retry)
```

### Agent Template Lifecycle
```
template_created -> validated -> rendered -> deployed
```

### Context Sharing Flow
```
context_created -> populated -> shared -> synchronized -> archived
```

## Validation Rules

### ImplementationTask
- Dependencies must form a DAG (no circular dependencies)
- Parallel tasks cannot have overlapping file_paths
- Test tasks must precede implementation tasks (TDD enforcement)
- Status transitions must follow defined flow

### AgentTemplate
- Template content must be valid Jinja2
- Variables must have defined types and defaults
- Output paths must be within allowed directories
- Assistant type must be supported

### ProjectConstitution
- Principles must be non-contradictory
- Guidelines must be actionable and measurable
- Decision framework must cover all major decision types
- Version must follow semantic versioning

### AgentContext
- Shared memory size must not exceed limits
- Context updates must be atomic
- Project root must be valid git repository
- All referenced entities must exist
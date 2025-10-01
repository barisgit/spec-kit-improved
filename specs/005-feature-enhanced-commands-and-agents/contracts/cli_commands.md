# CLI Command Contracts

This document defines the contracts for new SpecifyX CLI commands that will be integrated into the existing command structure.

## New Commands Integration

### 1. get-prompt Command
**Location**: `src/specify_cli/commands/get_prompt/get_prompt.py`
**Registration**: Direct command registration in `app.command("get-prompt")(get_prompt_command)`

```python
def get_prompt_command(
    assistant: str = typer.Argument(help="AI assistant type (claude, copilot, cursor, gemini)"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save prompt to file"),
    include_examples: bool = typer.Option(True, "--examples/--no-examples", help="Include usage examples"),
    context_size: str = typer.Option("large", help="Context size (small, medium, large)")
) -> None:
    """Generate comprehensive system prompt modification guide for specified AI assistant."""
```

### 2. Slash Commands (Template-based)
**Location**: `src/specify_cli/templates/commands/`
**Format**: Markdown with Jinja2 templating (`.md.j2`)

- `implement.md.j2` - Automated task execution
- `constitution.md.j2` - Project governance management
- `guide.md.j2` - Human implementation instructions

These integrate with existing template system and are processed during `specifyx init`.

## Command Architecture Integration

### Existing Pattern
Commands follow the established pattern:
1. **Direct commands**: `init`, `check`, `add-ai`, `refresh-templates`, `get-prompt`
2. **Command groups**: `run` (subcommands), `update` (subcommands)
3. **Template commands**: Slash commands generated during init

### Agent Support Integration
Agent support leverages existing SpecifyX systems:
- **Templates**: Extend `.specify/templates/` structure
- **Scripts**: Use `.specify/scripts/` for agent scaffolding
- **Configuration**: Extend `.specify/config.toml` sections
- **Services**: New services follow existing service patterns

## Template System Integration

### Agent Templates
- **Location**: `.specify/agent-templates/` (user-customizable)
- **System templates**: Bundled with SpecifyX installation
- **Rendering**: Uses existing Jinja2 infrastructure

### Script Generation
- **Location**: `.specify/scripts/agent-scaffold.py`
- **Pattern**: Follows existing script generation patterns
- **Dependencies**: Uses SpecifyX service imports for consistency

## Service Layer Integration

### New Services
Following existing service patterns in `src/specify_cli/services/`:

1. **AgentService**: Manages agent template rendering and scaffolding
2. **PromptService**: Handles system prompt generation and management
3. **ImplementService**: Orchestrates task execution and progress tracking
4. **ConstitutionService**: Manages project governance documents

### Existing Service Reuse
- **TemplateService**: For agent template rendering
- **ConfigService**: For agent configuration management
- **ProjectManager**: For project context and structure

## Testing Integration

### Test Structure
Following existing test patterns in `tests/`:
- **Command tests**: `tests/commands/test_get_prompt.py`
- **Service tests**: `tests/services/test_agent_service.py`
- **Template tests**: `tests/templates/test_agent_templates.py`
- **Integration tests**: `tests/integration/test_agent_workflow.py`

### Contract Tests
Templates must render without errors and produce valid outputs that match expected schemas.

## Configuration Integration

### Config Extension
Extends existing `.specify/config.toml` for user preferences:

```toml
[agents]
output_directory = ".specify/agents"
```

### Assistant Capabilities (Built-in)
Agent support is integrated with existing type-safe `AssistantProvider` architecture in `src/specify_cli/assistants/`:

```python
# Existing AssistantConfig already handles agent support
@dataclass
class AssistantConfig:
    name: str
    display_name: str
    description: str
    base_directory: str
    context_file: ContextFileConfig
    command_files: TemplateConfig
    agent_files: Optional[TemplateConfig]  # None = no agent support, TemplateConfig = agent support
```

Agent support is determined by whether `agent_files` is None or configured:
- **Claude**: `agent_files=TemplateConfig(directory=".claude/agents", file_format=FileFormat.MARKDOWN)`
- **Copilot/Cursor/Gemini**: `agent_files=None` (no agent support)

This leverages the existing type-safe system without additional fields.

This approach leverages SpecifyX's existing comprehensive system rather than creating parallel infrastructure.
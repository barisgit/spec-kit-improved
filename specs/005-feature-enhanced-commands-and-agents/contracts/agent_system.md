# Agent System Contracts

## Agent File Types

Agent system has three file types that come in pairs + one generic template:

### 1. Agent Prompt Templates
**Location**: `src/specify_cli/templates/agent-prompts/`
**Purpose**: Complete agent definitions with frontmatter, role definition, and systematic approach
**Output**: Files like `.claude/agents/code-reviewer.md`
**Pairing**: Each agent has corresponding runtime template

```markdown
---
name: code-reviewer
description: Use this agent proactively after major Claude Code operations (file creation, significant edits, feature implementations) or when user explicitly requests code review. Focus on code quality, type safety, professional standards, and eliminating hardcoding/hacks. Examples: <example>Context: Claude just implemented a new authentication system with multiple file changes. assistant: 'Now that I've completed the authentication implementation, let me use the code-reviewer agent to ensure code quality and catch any issues before we proceed.' <commentary>After major Claude Code operations, proactively use the code-reviewer to maintain quality standards.</commentary></example> <example>Context: User explicitly requests review after changes. user: 'Can you review the code changes I just made?' assistant: 'I'll use the code-reviewer agent to thoroughly examine your changes for quality, type safety, and best practices.' <commentary>When user explicitly requests review, use the code-reviewer agent for comprehensive analysis.</commentary></example>
tools: Glob, Grep, LS, Read, Edit, MultiEdit, Write, NotebookRead, NotebookEdit, WebFetch, TodoWrite, WebSearch, mcp__ide__getDiagnostics, mcp__ide__executeCode
model: sonnet
color: red
---

You are an expert software engineer specializing in comprehensive code review with deep expertise across multiple languages and frameworks...

**SYSTEMATIC ANALYSIS APPROACH:**
1. **Plan Adherence**: Verify implementation follows the intended plan and requirements
2. **Best Practices Compliance**: Ensure code follows language/framework-specific best practices
3. **Type Safety**: Identify non-type-safe code, missing types, and unsafe operations
4. **Hardcoding Detection**: Find hardcoded values that should be configurable or constants
5. **Professional Standards**: Flag unprofessional elements (excessive emojis, informal comments, etc.)

[Complete internal workflow that the agent follows but orchestrator doesn't see]
```

### 2. Agent Scaffold Scripts
**Location**: `.specify/scripts/scaffold-agent.py`
**Purpose**: Auto-discover agent types and generate structured output files
**Usage**:
- `specifyx run scaffold-agent --list` (show available agents)
- `specifyx run scaffold-agent code-reviewer:auth-system-review`
- `specifyx run scaffold-agent code-reviewer:auth-review documentation-reviewer:readme-updates`
- `specifyx run scaffold-agent code-reviewer:security-check code-reviewer:performance-review`
- `specifyx run scaffold-agent code-reviewer` (uses agent name as description)

**Output Structure**: `.specify/agents/{agent-type}/{date}-{seq}-{description}.md`
- Example: `.specify/agents/code-reviewer/2025-09-19-001-auth-system-review.md`

```python
#!/usr/bin/env python3
"""Agent scaffolding script for SpecifyX projects."""

import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from specify_cli.services.template_service import TemplateService
from specify_cli.services.project_manager import ProjectManager


@dataclass
class AgentType:
    """Type-safe agent type definition."""
    name: str
    description: str
    template_path: Path


@dataclass
class ScaffoldRequest:
    """Type-safe scaffold request."""
    agent_name: str
    description: Optional[str] = None
    args: Optional[Dict[str, Any]] = None


def discover_agent_types() -> List[AgentType]:
    """Auto-discover available agent types from templates."""
    template_dir = Path(".specify/agent-templates")
    if not template_dir.exists():
        return []

    agent_types: List[AgentType] = []
    for template_file in template_dir.glob("*.md.j2"):
        content = template_file.read_text()
        description = "Agent template"

        if content.startswith("---"):
            try:
                frontmatter_end = content.find("---", 3)
                frontmatter = yaml.safe_load(content[3:frontmatter_end])
                description = frontmatter.get("description", description)
            except Exception:
                pass  # Use default description

        agent_types.append(AgentType(
            name=template_file.stem,
            description=description,
            template_path=template_file
        ))

    return agent_types


def get_next_sequence_number(agent_dir: Path, date_str: str) -> str:
    """Get next sequence number for agent output file."""
    if not agent_dir.exists():
        return "001"

    existing_files = list(agent_dir.glob(f"{date_str}-*-*.md"))
    if not existing_files:
        return "001"

    max_seq = 0
    for file in existing_files:
        try:
            # Extract sequence from filename: {date}-{seq}-{description}.md
            parts = file.stem.split("-", 2)
            if len(parts) >= 2:
                seq = int(parts[1])
                max_seq = max(max_seq, seq)
        except ValueError:
            continue

    return f"{max_seq + 1:03d}"


def get_project_context() -> Dict[str, Any]:
    """Get current project context for template rendering."""
    project_manager = ProjectManager()

    return {
        "project_name": project_manager.get_project_name(),
        "current_feature": project_manager.get_current_feature(),
        "timestamp": datetime.now().isoformat(),
        "specs": project_manager.get_current_specs(),
        "plans": project_manager.get_current_plans(),
        "tasks": project_manager.get_current_tasks(),
    }


def scaffold_agent(request: ScaffoldRequest, base_output_dir: Path) -> Path:
    """Scaffold a specific agent with proper file naming."""
    template_service = TemplateService()
    template_path = Path(f".specify/agent-templates/{request.agent_name}.md.j2")

    if not template_path.exists():
        raise FileNotFoundError(f"Agent template not found: {template_path}")

    # Create agent-specific directory
    agent_dir = base_output_dir / request.agent_name
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename: {date}-{seq}-{description}.md
    date_str = datetime.now().strftime("%Y-%m-%d")
    sequence = get_next_sequence_number(agent_dir, date_str)
    description = request.description or request.agent_name

    output_path = agent_dir / f"{date_str}-{sequence}-{description}.md"

    # Render with project context + custom args
    context = get_project_context()
    if request.args:
        context.update(request.args)

    rendered = template_service.render(str(template_path), context)

    output_path.write_text(rendered)
    return output_path


def parse_agent_spec(agent_spec: str) -> ScaffoldRequest:
    """Parse agent specification in format 'agent-name' or 'agent-name:description'."""
    if ":" in agent_spec:
        agent_name, description = agent_spec.split(":", 1)
        return ScaffoldRequest(agent_name=agent_name, description=description)
    else:
        return ScaffoldRequest(agent_name=agent_spec, description=agent_spec)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scaffold agent output files")
    parser.add_argument("agents", nargs="*", help="Agent specifications (agent-name or agent-name:description)")
    parser.add_argument("--list", action="store_true", help="List available agent types")
    parser.add_argument("--args", help="JSON string of additional arguments")
    parser.add_argument("--output", default=".specify/agents", help="Base output directory")

    args = parser.parse_args()

    # Discover available agent types
    agent_types = discover_agent_types()

    if args.list:
        print("Available agents:")
        for agent in agent_types:
            print(f"  {agent.name}: {agent.description}")
        return

    if not args.agents:
        print("Specify agent(s) to scaffold or use --list to see available agents")
        return

    # Parse additional arguments
    additional_args: Optional[Dict[str, Any]] = None
    if args.args:
        try:
            additional_args = json.loads(args.args)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in --args: {e}")
            return

    base_output_dir = Path(args.output)

    # Generate for each requested agent
    for agent_spec in args.agents:
        request = parse_agent_spec(agent_spec)
        request.args = additional_args

        try:
            output_path = scaffold_agent(request, base_output_dir)
            print(f"Generated: {output_path}")
        except Exception as e:
            print(f"Failed to generate {agent_spec}: {e}")


if __name__ == "__main__":
    main()
```

### 3. Agent Runtime Templates
**Location**: `.specify/agent-templates/`
**Purpose**: Templates used by scaffold scripts to generate structured agent outputs
**Format**: Jinja2 templates (`.md.j2`)
**Pairing**: Each agent prompt template has corresponding runtime template

### 4. Generic Agent Template
**Location**: `.specify/agent-templates/generic-agent.md.j2`
**Purpose**: Fallback template for any agent type without specific runtime template
**Usage**: Used when scaffolding an agent that doesn't have a custom runtime template

```markdown
# {{ agent_type.title() }} Output

**Project**: {{ project_name }}
**Feature**: {{ current_feature }}
**Generated**: {{ timestamp }}

## Analysis

### Code Quality Assessment
- [ ] Architecture follows project patterns
- [ ] Error handling is comprehensive
- [ ] Code is properly documented
- [ ] Tests cover critical paths

### Recommendations

#### Critical Issues
{% for issue in critical_issues %}
- {{ issue }}
{% endfor %}

#### Improvements
{% for improvement in improvements %}
- {{ improvement }}
{% endfor %}

## Next Steps
{{ next_steps }}
```

### 5. Context Template
**Location**: `.specify/agent-templates/context.md.j2`
**Purpose**: Template for shared context files when using `--shared-context` flag
**Usage**: Creates shared context file that multiple agents reference in their reports

```markdown
# Shared Context: {{ context_title }}

**Project**: {{ project_name }}
**Feature**: {{ current_feature }}
**Created**: {{ timestamp }}
**Context ID**: {{ context_id }}

## Background Information
{{ context_description }}

## Relevant Files
{% for file_path in relevant_files %}
- `{{ file_path }}`
{% endfor %}

## Key Requirements
{{ key_requirements }}

## Analysis Focus Areas
{{ focus_areas }}

## Additional Context
{{ additional_context }}
```

## Integration with Existing Systems

### TemplateService Integration
Agent templates leverage existing `TemplateService`:
- No new template rendering infrastructure needed
- Uses proven Jinja2 integration
- Consistent variable substitution patterns

### AssistantProvider Integration
Agent support uses existing `AssistantProvider.agent_files`:
- `agent_files=None` → No assistant-specific agent files created
- `agent_files=TemplateConfig(...)` → Assistant-specific agent files created in assistant directory
- `.specify/agents/` and `.specify/agent-templates/` directories ALWAYS created regardless of assistant support
- No new fields or configuration needed

### Configuration
Extends existing `.specify/config.toml`:
```toml
[agents]
output_directory = ".specify/agents"
```

## File Generation During Init

### During `specifyx init`:
1. **Agent Prompt Templates** → Rendered to assistant directories (`.claude/agents/`)
2. **Scaffold Scripts** → Copied to `.specify/scripts/`
3. **Runtime Templates** → Copied to `.specify/agent-templates/`

### During Runtime:
1. User runs scaffold script
2. Script uses `TemplateService` to render runtime template
3. Output generated in `.specify/agents/`
4. Agent (via assistant) can reference output for context

This approach leverages SpecifyX's existing modular architecture without introducing parallel systems.

## Agent Selection UI Helper

### Interactive Agent Selection
Used in `specifyx init` and `specifyx refresh-templates` to let users choose which agents to include:

```python
from typing import List, Dict, Any
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

def select_agents_interactive(available_agents: List[AgentType], assistants: List[str]) -> Dict[str, List[str]]:
    """Interactive agent selection for project initialization."""
    console = Console()

    # Show available agents
    table = Table(title="Available Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")

    for agent in available_agents:
        table.add_row(agent.name, agent.description)

    console.print(table)
    console.print()

    # Selection options
    console.print("Agent selection options:")
    console.print("1. Include all agents")
    console.print("2. Select specific agents")
    console.print("3. Skip agent setup")

    choice = Prompt.ask("Choose option", choices=["1", "2", "3"], default="1")

    if choice == "3":
        return {}
    elif choice == "1":
        # Include all agents for all supporting assistants
        result = {}
        for assistant in assistants:
            if supports_agents(assistant):
                result[assistant] = [agent.name for agent in available_agents]
        return result
    else:
        # Interactive selection per assistant
        result = {}
        for assistant in assistants:
            if not supports_agents(assistant):
                continue

            console.print(f"\n[bold]Select agents for {assistant}:[/bold]")
            selected = []

            for agent in available_agents:
                if Confirm.ask(f"Include {agent.name}?", default=True):
                    selected.append(agent.name)

            if selected:
                result[assistant] = selected

        return result

def supports_agents(assistant: str) -> bool:
    """Check if assistant supports agents using existing AssistantProvider."""
    from specify_cli.assistants.registry import get_registry

    registry = get_registry()
    provider = registry.get_assistant(assistant)

    return provider and provider.config.agent_files is not None
```

### Integration Points

#### During `specifyx init`
```python
# After AI assistant selection
selected_agents = select_agents_interactive(discover_agent_types(), selected_assistants)

# Generate agent files for selected agents and assistants
for assistant, agent_names in selected_agents.items():
    generate_agent_files_for_assistant(assistant, agent_names)
```

#### During `specifyx refresh-templates`
```python
# Refresh agent templates
console.print("Refreshing agent templates...")
selected_agents = select_agents_interactive(discover_agent_types(), project.get_assistants())

# Update existing agent configuration
update_agent_templates(selected_agents)
```
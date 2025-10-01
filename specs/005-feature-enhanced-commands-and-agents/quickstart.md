# Quickstart: Enhanced Commands and Agent Support

## Overview
This guide demonstrates the new SpecifyX commands and agent support system through practical examples.

## Prerequisites
- SpecifyX installed (`uv tool install specifyx`)
- Project initialized with AI assistant (`specifyx init my-project --ai claude`)
- Constitution, spec, plan, and tasks already created

## Quick Test Scenarios

### 1. Automated Implementation with `/implement`
```bash
# From your AI assistant (Claude Code, etc.)
/implement

# Expected: System executes all tasks from tasks.md automatically
# Progress tracking shows phase completion
# Tasks marked as [X] when completed
# Stops on errors with recovery guidance
```

### 2. Project Governance with `/constitution`
```bash
# Create project constitution
/constitution Create principles focused on code quality, testing standards, and user experience consistency

# Expected: Creates .specify/memory/constitution.md
# Integrates with existing project guidelines
# Updates templates to align with new principles
```

### 3. Manual Implementation Guide with `/guide`
```bash
# Generate human instructions
/guide

# Expected: Creates implementation-guide.md
# Structured checklist format
# Includes time estimates and prerequisites
# Provides troubleshooting section
```

### 4. System Prompt Optimization with `specifyx get-prompt`
```bash
# Get Claude Code prompt guide
specifyx get-prompt claude --output claude-prompt.md

# Expected: Comprehensive system prompt modification guide
# Injection points for SpecifyX integration
# Examples and customization sections
```

### 5. Agent Scaffolding
```bash
# During specifyx init, user selects from 6 core agents:
# - code-reviewer: Code quality, type safety, professional standards
# - documentation-reviewer: Review docs for accuracy and professionalism
# - implementer: Execute implementation tasks systematically
# - spec-reviewer: Review specifications for completeness and clarity
# - architecture-reviewer: Review system design and architectural decisions
# - test-reviewer: Test coverage, TDD compliance, test quality

# System automatically creates:
# - .specify/agents/ and .specify/agent-templates/ directories (ALWAYS)
# - .claude/agents/{agent-name}.md (ONLY if assistant supports agents)
# - .specify/agent-templates/{agent-name}.j2 (ALWAYS - for future use)
# - .specify/scripts/scaffold-agent.py (ALWAYS - works regardless of assistant)

# Run agent scaffolding
specifyx run scaffold-agent code-reviewer:auth-system-review documentation-reviewer:api-docs-update

# Expected: Generates timestamped agent output files in .specify/agents/{agent-type}/

# Run shared context scaffolding
specifyx run scaffold-agent --shared-context="auth system security review" code-reviewer:security-analysis spec-reviewer:auth-spec-validation

# Expected: Creates one context file + multiple agent reports referencing the context
```

## Integration Test Scenarios

### End-to-End Workflow
1. **Setup**: `specifyx init test-project --ai claude`
2. **Governance**: `/constitution` command to establish principles
3. **Feature**: `/specify` command to create feature spec
4. **Planning**: `/plan` command to create implementation plan
5. **Tasks**: `/tasks` command to generate task breakdown
6. **Implementation**: `/implement` command for automated execution
7. **Validation**: Verify all tests pass and features work

### Agent-Assisted Development
1. **Agent Setup**: Verify `.claude/agents/` populated during init
2. **Context Sharing**: Agents have access to project specs and plans
3. **Scaffolding**: Generate new agent outputs using scripts
4. **Cross-Assistant**: Test with multiple AI assistants configured

### Error Recovery
1. **Failed Task**: Test `/implement` with intentionally failing task
2. **Resume**: Verify ability to resume from failed point
3. **Manual Fallback**: Use `/guide` when automation fails
4. **Constitution Conflicts**: Test merging with existing guidelines

## Performance Expectations
- Command execution: < 2 seconds
- Template rendering: < 500ms
- Agent scaffolding: < 1 second
- Large task lists (50+ tasks): < 10 seconds processing

## Validation Criteria
- [ ] All commands respond within performance thresholds
- [ ] Templates render without errors
- [ ] Agent files created in correct locations
- [ ] Task execution follows proper dependency order
- [ ] Error handling provides actionable feedback
- [ ] Cross-platform compatibility (Windows/macOS/Linux)
- [ ] Backward compatibility with existing projects
- [ ] Type safety maintained throughout system

## Troubleshooting Common Issues

### `/implement` fails with "Prerequisites not met"
- Verify constitution.md exists
- Check that spec.md, plan.md, and tasks.md are complete
- Run `specifyx check` to validate setup

### Agent templates not found
- Ensure assistant supports agents (check with `specifyx check`)
- Verify proper directory permissions
- Re-run `specifyx init` if templates missing

### System prompt guide empty
- Check assistant name spelling
- Verify assistant is properly configured
- Use `--include-examples` flag for detailed output

### Cross-platform script failures
- Ensure Python 3.11+ installed
- Check file permissions on `.specify/scripts/`
- Use `python` instead of `python3` on Windows

This quickstart provides the foundation for testing and validating the enhanced commands and agent support system.
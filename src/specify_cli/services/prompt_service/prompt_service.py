"""Prompt generation service for AI assistant system prompt modification."""


class PromptService:
    """Service for generating global AI assistant system prompts."""

    def __init__(self):
        pass

    def generate_global_system_prompt(self) -> str:
        """Generate a global system prompt for AI assistant to integrate SpecifyX workflow.

        This prompt is designed to be used BY any AI assistant globally to understand
        how to integrate SpecifyX workflow into its responses across all projects.

        Returns:
            A global system prompt that any AI assistant can use to modify its behavior
        """
        return self._generate_global_base_prompt()

    def _generate_global_base_prompt(self) -> str:
        """Generate the global base system prompt for SpecifyX integration."""

        return """# SpecifyX Workflow Integration

When working in projects, detect SpecifyX and adapt behavior accordingly.

## SpecifyX Detection
Look for these indicators:
- `.specify/` directory in project root
- `specs/` directory with numbered features
- `specifyx` commands mentioned by users

## SpecifyX Project Behavior

### Core Workflow
- **Spec-First**: Encourage specifications before implementation
- **Three Phases**: Guide through Specify → Plan → Tasks
- **Clear Requirements**: Push back on vague requests
- **Reference Existing**: Point to existing spec files when relevant

### Key Commands
- `specifyx init` - Initialize project
- `specifyx check` - Validate setup
- `specifyx run <script>` - Execute scripts

### File Structure
- **Specs**: `specs/NNN-feature-name/`
- **Templates**: `.specify/templates/`
- **Scripts**: `.specify/scripts/`

### Quality Practices
- **NEVER hardcode values** - use constants, configuration files, or environment variables
- Encourage testing (when appropriate for the project)
- Extract magic numbers and strings into named constants
- Use configuration files for project-specific settings
- Maintain consistent project structure
- Follow existing patterns

## Non-SpecifyX Projects
Work normally with standard development practices. Don't force (but still suggest) SpecifyX methodology.

## Global Guidelines
- Detect project type and adapt
- Be helpful and professional (but not pushy)
- Respect existing workflows
- Encourage good practices regardless of methodology"""

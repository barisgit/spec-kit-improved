# Tasks: Enhanced Commands and Agent Support System (SIMPLIFIED)

**Feature**: Enhanced Commands and Agent Support System (005)
**Status**: Leveraging Existing Infrastructure - Much Simpler Than Originally Planned!

## Analysis Results
After examining the existing codebase, this feature is **much simpler** than originally planned:
- ✅ **Slash commands** = Just Jinja2 templates in `templates/commands/` (auto-rendered during init)
- ✅ **Agent support** = Already exists! Claude provider has `agent_files=TemplateConfig(directory=".claude/agents")`
- ✅ **Template system** = Robust existing infrastructure with TemplateService
- ✅ **CLI integration** = Well-established patterns in core/app.py

## Completed: Phase 3.1 Setup
- [x] T001 Project structure analysis - excellent existing infrastructure identified
- [x] T002 Dependencies - no new dependencies needed, rich/jinja2/typer already available
- [x] T003 Linting - existing ruff configuration sufficient for .j2 templates
- [x] T004 .gitignore - .specify/ already properly configured

## Phase 3.2: Core Implementation (SIMPLIFIED) ✅ COMPLETED

### Slash Command Templates (Just 3 Jinja2 files - auto-render during init)
- [x] T005 [P] Create implement.md.j2 slash command template in src/specify_cli/templates/commands/implement.md.j2
- [x] T006 [P] Create constitution.md.j2 slash command template in src/specify_cli/templates/commands/constitution.md.j2
- [x] T007 [P] Create guide.md.j2 slash command template in src/specify_cli/templates/commands/guide.md.j2

### Agent Prompt Templates (For assistant directories like .claude/agents/ - 6 files)
- [x] T008 [P] Create code-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/code-reviewer.md.j2
- [x] T009 [P] Create documentation-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/documentation-reviewer.md.j2
- [x] T010 [P] Create implementer agent prompt template in src/specify_cli/templates/agent-prompts/implementer.md.j2
- [x] T011 [P] Create spec-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/spec-reviewer.md.j2
- [x] T012 [P] Create architecture-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/architecture-reviewer.md.j2
- [x] T013 [P] Create test-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/test-reviewer.md.j2

### Agent Runtime Templates (For .specify/agent-templates/ - 8 files)
- [x] T014 [P] Create code-reviewer runtime template in src/specify_cli/templates/agent-templates/code-reviewer.md.j2
- [x] T015 [P] Create documentation-reviewer runtime template in src/specify_cli/templates/agent-templates/documentation-reviewer.md.j2
- [x] T016 [P] Create implementer runtime template in src/specify_cli/templates/agent-templates/implementer.md.j2
- [x] T017 [P] Create spec-reviewer runtime template in src/specify_cli/templates/agent-templates/spec-reviewer.md.j2
- [x] T018 [P] Create architecture-reviewer runtime template in src/specify_cli/templates/agent-templates/architecture-reviewer.md.j2
- [x] T019 [P] Create test-reviewer runtime template in src/specify_cli/templates/agent-templates/test-reviewer.md.j2
- [x] T020 [P] Create generic-agent runtime template in src/specify_cli/templates/agent-templates/generic-agent.md.j2
- [x] T021 [P] Create context template in src/specify_cli/templates/agent-templates/context.md.j2

### Scaffold Script (Main workflow logic)
- [x] T022 Create scaffold-agent.py script in src/specify_cli/templates/scripts/scaffold-agent.py.j2

### Get-Prompt Command (Only real code needed)
- [x] T023 Create get-prompt command directory src/specify_cli/commands/get_prompt/
- [x] T024 Implement get-prompt command in src/specify_cli/commands/get_prompt/get_prompt.py
- [x] T025 Register get-prompt command in src/specify_cli/core/app.py

### Integration Updates (Leverage existing systems)
- [x] T026 Update TemplateService folder mappings to include agent-prompts and agent-templates
- [x] T027 Verify Claude provider agent support works with new templates

## Phase 3.3: Testing & Validation
- [ ] T028 [P] Test slash command template rendering during init
- [ ] T029 [P] Test agent template generation for Claude
- [ ] T030 [P] Test scaffold-agent.py script functionality
- [ ] T031 Test get-prompt command for all assistant types
- [ ] T032 Test complete agent workflow (scaffold → populate → read)

## Dependencies (Simplified)
**Sequential:**
- Setup (T001-T004) → Core Implementation (T005-T027) → Testing (T028-T032)

**Parallel Groups:**
- **Slash Commands**: T005-T007 (3 different template files)
- **Agent Prompt Templates**: T008-T013 (6 different template files)
- **Agent Runtime Templates**: T014-T021 (8 different template files)
- **Testing**: T028-T032 (different test scenarios)

## Massive Simplification Notes
**What we DON'T need** (originally planned but unnecessary):
- ❌ No separate AgentService, PromptService, ImplementService, ConstitutionService
- ❌ No data models (ImplementationTask, ProjectConstitution, etc.)
- ❌ No complex TDD test suites for services that don't exist
- ❌ No integration layer updates (AssistantProvider already supports agents)
- ❌ No config.toml updates (existing config sufficient)

**What we DO need** (actual implementation):
- ✅ 3 slash command templates (Jinja2 files)
- ✅ 14 agent templates (6 prompts + 8 runtime templates)
- ✅ 1 scaffold script (Python with template discovery)
- ✅ 1 get-prompt command (actual CLI command code)
- ✅ Small template system integration updates

**Total**: ~19 template files + 1 Python command + minor integration = **Much simpler than the 60-task original plan!**

## Implementation Strategy
1. **Create all templates in parallel** (T005-T022) - they're independent Jinja2 files
2. **Implement get-prompt command** (T023-T025) - standard Typer command
3. **Update template mappings** (T026-T027) - minor changes to existing system
4. **Test everything** (T028-T032) - verify templates render and workflow works

The existing SpecifyX infrastructure is so robust that most of this feature "just works" by adding the right template files!
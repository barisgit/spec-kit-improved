# Tasks: Enhanced Commands and Agent Support System

**Feature**: Enhanced Commands and Agent Support System (005)
**Input**: Design documents from `specs/005-feature-enhanced-commands-and-agents/`
**Prerequisites**: spec.md, plan.md, data-model.md, contracts/

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup & Dependencies
- [ ] T001 Create project structure for new services and commands per plan.md
- [ ] T002 Add new dependencies to pyproject.toml: enhanced rich features, advanced template processing
- [ ] T003 [P] Configure new linting rules for agent template validation
- [ ] T004 [P] Update .gitignore for new .specify/agents/ and .specify/agent-templates/ directories

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Different Contract Files - Can Run Parallel)
- [ ] T005 [P] Contract test get-prompt command in tests/contract/test_get_prompt_command.py
- [ ] T006 [P] Contract test agent template rendering in tests/contract/test_agent_templates.py
- [ ] T007 [P] Contract test scaffold script generation in tests/contract/test_scaffold_scripts.py
- [ ] T008 [P] Contract test slash command template generation in tests/contract/test_slash_commands.py

### Service Tests (Different Service Files - Can Run Parallel)
- [ ] T009 [P] Service test AgentService in tests/services/test_agent_service.py
- [ ] T010 [P] Service test PromptService in tests/services/test_prompt_service.py
- [ ] T011 [P] Service test ImplementService in tests/services/test_implement_service.py
- [ ] T012 [P] Service test ConstitutionService in tests/services/test_constitution_service.py

### Integration Tests (Complex Workflows)
- [ ] T013 [P] Integration test full agent workflow (scaffold → populate → read) in tests/integration/test_agent_workflow.py
- [ ] T014 [P] Integration test implement command execution with task dependencies in tests/integration/test_implement_workflow.py
- [ ] T015 [P] Integration test constitution command creation and validation in tests/integration/test_constitution_workflow.py
- [ ] T016 [P] Integration test get-prompt command for all assistant types in tests/integration/test_prompt_generation.py

## Phase 3.3: Data Models (ONLY after tests are failing)
- [ ] T017 [P] Implement ImplementationTask model in src/specify_cli/models/implementation_task.py
- [ ] T018 [P] Implement ProjectConstitution model in src/specify_cli/models/project_constitution.py
- [ ] T019 [P] Implement AgentTemplate model in src/specify_cli/models/agent_template.py
- [ ] T020 [P] Implement AgentContext model in src/specify_cli/models/agent_context.py
- [ ] T021 [P] Implement SystemPromptGuide model in src/specify_cli/models/system_prompt_guide.py

## Phase 3.4: Core Services (Dependencies: Data Models Complete)
- [ ] T022 Implement AgentService in src/specify_cli/services/agent_service/agent_service.py
- [ ] T023 Implement PromptService in src/specify_cli/services/prompt_service/prompt_service.py
- [ ] T024 Implement ImplementService in src/specify_cli/services/implement_service/implement_service.py
- [ ] T025 Implement ConstitutionService in src/specify_cli/services/constitution_service/constitution_service.py

## Phase 3.5: Commands Implementation (Dependencies: Services Complete)
- [ ] T026 Implement get-prompt command in src/specify_cli/commands/get_prompt/get_prompt.py
- [ ] T027 Register get-prompt command in src/specify_cli/core/app.py
- [ ] T028 [P] Create implement.md.j2 slash command template in src/specify_cli/templates/commands/implement.md.j2
- [ ] T029 [P] Create constitution.md.j2 slash command template in src/specify_cli/templates/commands/constitution.md.j2
- [ ] T030 [P] Create guide.md.j2 slash command template in src/specify_cli/templates/commands/guide.md.j2

## Phase 3.6: Agent Templates System (Dependencies: AgentService Complete)
- [ ] T031 [P] Create code-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/code-reviewer.md.j2
- [ ] T032 [P] Create documentation-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/documentation-reviewer.md.j2
- [ ] T033 [P] Create implementer agent prompt template in src/specify_cli/templates/agent-prompts/implementer.md.j2
- [ ] T034 [P] Create spec-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/spec-reviewer.md.j2
- [ ] T035 [P] Create architecture-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/architecture-reviewer.md.j2
- [ ] T036 [P] Create test-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/test-reviewer.md.j2

## Phase 3.7: Agent Runtime Templates (Dependencies: Agent Prompt Templates Complete)
- [ ] T037 [P] Create code-reviewer runtime template in src/specify_cli/templates/agent-templates/code-reviewer.md.j2
- [ ] T038 [P] Create documentation-reviewer runtime template in src/specify_cli/templates/agent-templates/documentation-reviewer.md.j2
- [ ] T039 [P] Create implementer runtime template in src/specify_cli/templates/agent-templates/implementer.md.j2
- [ ] T040 [P] Create spec-reviewer runtime template in src/specify_cli/templates/agent-templates/spec-reviewer.md.j2
- [ ] T041 [P] Create architecture-reviewer runtime template in src/specify_cli/templates/agent-templates/architecture-reviewer.md.j2
- [ ] T042 [P] Create test-reviewer runtime template in src/specify_cli/templates/agent-templates/test-reviewer.md.j2
- [ ] T043 [P] Create generic-agent runtime template in src/specify_cli/templates/agent-templates/generic-agent.md.j2
- [ ] T044 [P] Create context template in src/specify_cli/templates/agent-templates/context.md.j2

## Phase 3.8: Scaffold Scripts (Dependencies: Runtime Templates Complete)
- [ ] T045 Create main scaffold-agent.py script in src/specify_cli/templates/scripts/scaffold-agent.py
- [ ] T046 Create agent interactive selection UI in src/specify_cli/services/agent_service/selection.py

## Phase 3.9: Integration & Configuration (Dependencies: All Templates Complete)
- [ ] T047 Update AssistantProvider integration for agent support in existing src/specify_cli/assistants/registry.py
- [ ] T048 Update init command to handle agent template generation in src/specify_cli/commands/init/init.py
- [ ] T049 Update refresh-templates command for agent templates in src/specify_cli/commands/refresh/refresh.py
- [ ] T050 Add agent configuration section to default config.toml in src/specify_cli/templates/config/config.toml.j2

## Phase 3.10: Error Handling & Validation
- [ ] T051 Add task dependency validation in ImplementService task execution
- [ ] T052 Add template rendering validation for all agent templates
- [ ] T053 Add error recovery for failed implement command execution
- [ ] T054 Add constitution conflict detection and resolution

## Phase 3.11: Polish & Documentation
- [ ] T055 [P] Create comprehensive unit tests for edge cases in tests/unit/
- [ ] T056 [P] Performance tests for template rendering (<500ms) in tests/performance/test_template_performance.py
- [ ] T057 [P] Update service documentation in src/specify_cli/services/*/docs.mdx
- [ ] T058 [P] Update command documentation in src/specify_cli/commands/*/docs.mdx
- [ ] T059 Run quickstart.md validation scenarios
- [ ] T060 Remove code duplication and refactor shared utilities

## Dependencies
**Sequential Dependencies:**
- Setup (T001-T004) → Tests (T005-T016)
- Tests (T005-T016) → Models (T017-T021)
- Models (T017-T021) → Services (T022-T025)
- Services (T022-T025) → Commands (T026-T030)
- AgentService (T022) → Agent Templates (T031-T044)
- Runtime Templates (T037-T044) → Scaffold Scripts (T045-T046)
- All Templates (T031-T044) → Integration (T047-T050)
- Integration (T047-T050) → Validation (T051-T054)
- All Implementation → Polish (T055-T060)

**Parallel Groups:**
- Contract Tests: T005-T008 (different contract files)
- Service Tests: T009-T012 (different service files)
- Integration Tests: T013-T016 (different workflow files)
- Data Models: T017-T021 (different model files)
- Slash Commands: T028-T030 (different template files)
- Agent Prompt Templates: T031-T036 (different agent files)
- Agent Runtime Templates: T037-T044 (different template files)

## Parallel Execution Examples

### Tests Phase (T005-T016)
```bash
# Contract tests - can run all together
Task: "Contract test get-prompt command in tests/contract/test_get_prompt_command.py"
Task: "Contract test agent template rendering in tests/contract/test_agent_templates.py"
Task: "Contract test scaffold script generation in tests/contract/test_scaffold_scripts.py"
Task: "Contract test slash command template generation in tests/contract/test_slash_commands.py"

# Service tests - can run all together
Task: "Service test AgentService in tests/services/test_agent_service.py"
Task: "Service test PromptService in tests/services/test_prompt_service.py"
Task: "Service test ImplementService in tests/services/test_implement_service.py"
Task: "Service test ConstitutionService in tests/services/test_constitution_service.py"
```

### Agent Templates Phase (T031-T036)
```bash
# All agent prompt templates - different files, no dependencies
Task: "Create code-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/code-reviewer.md.j2"
Task: "Create documentation-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/documentation-reviewer.md.j2"
Task: "Create implementer agent prompt template in src/specify_cli/templates/agent-prompts/implementer.md.j2"
Task: "Create spec-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/spec-reviewer.md.j2"
Task: "Create architecture-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/architecture-reviewer.md.j2"
Task: "Create test-reviewer agent prompt template in src/specify_cli/templates/agent-prompts/test-reviewer.md.j2"
```

## Validation Checklist
**GATE: Check before marking feature complete**

- [ ] All contract tests have implementation and pass
- [ ] All data models have corresponding service tests
- [ ] All tests written before implementation (TDD enforced)
- [ ] All parallel tasks truly independent (different files)
- [ ] Each task specifies exact file path
- [ ] No parallel task modifies same file as another
- [ ] Agent workflow (scaffold → populate → read) functional
- [ ] All six agent types properly templated
- [ ] Assistant integration works for supported assistants
- [ ] Template rendering performance meets <500ms requirement
- [ ] All slash commands functional and documented
- [ ] Error handling comprehensive with recovery guidance
- [ ] Constitution integration non-conflicting
- [ ] Cross-platform compatibility maintained

## Implementation Notes
- Focus on simplicity and reusability over complexity
- Leverage existing SpecifyX infrastructure (TemplateService, ConfigService, ProjectManager)
- Each service should be independently testable
- Agent templates must be valid Jinja2 and render without errors
- Maintain backward compatibility with existing projects
- All new commands must integrate with existing CLI structure
- Follow TDD strictly - no implementation without failing tests first
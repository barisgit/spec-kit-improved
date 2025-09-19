# Implementation Plan: Feature/enhanced-Commands-And-Agents

**Branch**: `feature/enhanced-commands-and-agents` | **Date**: 2025-09-18 | **Spec**: [-feature/enhanced-commands-and-agents/spec.md](/spec.md)
**Input**: Feature specification from `/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file.
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Enhance SpecifyX with three new slash commands (`/implement`, `/constitution`, `/guide`) and comprehensive agent support system. The feature enables automated task execution, project governance, and structured AI agent integration. Agent context sharing works by: SpecifyX scaffolds empty report outlines in `.specify/agents/`, external agents populate those reports, and the orchestrator/other agents read completed reports for cross-workflow context. User input: "perfect continue with plan"

## Technical Context
**Project**: spec-kit-improved
**Language/Version**: Python 3.11+
**Primary Dependencies**: Typer, Rich, Jinja2, Dynaconf, HTTPX, Pydantic
**Storage**: File-based (TOML config, Markdown templates, JSON data)
**Testing**: pytest, pytest-asyncio, pytest-cov
**Target Platform**: Linux/macOS/Windows (cross-platform CLI)
**Project Type**: single (CLI application with modular services)
**Performance Goals**: <2s command execution, <500ms template rendering, CLI responsiveness
**Constraints**: Cross-platform compatibility, backward compatibility with existing projects, no external service dependencies
**Scale/Scope**: Enterprise development teams, 100+ features per project, multi-assistant workflows

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (CLI application extending existing SpecifyX)
- Using framework directly? [x] (Direct Typer commands, no wrappers)
- Single data model? [x] (Configuration models, task models - no DTOs)
- Avoiding patterns? [x] (Direct service calls, no Repository pattern)

**Architecture**:
- EVERY feature as library? [x] (Commands, services, templates as importable modules)
- Libraries listed: commands.implement, commands.constitution, commands.guide, services.agent_service, services.prompt_service
- CLI per library: [x] (Each command has --help/--version support via Typer)
- Library docs: [x] (Docstrings + docs.mdx files planned)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? [x] (Tests written first, must fail)
- Git commits show tests before implementation? [x] (Constitution requirement)
- Order: Contract→Integration→E2E→Unit strictly followed? [x] (Template contracts, command integration, unit tests)
- Real dependencies used? [x] (Real file system, real templates, no mocks for core functionality)
- Integration tests for: new libraries, contract changes, shared schemas? [x] (New command services, agent template changes)
- FORBIDDEN: Implementation before test, skipping RED phase [x]

**Observability**:
- Structured logging included? [x] (Rich console output, structured progress tracking)
- Frontend logs → backend? N/A (CLI application)
- Error context sufficient? [x] (Detailed error reporting with context)

**Versioning**:
- Version number assigned? [x] (Current: 0.3.0, increment BUILD for this feature)
- BUILD increments on every change? [x] (pyproject.toml version management)
- Breaking changes handled? [x] (Backward compatible command addition, migration for agent templates)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh [claude|gemini|copilot]` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: research.md, data-model.md, /contracts/*, quickstart.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each command template → command implementation task
- Each service interface → service implementation task [P]
- CLI command registration → integration task
- Template system integration → template rendering test task
- Agent scaffolding system → agent workflow test task (scaffold → populate → read cycle)

**Ordering Strategy**:
- TDD order: Tests before implementation
- Foundation first: Data models, then services, then commands
- Service layer tasks can run in parallel [P]
- Integration tests after unit tests
- End-to-end testing last

**Task Phases**:
1. **Setup**: Project structure, dependencies, configuration updates
2. **Foundation**: Data models, service interfaces, type definitions
3. **Core Services**: Agent service, prompt service, implement service [P]
4. **Commands**: CLI command implementations (get-prompt, register new slash commands)
5. **Integration**: Template system integration, assistant provider updates
6. **Testing**: Comprehensive test suite, quickstart validation

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
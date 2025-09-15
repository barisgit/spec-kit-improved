# Implementation Plan: Feature/type-Safe-Ai-Assistant-Organization

**Branch**: `feature/modular-ai-assistant-architecture` | **Date**: 2025-09-15 | **Spec**: [-feature/modular-ai-assistant-architecture/spec.md](/spec.md)
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
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md for Claude Code.
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
Reorganize SpecifyX's AI assistant code from scattered files into organized assistant folders with type-safe injection points and auto-documentation. Replace template conditionals with clean injection points while maintaining full type safety and automatic documentation generation.

## Technical Context
**Project**: spec-kit-improved
**Language/Version**: Python 3.11+
**Primary Dependencies**: typer, rich, jinja2, dynaconf, platformdirs, importlib.resources
**Storage**: File system (assistant folder structure, typed configuration files)
**Testing**: pytest with type checking (mypy/pyright)
**Target Platform**: Cross-platform (Linux, macOS, Windows via Python)
**Project Type**: single (CLI tool)
**Performance Goals**: Template rendering <100ms (no degradation), Build-time validation
**Constraints**: Backward compatibility required, no template duplication, maintain current performance
**Scale/Scope**: 4-6 AI assistants initially, extensible via typed interfaces

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (CLI tool only)
- Using framework directly? YES (direct typer/rich usage)
- Single data model? YES (assistant configuration + injection points)
- Avoiding patterns? YES (simple folder organization, static imports)

**Architecture**:
- EVERY feature as library? YES (assistant organization as enhanced service)
- Libraries listed: assistant_registry (static registry), injection_system (type-safe injections)
- CLI per library: integrated into main CLI with enhanced help/documentation
- Library docs: YES, auto-generated from typed definitions

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? YES
- Git commits show tests before implementation? YES
- Order: Contract→Integration→E2E→Unit strictly followed? YES
- Real dependencies used? YES (actual file system operations)
- Integration tests for: assistant organization, injection points, template rendering
- FORBIDDEN: Implementation before test, skipping RED phase - ENFORCED

**Observability**:
- Structured logging included? YES (assistant loading, injection validation)
- Frontend logs → backend? N/A (CLI tool)
- Error context sufficient? YES (type validation failures, missing injections)

**Versioning**:
- Version number assigned? YES (follows existing SpecifyX versioning)
- BUILD increments on every change? YES
- Breaking changes handled? YES (backward compatibility required, migration path for existing configs)

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
# Single project structure (CLI tool)
src/specify_cli/
├── assistants/          # NEW: Organized assistant modules
│   ├── __init__.py     # Registry with static imports
│   ├── claude/
│   │   ├── config.py   # Typed configuration
│   │   └── injections.py # Type-safe injection points
│   ├── gemini/
│   └── cursor/
├── models/             # Enhanced with assistant types
├── services/           # Enhanced template service
├── templates/          # Shared templates with injection points
└── core/              # CLI integration

tests/
├── contract/          # Assistant interface contracts
├── integration/       # Template rendering + assistant integration
└── unit/             # Type validation + individual components
```

**Structure Decision**: Single project (CLI tool) with enhanced assistant organization

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Type safety implementation patterns for dynamic configurations
   - Template injection point design patterns
   - Python type checking integration with build process
   - Documentation auto-generation from typed definitions

2. **Generate and dispatch research agents**:
   ```
   Task: "Research Python type safety patterns for plugin-like configurations"
   Task: "Find template injection patterns that maintain type safety"
   Task: "Research auto-documentation generation from Python type annotations"
   Task: "Investigate build-time validation patterns for Python CLI tools"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - AssistantConfiguration (typed structure for assistant definitions)
   - InjectionRegistry (type-safe mapping of injection points)
   - TemplateContext (enhanced context with assistant injections)
   - AssistantModule (folder structure with typed interfaces)

2. **Generate interface contracts** from functional requirements:
   - AssistantConfig interface with required fields and validation
   - InjectionProvider interface for type-safe injection points
   - TemplateRenderer interface with injection support
   - Output TypedDict/Protocol definitions to `/contracts/`

3. **Generate contract tests** from contracts:
   - Assistant configuration validation tests
   - Injection point type safety tests
   - Template rendering with injections tests
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Assistant folder organization scenarios
   - Type-safe injection point scenarios
   - Auto-documentation generation scenarios
   - Quickstart test = organization validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh [claude|gemini|copilot]` for your AI assistant
   - Add assistant organization and type safety context
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Assistant configuration interfaces → contract test tasks [P]
- Type safety validation → validation test tasks [P]
- Injection point system → integration test tasks
- Template enhancement → rendering test tasks
- Folder organization → file structure tasks
- Implementation tasks following TDD red-green-refactor

**Ordering Strategy**:
- TDD order: Contract tests → Integration tests → Unit tests → Implementation
- Dependency order: Types → Configuration → Injections → Templates → Integration
- Organization tasks: Create folders → Move files → Update imports → Validate
- Mark [P] for parallel execution (independent assistant folders)

**Key Task Categories**:
1. **Type System** (3-4 tasks): Configuration types, injection interfaces, validation
2. **Assistant Organization** (4-5 tasks): Folder creation, file movement, import updates
3. **Injection System** (3-4 tasks): Injection points, template integration, type safety
4. **Template Enhancement** (2-3 tasks): Remove conditionals, add injection points
5. **Documentation Auto-generation** (2-3 tasks): Type-based docs, assistant discovery
6. **Integration & Testing** (3-4 tasks): End-to-end validation, backward compatibility

**Estimated Output**: 18-25 numbered, ordered tasks in tasks.md

**Performance Requirements**:
- Template rendering benchmarks (maintain current speed)
- Type checking integration validation
- Build-time validation implementation

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, type checking validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (None) | Simple folder organization | No constitutional violations |

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
- [x] Initial Constitution Check: PASS (simple organization, no over-engineering)
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
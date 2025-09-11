# Implementation Plan: Feature/docs-By-Code-Docusaurus

**Branch**: `feature/docs-by-code-docusaurus` | **Date**: 2025-09-10 | **Spec**: [-feature/docs-by-code-docusaurus/spec.md](/spec.md)
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
Implement a documentation-by-code pattern where documentation files live alongside their corresponding code files, with automatic synchronization to a Docusaurus-based documentation website. This ensures documentation stays current and maintainable by keeping it close to the code it describes.

## Technical Context
**Project**: spec-kit-improved  
**Language/Version**: Python 3.11+ (main codebase), TypeScript/Node.js 18+ (docs sync)  
**Primary Dependencies**: Typer, Jinja2, Rich (Python); Docusaurus 3.x, React 18, chokidar (Documentation)  
**Storage**: File system (markdown/MDX files), Git for version control  
**Testing**: pytest for Python components, Jest/Vitest for TypeScript sync tests  
**Target Platform**: Cross-platform CLI (Windows, macOS, Linux), Web browser for docs
**Project Type**: single (Python CLI with separate docs project)  
**Performance Goals**: <100ms sync time for individual files, <5s for full sync  
**Constraints**: <50MB memory for sync process, incremental updates required  
**Scale/Scope**: ~20 commands, ~10 services, ~15 guide documents

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (Python CLI + Docusaurus docs) ✅ (max 3)
- Using framework directly? Yes - Docusaurus without wrappers ✅
- Single data model? Yes - documentation metadata only ✅
- Avoiding patterns? Yes - direct file operations, no abstraction layers ✅

**Architecture**:
- EVERY feature as library? Yes - sync as TypeScript module in docs ✅
- Libraries listed: 
  - `docs/scripts/sync-docs.ts`: TypeScript sync script (like kilm)
  - `docs_site`: Docusaurus documentation website with embedded sync
- CLI per library: npm scripts - `docs:sync`, `docs:watch`, `docs:clean` ✅
- Library docs: MDX format with llms.txt generation planned ✅

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes - tests written first ✅
- Git commits show tests before implementation? Will be enforced ✅
- Order: Contract→Integration→E2E→Unit strictly followed? Yes ✅
- Real dependencies used? Yes - actual file system, real Docusaurus ✅
- Integration tests for: sync process, file watching, validation ✅
- FORBIDDEN: Implementation before test - understood ✅

**Observability**:
- Structured logging included? Yes - sync operations logged ✅
- Frontend logs → backend? N/A (documentation site only) ✅
- Error context sufficient? Yes - file paths and error details ✅

**Versioning**:
- Version number assigned? Will use SpecifyX version ✅
- BUILD increments on every change? Via SpecifyX releases ✅
- Breaking changes handled? Documentation versioning built-in ✅

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

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract interface → TypeScript implementation task
- Each test suite → test implementation task (TDD - tests first!)
- Docusaurus setup and configuration tasks
- Sync script implementation following kilm pattern

**Specific Task Categories**:
1. **Docusaurus Setup** (3-4 tasks)
   - Initialize Docusaurus with TypeScript
   - Configure docusaurus.config.js
   - Set up sidebar structure
   - Add SpecifyX branding

2. **TypeScript Sync Script** (8-10 tasks) [P]
   - Create sync-docs.ts main structure
   - Implement file discovery with glob
   - Implement frontmatter processing
   - Implement path mapping logic
   - Add file watching with chokidar
   - Add cleanup functionality
   - Add validation logic
   - Create CLI argument parsing

3. **Testing** (5-6 tasks)
   - Set up Vitest configuration
   - Write file discovery tests
   - Write frontmatter processing tests
   - Write path mapping tests
   - Write integration tests
   - Write quickstart validation tests

4. **Documentation Creation** (4-5 tasks) [P]
   - Create sample command docs
   - Create sample service docs
   - Create guide documents
   - Migrate existing content

5. **Integration** (3-4 tasks)
   - Configure pnpm scripts
   - Set up GitHub Actions
   - Create deployment workflow
   - Add pre-commit hooks

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Docusaurus setup → Sync script → Documentation
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

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
- [x] Phase 3: Tasks generated (/tasks command) - 37 tasks created
- [x] Phase 4: Implementation complete - TypeScript sync script working
- [x] Phase 5: Validation passed - 57 tests passing, sync processing 4 files

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)
- [x] TDD approach followed - all tests written first and failed initially
- [x] TypeScript sync script implemented following kilm pattern
- [x] pnpm used as package manager per user request

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
# Tasks: 003-Feature-Docs-By-Code-Docusaurus

**Input**: Design documents from `specs/003-feature-docs-by-code-docusaurus/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: TypeScript/Node.js stack, Docusaurus, pnpm
2. Load design documents:
   → data-model.md: DocumentationFile, FrontmatterData entities
   → contracts/sync-service.ts: TypeScript interfaces
   → research.md: Technology decisions (chokidar, gray-matter)
   → quickstart.md: Validation scenarios
3. Generate tasks by category:
   → Setup: Docusaurus init, dependencies
   → Tests: Vitest setup, contract tests
   → Core: Sync script implementation
   → Documentation: Sample docs creation
   → Integration: pnpm scripts, GitHub Actions
4. Apply TDD rules:
   → Tests before implementation
   → All tests must fail initially
5. Number tasks sequentially (T001, T002...)
6. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [x] T001 Create docs directory and initialize Docusaurus with TypeScript template
- [x] T002 Install sync dependencies: pnpm add -D chokidar gray-matter glob tsx concurrently @types/node
- [x] T003 Configure docusaurus.config.js with SpecifyX branding and navigation structure
- [x] T004 Create docs/scripts directory for TypeScript sync script

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [x] T005 Set up Vitest configuration in docs/vitest.config.ts
- [x] T006 [P] Write file discovery tests in docs/scripts/__tests__/file-discovery.test.ts
- [x] T007 [P] Write frontmatter processing tests in docs/scripts/__tests__/frontmatter.test.ts
- [x] T008 [P] Write path mapping tests in docs/scripts/__tests__/path-mapper.test.ts
- [x] T009 [P] Write sync service integration tests in docs/scripts/__tests__/sync-service.test.ts
- [x] T010 Run all tests and verify they FAIL (no implementation yet)

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### TypeScript Sync Script Components
- [x] T011 Create main sync-docs.ts with CLI argument parsing using process.argv
- [x] T012 [P] Implement file discovery module in docs/scripts/lib/file-discovery.ts using glob
- [x] T013 [P] Implement frontmatter processor in docs/scripts/lib/frontmatter-processor.ts using gray-matter
- [x] T014 [P] Implement path mapper in docs/scripts/lib/path-mapper.ts for source→dest mapping
- [x] T015 [P] Implement file operations in docs/scripts/lib/file-operations.ts for read/write/checksum
- [x] T016 Implement sync service in docs/scripts/lib/sync-service.ts orchestrating all modules
- [x] T017 Add file watching with chokidar in docs/scripts/lib/watcher.ts
- [x] T018 Add cleanup functionality for orphaned files in sync-service.ts
- [x] T019 Add validation logic for MDX files in docs/scripts/lib/validator.ts

### Documentation Content
- [x] T020 [P] Create sample command docs: src/specify_cli/commands/init/docs.mdx
- [x] T021 [P] Create sample command docs: src/specify_cli/commands/check/docs.mdx
- [x] T022 [P] Create sample service docs: src/specify_cli/services/template_service/docs.mdx
- [ ] T023 [P] Create sample service docs: src/specify_cli/services/config_service/docs.mdx
- [x] T024 [P] Create guide docs: src/specify_cli/guides/getting-started.mdx
- [ ] T025 [P] Create guide docs: src/specify_cli/guides/configuration.mdx

## Phase 3.4: Integration
- [x] T026 Configure pnpm scripts in docs/package.json (sync, sync:watch, sync:clean, dev, build)
- [ ] T027 Test initial sync: pnpm sync and verify files appear in correct locations
- [ ] T028 Test file watching: pnpm dev and modify a doc file
- [ ] T029 Test cleanup: Delete source file and run pnpm sync:clean
- [ ] T030 Configure Docusaurus sidebar in docs/sidebars.js for auto-generated structure
- [ ] T031 Add custom CSS for SpecifyX branding in docs/src/css/custom.css

## Phase 3.5: Polish & Deployment
- [ ] T032 [P] Add unit tests for edge cases in docs/scripts/__tests__/edge-cases.test.ts
- [ ] T033 Performance test: Ensure sync completes in <5s for all docs
- [ ] T034 [P] Create GitHub Actions workflow in .github/workflows/docs.yml
- [ ] T035 [P] Update main README.md with documentation section
- [ ] T036 Run quickstart.md validation steps end-to-end
- [ ] T037 Build production site: pnpm build and verify output

## Dependencies
- Setup (T001-T004) must complete first
- Tests (T005-T010) before implementation (T011-T019)
- T011 blocks T016 (main script before service)
- T016 requires T012-T015 (service needs all modules)
- Documentation (T020-T025) can run parallel after setup
- Integration (T026-T031) requires implementation
- Polish (T032-T037) runs last

## Parallel Execution Examples
```bash
# After setup, launch test writing in parallel:
Task: "Write file discovery tests"
Task: "Write frontmatter tests"
Task: "Write path mapper tests"
Task: "Write integration tests"

# Implementation modules can be parallel:
Task: "Implement file discovery"
Task: "Implement frontmatter processor"
Task: "Implement path mapper"
Task: "Implement file operations"

# Documentation creation fully parallel:
Task: "Create init command docs"
Task: "Create check command docs"
Task: "Create template service docs"
Task: "Create getting-started guide"
```

## Success Criteria
- All tests pass (initially fail, then pass after implementation)
- Sync completes without errors
- File watching updates docs in real-time
- Cleanup removes orphaned files
- Production build succeeds
- Documentation accessible at localhost:3000

## Notes
- Use TypeScript strict mode for all scripts
- Follow kilm's sync-docs.ts pattern for consistency
- Preserve .md vs .mdx extensions during sync
- Add proper error handling with meaningful messages
- Use structured logging for debugging

## Validation Checklist
*GATE: Checked before marking complete*

- [ ] All contract interfaces have implementations
- [ ] All test suites pass
- [ ] Quickstart guide validates successfully
- [ ] No TypeScript errors or warnings
- [ ] Documentation builds without errors
- [ ] File watching works reliably
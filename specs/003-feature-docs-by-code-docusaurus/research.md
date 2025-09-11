# Phase 0: Research - Documentation-by-Code with Docusaurus

## Architecture Decision: TypeScript Sync Script

**Decision**: Use TypeScript for the sync script (following kilm pattern)  
**Rationale**: 
- Runs in the same Node.js environment as Docusaurus
- Can be integrated into npm scripts and build process
- Works seamlessly with Docusaurus dev server
- Enables deployment to web hosting without Python dependency
- Proven pattern from kilm repository

**Alternatives considered**:
- Python sync script: Rejected - adds unnecessary runtime dependency for hosted docs
- Bash script: Rejected - poor cross-platform support
- GitHub Actions only: Rejected - doesn't support local development workflow

## Technology Stack Research

### Docusaurus 3.x Configuration

**Decision**: Latest Docusaurus 3.x with MDX support  
**Rationale**:
- Industry standard for modern documentation sites
- Built-in versioning, search, and i18n support
- MDX allows interactive components in docs
- Used by Meta, Pydantic, and many major projects

**Key Features Needed**:
- Custom sidebar configuration
- Multiple documentation sections (commands, services, guides)
- Search integration (Algolia or local)
- Dark mode support
- Mobile responsive design

### TypeScript Sync Implementation

**Decision**: TypeScript with chokidar for file watching (like kilm)  
**Rationale**:
- chokidar provides reliable cross-platform file watching
- TypeScript ensures type safety and better maintainability
- Can handle complex path mappings and transformations
- Integrates well with Node.js ecosystem

**Dependencies**:
```json
{
  "chokidar": "^4.0.0",    // File watching
  "gray-matter": "^4.0.3",  // Frontmatter parsing
  "glob": "^10.0.0",        // File pattern matching
  "tsx": "^4.0.0"           // TypeScript execution
}
```

### Documentation Structure Mapping

**Decision**: Embedded docs pattern with automatic discovery  
**Rationale**:
- Documentation lives next to code for maintainability
- Automatic discovery reduces configuration overhead
- Clear mapping rules prevent confusion

**Mapping Rules**:
```
Source → Destination
src/specify_cli/commands/*/docs.mdx → docs/docs/reference/cli/*.mdx
src/specify_cli/services/*/docs.mdx → docs/docs/reference/api/*.mdx
src/specify_cli/guides/*.mdx → docs/docs/guides/*.mdx
```

### Frontmatter Processing

**Decision**: Automatic frontmatter injection if missing  
**Rationale**:
- Ensures all docs have required metadata
- Extracts title from first heading if not provided
- Maintains consistency across all documentation

**Required Frontmatter**:
```yaml
---
title: Command/Service Name
description: Brief description
sidebar_label: Display name
---
```

### Development Workflow

**Decision**: Concurrent sync watching with Docusaurus dev server  
**Rationale**:
- Real-time documentation updates during development
- Similar to kilm's proven workflow
- Uses concurrently package for parallel execution

**NPM Scripts**:
```json
{
  "docs:sync": "tsx scripts/sync-docs.ts sync",
  "docs:watch": "tsx scripts/sync-docs.ts watch",
  "docs:clean": "tsx scripts/sync-docs.ts clean",
  "docs:dev": "concurrently \"npm run docs:watch\" \"docusaurus start\""
}
```

### Testing Strategy

**Decision**: Vitest for TypeScript sync script testing  
**Rationale**:
- Fast and modern test runner
- Native TypeScript support
- Compatible with Jest assertions
- Good watch mode for TDD

**Test Coverage**:
- File discovery and pattern matching
- Frontmatter processing
- Path mapping logic
- Error handling for malformed docs
- Cleanup of orphaned files

### Deployment Strategy

**Decision**: GitHub Pages with GitHub Actions  
**Rationale**:
- Free hosting for open source projects
- Automatic deployment on merge to main
- Custom domain support if needed
- Built-in CDN and SSL

**Alternative Platforms Supported**:
- Netlify (for preview deployments)
- Vercel (for serverless features)
- Self-hosted (Docker container)

## Best Practices from Research

### From Kilm Implementation
1. **Separate .command files** for CLI command naming flexibility
2. **Preserve file extensions** (.md vs .mdx) during sync
3. **Clean up orphaned docs** when source files are deleted
4. **Structured logging** for debugging sync issues

### From Docusaurus Community
1. **Use docusaurus.config.js** for all configuration
2. **Implement custom CSS** for branding
3. **Add edit URLs** for GitHub integration
4. **Configure redirects** for moved pages

### From TypeScript Best Practices
1. **Use strict mode** for type safety
2. **Implement error boundaries** for graceful failures
3. **Add JSDoc comments** for better IDE support
4. **Use path aliases** for cleaner imports

## Resolved Clarifications

All technical context items have been resolved:
- ✅ Language versions confirmed (Node.js 18+, TypeScript 5+)
- ✅ Dependencies selected (Docusaurus 3.x, chokidar, etc.)
- ✅ Testing framework chosen (Vitest)
- ✅ Performance goals achievable with incremental sync
- ✅ Memory constraints met with streaming operations

## Risk Mitigation

### Identified Risks and Mitigations

1. **Risk**: Large documentation sets causing slow sync
   - **Mitigation**: Incremental sync with file-level granularity
   
2. **Risk**: Malformed MDX breaking documentation build
   - **Mitigation**: Validation during sync with error reporting
   
3. **Risk**: Race conditions during concurrent file changes
   - **Mitigation**: Debouncing and queue-based processing

4. **Risk**: Version conflicts between Node.js environments
   - **Mitigation**: Use .nvmrc file and package-lock.json

## Next Steps (Phase 1)

With all research complete and decisions made:
1. Design the sync script contract (TypeScript interfaces)
2. Create data models for documentation metadata
3. Generate failing tests for sync functionality
4. Create quickstart guide for documentation workflow
5. Update CLAUDE.md with documentation system details
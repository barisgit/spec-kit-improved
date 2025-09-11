# Quickstart: Documentation-by-Code with Docusaurus

This guide validates the documentation-by-code implementation by walking through the complete setup and usage workflow.

## Prerequisites

- Node.js 18+ and pnpm installed
- SpecifyX project cloned locally
- Git repository initialized

## Step 1: Initialize Docusaurus Documentation Site

```bash
# From repository root
cd docs
pnpm create docusaurus@latest . classic --typescript
pnpm install
```

**Expected**: Docusaurus project created with TypeScript support

## Step 2: Install Sync Dependencies

```bash
pnpm add -D chokidar gray-matter glob tsx concurrently
pnpm add -D @types/node vitest
```

**Expected**: All dependencies installed without errors

## Step 3: Create Sync Script

Create `docs/scripts/sync-docs.ts`:

```bash
mkdir -p scripts
touch scripts/sync-docs.ts
```

**Expected**: Script file created at correct location

## Step 4: Configure Package Scripts

Add to `docs/package.json`:

```json
{
  "scripts": {
    "sync": "tsx scripts/sync-docs.ts sync",
    "sync:watch": "tsx scripts/sync-docs.ts watch",
    "sync:clean": "tsx scripts/sync-docs.ts clean",
    "dev": "concurrently \"pnpm sync:watch\" \"docusaurus start\" --names \"sync,docs\" --prefix-colors \"blue,green\"",
    "build": "pnpm sync && docusaurus build"
  }
}
```

**Expected**: Scripts added successfully

## Step 5: Create Sample Documentation

Create documentation alongside code:

```bash
# Create command documentation
echo "# init Command\n\nInitializes a new project." > src/specify_cli/commands/init/docs.mdx

# Create service documentation  
echo "# Template Service\n\nHandles template processing." > src/specify_cli/services/template_service/docs.mdx

# Create guide documentation
mkdir -p src/specify_cli/guides
echo "# Getting Started\n\nWelcome to SpecifyX!" > src/specify_cli/guides/getting-started.mdx
```

**Expected**: Three documentation files created

## Step 6: Run Initial Sync

```bash
cd docs
pnpm sync
```

**Expected Output**:
```
Syncing embedded documentation...
Synced init.mdx
Synced template_service.mdx
Synced getting-started.mdx
Synced 3 embedded docs
```

## Step 7: Verify Synced Files

```bash
ls -la src/content/docs/reference/cli/
ls -la src/content/docs/reference/api/
ls -la src/content/docs/guides/
```

**Expected**: Files exist in correct locations:
- `src/content/docs/reference/cli/init.mdx`
- `src/content/docs/reference/api/template_service.mdx`
- `src/content/docs/guides/getting-started.mdx`

## Step 8: Start Development Server

```bash
pnpm dev
```

**Expected**: 
- Sync watcher starts with blue prefix
- Docusaurus dev server starts with green prefix on http://localhost:3000
- Documentation site loads with synced content

## Step 9: Test Live Updates

1. Open `src/specify_cli/commands/init/docs.mdx`
2. Add a line: `## New Section`
3. Save the file

**Expected**:
- Console shows: `File changed: .../init/docs.mdx`
- Console shows: `init docs changed, syncing...`
- Browser auto-refreshes
- New section appears in documentation

## Step 10: Test File Addition

Create new command documentation:

```bash
echo "# check Command\n\nChecks system requirements." > src/specify_cli/commands/check/docs.mdx
```

**Expected**:
- Console shows: `File added: .../check/docs.mdx`
- Console shows: `Re-syncing all docs due to new file...`
- New page appears in documentation navigation

## Step 11: Test File Removal

Delete a documentation file:

```bash
rm src/specify_cli/commands/check/docs.mdx
```

**Expected**:
- Console shows: `File removed: .../check/docs.mdx`
- Console shows: `Re-syncing all docs due to file removal...`
- Orphaned file removed from docs site
- Page no longer accessible

## Step 12: Test Validation

Create invalid documentation:

```bash
echo "---\ntitle: Test\n---\n\nInvalid {{jinja}} syntax" > src/specify_cli/commands/test/docs.mdx
```

**Expected**:
- Sync completes (MDX with invalid Jinja is still valid MDX)
- If MDX parsing fails, error details in console
- Site continues to work with other valid pages

## Step 13: Run Tests

```bash
pnpm test
```

**Expected**: All sync script tests pass

## Step 14: Build Production Site

```bash
pnpm build
```

**Expected**:
- Sync runs automatically before build
- Documentation built successfully
- Static site in `build/` directory
- All pages render correctly

## Step 15: Clean Orphaned Files

```bash
pnpm sync:clean
```

**Expected**: Any files in docs without source files are removed

## Validation Checklist

- [ ] Docusaurus site initializes successfully
- [ ] Sync script discovers all documentation files
- [ ] Files sync to correct locations
- [ ] Frontmatter is added if missing
- [ ] Live watching updates files immediately
- [ ] New files are added automatically
- [ ] Deleted files are cleaned up
- [ ] Validation catches MDX errors
- [ ] Tests pass for sync functionality
- [ ] Production build completes
- [ ] Documentation is searchable
- [ ] Navigation structure is correct

## Troubleshooting

### Issue: Files not syncing
- Check glob patterns in sync script
- Verify file paths are correct
- Check console for error messages

### Issue: Frontmatter errors
- Ensure YAML syntax is valid
- Check for required fields (title, description)

### Issue: Build failures
- Validate all MDX files
- Check for broken links
- Ensure all imports exist

### Issue: pnpm workspace conflicts
- If in monorepo, add `docs/` to pnpm-workspace.yaml
- Or use separate pnpm lockfile with `--ignore-workspace`

## Success Criteria

The implementation is successful when:
1. All documentation lives next to code
2. Changes sync automatically during development
3. Documentation site builds without errors
4. All tests pass
5. Production deployment works
6. TypeScript sync script follows kilm pattern
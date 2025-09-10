# SpecifyX Documentation Assets

This directory contains static assets for the SpecifyX documentation website.

## Directory Structure

- `screenshots/` - Screenshots of the CLI in action, UI examples, etc.
- `gifs/` - Animated GIFs showing workflows and features
- `icons/` - Icons and logos for the project
- `diagrams/` - Architecture diagrams and flowcharts

## Asset Guidelines

### Screenshots
- Use consistent terminal themes (dark background preferred)
- Include window borders and context when helpful
- Save as WEBP format for best quality
- Use descriptive filenames (e.g., `init-command-output.png`)

### GIFs
- Keep file sizes reasonable (<5MB when possible)
- Use consistent frame rates (15-30 FPS)
- Show complete workflows from start to finish
- Include pauses to let viewers read output

### Naming Convention
- Use kebab-case for filenames
- Include version or date if content might change
- Examples:
  - `init-workflow-demo.gif`
  - `cli-help-output.webp`
  - `template-generation-2024.gif`

## Usage in Documentation

Reference assets using relative paths from the docs root:
```markdown
![CLI Screenshot](/img/screenshots/init-command-output.webp)
```

For React components:
```tsx
import screenshot from '@site/static/img/screenshots/init-command-output.webp';
```
---
title: Introduction
description: Welcome to SpecifyX Documentation
---

# Welcome to SpecifyX Documentation

SpecifyX is an enhanced Python CLI tool for specification-driven development that helps developers create specifications, implementation plans, and manage project workflows with AI assistant integration.

<img src="/img/logo.svg" alt="SpecifyX Logo" width="120" style={{display: 'block', margin: '2rem auto'}} />


## Getting Started

Choose your path to get started with SpecifyX:

### Quick Start (5 minutes)
- **[Quick Start Guide](./guides/quickstart)** - Get up and running in minutes with AI assistant commands

### Comprehensive Guides
- **[Installation Guide](./guides/installation)** - Detailed setup instructions for all platforms
- **[Development Workflow](./guides/workflow)** - Complete specification-driven development process

### Reference Documentation
- **[CLI Reference](./reference/cli/init)** - Command-line interface documentation
- **[API Reference](./reference/api/template_service)** - Service and API documentation

## What is Specification-Driven Development?

Specification-Driven Development **flips the script** on traditional software development. Instead of code being king, **specifications become executable**, directly generating working implementations through AI assistants.

### The 3-Phase Process

1. **Specify** - Define what to build using `/specify` commands
2. **Plan** - Design how to build it using `/plan` commands  
3. **Tasks** - Break down into actionable tasks using `/tasks` commands

## Key Features

- **AI-Native Workflow**: Seamless integration with Claude, Gemini, and Copilot
- **Specification-First**: Define requirements before implementation
- **Template System**: Powerful Jinja2-based templating with AI-aware content
- **Project Management**: Initialize projects with structured workflows
- **Auto-Synced Documentation**: Keep documentation alongside code

## Quick Installation

```bash
# Using uv (recommended)
uv tool install specifyx

# Using pipx
pipx install specifyx

# Using pip
pip install specifyx
```

## Quick Usage

```bash
# Initialize a new project
specifyx init my-awesome-project

# Check system requirements
specifyx check

# Use AI assistant commands
/specify Build a user authentication system
/plan Use Python with FastAPI and SQLite
/tasks Break down into actionable development tasks
```

## Next Steps

Ready to get started? Begin with the [Quick Start Guide](/docs/guides/quickstart) to see SpecifyX in action, or dive deeper with the [Development Workflow](/docs/guides/workflow) for comprehensive guidance.
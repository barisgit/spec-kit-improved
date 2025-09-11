# SpecifyX

**Enhanced spec-driven development CLI with modern architecture and Jinja2 templating**

[![Release](https://github.com/barisgit/spec-kit-improved/actions/workflows/release.yml/badge.svg)](https://github.com/barisgit/spec-kit-improved/actions/workflows/release.yml)
[![PyPI version](https://badge.fury.io/py/specifyx.svg)](https://badge.fury.io/py/specifyx)

<div align="center">
  <p><strong><a href="https://specifyx.dev">📚 Documentation</a> • <a href="https://specifyx.dev/docs/guides/quickstart">🚀 Quick Start</a> • <a href="https://github.com/barisgit/spec-kit-improved/issues">💬 Support</a></strong></p>
</div>

---

## What is SpecifyX?

![SpecifyX Demo](docs/static/img/gifs/specifyx-init.gif)

SpecifyX is a modern Python CLI tool for spec-driven development that helps teams focus on product scenarios rather than writing boilerplate code. Enhanced fork of GitHub's [spec-kit](https://github.com/github/spec-kit).

### Key Features

- **Easy Installation**: `uv tool install specifyx` or `uvx specifyx` 
- **Jinja2 Templating**: Variables, conditionals, loops for complex project generation
- **Flexible Branch Naming**: Custom patterns like `feature/{name}` or `task/{id}-{name}`
- **Configuration System**: TOML-based preferences and settings
- **Interactive UI**: Menus, progress tracking, colored output

<br clear="right">

## Installation

### Using uv (recommended )
```bash
uv tool install specifyx
```

### Alternative without installation
```bash
uvx specifyx
```

### Using pipx or pip
```bash
pipx install specifyx  # or: pip install specifyx
```

<br clear="left">

## Quick Start

See SpecifyX in action - initialize a new project and start building:

```bash
# Create a new project
specifyx init my-project
cd my-project

# Check system requirements  
specifyx check

# Run project scripts
specifyx run --list
```

<div align="center">
  <p><strong>🎯 <a href="https://specifyx.dev">Visit specifyx.dev for comprehensive guides and examples</a></strong></p>
</div>

## What is Spec-Driven Development?

Spec-Driven Development makes **specifications executable** - directly generating working implementations rather than just guiding them.

### Core Philosophy
- **Intent-driven** development where specs define "_what_" before "_how_"
- **Multi-step refinement** rather than one-shot code generation
- **AI-enhanced** specification interpretation and implementation

<br clear="right">

## Prerequisites

- **Linux/macOS** (or WSL2 on Windows)
- **Python 3.11+**
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [uv](https://docs.astral.sh/uv/) for package management

## Development

```bash
git clone https://github.com/barisgit/spec-kit-improved
cd spec-kit-improved
uv sync --extra dev

# Run tests
pytest

# Code quality
ruff check . && ruff format . && pyrefly check .
```

<br clear="left">

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines. We welcome contributions!

## License

MIT License - see [LICENSE](./LICENSE) file.

---

<div align="center">
  <p><strong>SpecifyX</strong>: Making spec-driven development accessible and powerful for modern teams.</p>
  <p>🌟 <a href="https://specifyx.dev">Explore the full documentation at specifyx.dev</a> 🌟</p>
</div>
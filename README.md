# SpecifyX

**Enhanced spec-driven development CLI with modern architecture and Jinja2 templating**

[![Release](https://github.com/barisgit/spec-kit-improved/actions/workflows/release.yml/badge.svg)](https://github.com/barisgit/spec-kit-improved/actions/workflows/release.yml)
[![PyPI version](https://badge.fury.io/py/specifyx.svg)](https://badge.fury.io/py/specifyx)

---

## What is SpecifyX?

SpecifyX is a modern, Python-installable CLI tool forked from the popular [spec-kit](https://github.com/github/spec-kit) for spec-driven development that helps organizations focus on product scenarios rather than writing undifferentiated code.

### Key Benefits for Users

- **Easy Installation**: Install with `uv tool install specifyx` or run `uvx specifyx` without installation
- **Powerful Templating**: Use Jinja2 templates with variables, conditionals, and loops for complex project generation
- **Flexible Branch Naming**: Customize branch patterns like `feature/{name}` or `task/{id}-{name}` and more instead of fixed formats
- **Enhanced User Experience**: Interactive menus, progress tracking, and better error messages
- **Project Generation**: Generate projects from templates with variables, conditionals, and loops for complex project generation
- **Configurable Python Scripts**: Uses python for scripts with utils imported from specifyx to achieve user customizable scripts with low boilerplate
- **Configuration System**: Save your preferences in TOML files instead of repeating command-line options

## Installation

### Using uv (recommended)
```bash
uv tool install specifyx
```

#### Alternative if you don't want to install

```bash
uvx specifyx
```

> Note: `uvx` is a shortcut for `uv tool run`

### Using pipx (for CLI tools)
```bash
pipx install specifyx
```

### Using pip
```bash
pip install specifyx
```

### From git (development version)
```bash
uv tool install --from git+https://github.com/barisgit/spec-kit-improved
```

## Quick Start

Initialize a new spec-driven project:
```bash
specifyx init my-project
specifyx init --here  # in current directory
```

Check tool requirements:
```bash
specifyx check
```

Run specifyx python scripts in your project with:
```bash
specifyx run my-script

# List available scripts
specifyx run --list

# Show path to specified script
specifyx run --which my-script
```

> Note: Your AI assistant is instructed to use specifyx when you run commands.

## Attribution and Philosophy

### Inspiration and Attribution

This project is **inspired by and builds upon** the foundational work of the original [specify](https://github.com/github/spec-kit) project by the GitHub team, particularly [John Lam](https://github.com/jflam) and [Den Delimarsky](https://github.com/dend). Their pioneering work in spec-driven development methodology laid the groundwork for this enhanced implementation.

### Why a Separate Project?

While deeply respecting the original specify project, SpecifyX takes a different philosophical approach in several key areas:

#### **1. Installation and Distribution**
- **Original specify**: Git-based templates requiring manual setup
- **SpecifyX**: Standard Python package installable via PyPI for easier adoption

#### **2. Templating Capabilities** 
- **Original specify**: Basic string replacement templating
- **SpecifyX**: Full Jinja2 templating with variables, loops, conditionals, and complex logic

#### **3. Configuration and Customization**
- **Original specify**: Minimal configuration, mostly environment-based
- **SpecifyX**: Rich TOML-based configuration system with user preferences and project-specific settings

#### **4. Branch Naming Flexibility**
- **Original specify**: Fixed pattern like "001-feature-name"
- **SpecifyX**: Customizable patterns to match your team's conventions AND branch validation logic so your AI assistant can't generate invalid branch names

#### **5. User Experience Focus**
- **Original specify**: Bash scripts with basic output
- **SpecifyX**: Customizable scripts with utils imported from specifyx to achieve user customizable scripts with low boilerplate

### Our Vision

SpecifyX aims to make spec-driven development more **accessible and powerful** for teams who want enhanced tooling while maintaining full respect for the original methodology. We believe both approaches serve different needs in the ecosystem.

## What is Spec-Driven Development?

Spec-Driven Development **flips the script** on traditional software development. Instead of code being king, **specifications become executable**, directly generating working implementations rather than just guiding them.

### Core Philosophy

- **Intent-driven development** where specifications define the "_what_" before the "_how_"
- **Rich specification creation** using guardrails and organizational principles  
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation

## Development Phases

| Phase | Focus | Key Activities |
|-------|-------|----------------|
| **0-to-1 Development** | Generate from scratch | Generate specs → Plan implementation → Build production-ready applications |
| **Creative Exploration** | Parallel implementations | Explore diverse solutions → Support multiple tech stacks → Experiment with UX patterns |
| **Iterative Enhancement** | Brownfield modernization | Add features iteratively → Modernize legacy systems → Adapt processes |

## Prerequisites

- **Linux/macOS** (or WSL2 on Windows)
- **Python 3.11+** 
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [uv](https://docs.astral.sh/uv/) for package management (recommended)
- [Git](https://git-scm.com/downloads)

## Enhanced Features

### Jinja2 Templating

In your generated project, you can see spec, plan and tasks templates in `.specify/templates/` directory. You can customize them to your needs. They will be rendered with your project variables.

### Enhanced User Interface
- Interactive menus with keyboard navigation
- Progress tracking with live updates  
- Rich console output with colored themes
- Graceful fallbacks for limited terminals

## Technical Details

For developers interested in the architecture:

- **Modern Architecture**: Modular services instead of monolithic code
- **Type Safety**: Full type annotations and validation throughout
- **Comprehensive Testing**: Contract, integration, and unit tests
- **TOML Configuration**: Flexible configuration with dynaconf

## Documentation

To be updated.

## Development

### Setup Development Environment
```bash
git clone https://github.com/barisgit/spec-kit-improved
cd spec-kit-improved
uv sync --extra dev
```

### Run Tests
```bash
pytest                    # All tests
pytest tests/contract/    # Contract tests
pytest tests/integration/ # Integration tests
pytest tests/unit/        # Unit tests
```

### Code Quality
```bash
ruff check .              # Linting
ruff format .             # Formatting  
pyrefly check .           # Type checking
```

#### There is also a Makefile in the root of the project for convenience.

You can run `make help` to see the available commands.

## Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for more details.

## Support

For support, please open a [GitHub issue](https://github.com/barisgit/spec-kit-improved/issues/new). We welcome bug reports, feature requests, and questions about using SpecifyX.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

**SpecifyX**: Making spec-driven development more accessible and powerful for modern development teams.
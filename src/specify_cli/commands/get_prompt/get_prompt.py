"""Get prompt command for generating AI assistant system prompts."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from specify_cli.services.prompt_service import PromptService

console = Console()


def get_prompt_command(
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save prompt to file"
    ),
) -> None:
    """Generate global system prompt for AI assistant to integrate SpecifyX workflow.

    This command generates a universal system prompt that any AI assistant can use to
    understand and integrate SpecifyX spec-driven development workflow across all projects.

    The prompt includes:
    - SpecifyX project detection logic
    - Global workflow integration rules
    - Universal guidance for all AI assistants

    Use this prompt globally in your AI assistant configuration to enable
    SpecifyX workflow understanding across all your development work.
    """
    prompt_service = PromptService()

    try:
        # Generate the global system prompt
        console.print("[cyan]Generating universal SpecifyX system prompt...[/cyan]")

        system_prompt = prompt_service.generate_global_system_prompt()

        # Display header
        console.print(
            Panel.fit(
                "[bold cyan]SpecifyX Universal System Prompt Generated[/bold cyan]\n"
                "Compatibility: [yellow]All AI Assistants[/yellow]\n"
                "Scope: [blue]Global (all projects)[/blue]\n"
                "Detection: [green]Automatic SpecifyX project detection[/green]",
                border_style="cyan",
            )
        )

        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(system_prompt, encoding="utf-8")

            console.print(f"\n[green]System prompt saved to [cyan]{output_path}[/cyan]")
            console.print(f"File size: {len(system_prompt):,} characters")
        else:
            # Display in terminal with syntax highlighting and proper wrapping
            console.print("\n[bold]Generated System Prompt:[/bold]\n")
            syntax = Syntax(
                system_prompt,
                "markdown",
                theme="monokai",
                line_numbers=False,
                word_wrap=True,
            )
            console.print(syntax)

        # Show usage instructions
        console.print(
            "\n[bold]Universal Usage:[/bold]\n"
            "• Add this prompt to any AI assistant's global configuration\n"
            "• Examples: ~/.claude/CLAUDE.md, Cursor settings, etc.\n"
            + (
                f"• Edit {output_file} to customize for your workflow\n"
                if output_file
                else ""
            )
            + "• AI will auto-detect SpecifyX projects and adapt behavior\n"
            + "• Works across all projects - no per-project setup needed"
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to generate system prompt: {e}")
        raise typer.Exit(1) from e

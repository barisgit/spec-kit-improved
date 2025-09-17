"""System and utility commands."""

import shutil

import httpx

from specify_cli.assistants import InjectionPoint


def check_tool(console, tool: str, install_hint: str) -> bool:
    """Check if a tool is installed."""
    if shutil.which(tool):
        console.print(f"[green]✓[/green] {tool} found")
        return True
    else:
        console.print(f"[yellow]⚠️  {tool} not found[/yellow]")
        console.print(f"   Install with: [cyan]{install_hint}[/cyan]")
        return False


def check_command():
    """Check that all required tools are installed."""
    from specify_cli.assistants import get_all_assistants
    from specify_cli.core.app import console, show_banner

    show_banner()
    console.print("[bold]Checking Specify requirements...[/bold]\n")

    # Check internet connectivity
    console.print("[cyan]Checking internet connectivity...[/cyan]")
    try:
        httpx.get("https://api.github.com", timeout=5, follow_redirects=True)
        console.print("[green]✓[/green] Internet connection available")
    except httpx.RequestError:
        console.print(
            "[red]✗[/red] No internet connection - required for downloading templates"
        )
        console.print("[yellow]Please check your internet connection[/yellow]")

    console.print("\n[cyan]Optional tools:[/cyan]")
    git_ok = check_tool(console, "git", "https://git-scm.com/downloads")

    console.print("\n[cyan]Optional AI tools:[/cyan]")

    # Dynamically check all registered assistants
    assistants = get_all_assistants()
    ai_tools_available = []

    for assistant in assistants:
        validation_result = assistant.validate_setup()
        tool_name = assistant.config.name

        if validation_result.is_valid:
            console.print(f"[green]✓[/green] {tool_name} found")
            ai_tools_available.append(tool_name)
        else:
            console.print(f"[yellow]⚠️  {tool_name} not found[/yellow]")
            # Use assistant's injection values for setup instructions
            injection_values = assistant.get_injection_values()
            setup_instructions = injection_values.get(
                InjectionPoint.SETUP_INSTRUCTIONS, f"Install {tool_name}"
            )
            documentation_url = injection_values.get(
                InjectionPoint.DOCUMENTATION_URL, ""
            )

            if documentation_url:
                console.print(f"   Install from: [cyan]{documentation_url}[/cyan]")
            else:
                console.print(f"   {setup_instructions}")

    console.print("\n[green]✓ SpecifyX CLI is ready to use![/green]")
    if not git_ok:
        console.print(
            "[yellow]Consider installing git for repository management[/yellow]"
        )
    if not ai_tools_available:
        console.print(
            "[yellow]Consider installing an AI assistant for the best experience[/yellow]"
        )

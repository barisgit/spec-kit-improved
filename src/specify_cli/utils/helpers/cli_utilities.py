"""
CLI Utilities - focused on CLI decorators and output utilities.

This helper handles:
- CLI output formatting (echo functions)
- JSON mode support
- Error handling decorators
- Typer integration utilities
"""

import json
import sys
from typing import Any, Callable, Dict, Optional

import typer
from rich.console import Console

# Create console instance for output
console = Console()


class CliUtilities:
    """Helper for CLI operations and output formatting."""

    @staticmethod
    def echo_info(message: str, quiet: bool = False, json_mode: bool = False) -> None:
        """Echo informational message."""
        if quiet:
            return

        if json_mode:
            CliUtilities._output_json({"level": "info", "message": message})
        else:
            console.print(f"   {message}", style="blue")

    @staticmethod
    def echo_debug(message: str, debug: bool = False) -> None:
        """Echo debug message if debug mode is enabled."""
        if debug:
            console.print(f"{message}", style="dim")

    @staticmethod
    def echo_error(message: str, json_mode: bool = False, quiet: bool = False) -> None:
        """Echo error message."""
        if json_mode:
            CliUtilities._output_json({"level": "error", "message": message})
        elif not quiet:
            console.print(f"  {message}", style="red")

        # Always output to stderr for errors
        if not json_mode and not quiet:
            print(f"Error: {message}", file=sys.stderr)

    @staticmethod
    def echo_success(
        message: str, quiet: bool = False, json_mode: bool = False
    ) -> None:
        """Echo success message."""
        if quiet:
            return

        if json_mode:
            CliUtilities._output_json({"level": "success", "message": message})
        else:
            console.print(f"  {message}", style="green")

    @staticmethod
    def echo_warning(
        message: str, quiet: bool = False, json_mode: bool = False
    ) -> None:
        """Echo warning message."""
        if quiet:
            return

        if json_mode:
            CliUtilities._output_json({"level": "warning", "message": message})
        else:
            console.print(f"   {message}", style="yellow")

    @staticmethod
    def output_result(
        result: Dict[str, Any],
        success_message: Optional[str] = None,
        error_message: Optional[str] = None,
        json_mode: bool = False,
        quiet: bool = False,
    ) -> None:
        """
        Output result in appropriate format.

        Args:
            result: Result dictionary
            success_message: Message to show on success
            error_message: Message to show on error
            json_mode: Whether to output in JSON format
            quiet: Whether to suppress output
        """
        if json_mode:
            CliUtilities._output_json(result)
            return

        if quiet:
            return

        # Determine if result indicates success
        is_success = result.get("success", True)

        if is_success and success_message:
            CliUtilities.echo_success(success_message)
        elif not is_success and error_message:
            CliUtilities.echo_error(error_message)

        # Output additional result details if present
        if "details" in result and not quiet:
            console.print(result["details"])

    @staticmethod
    def handle_typer_exceptions(func: Callable) -> Callable:
        """
        Decorator to handle common Typer exceptions gracefully.

        Args:
            func: Function to wrap

        Returns:
            Callable: Wrapped function
        """

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except typer.Exit as e:
                sys.exit(e.exit_code)
            except KeyboardInterrupt:
                CliUtilities.echo_error("Operation cancelled by user")
                sys.exit(130)  # Standard exit code for SIGINT
            except Exception as e:
                CliUtilities.echo_error(f"Unexpected error: {str(e)}")
                sys.exit(1)

        return wrapper

    @staticmethod
    def confirm_action(
        message: str, default: bool = False, auto_confirm: bool = False
    ) -> bool:
        """
        Confirm an action with the user.

        Args:
            message: Confirmation message
            default: Default response if user just presses Enter
            auto_confirm: If True, automatically confirm without prompting

        Returns:
            bool: True if confirmed
        """
        if auto_confirm:
            return True

        return typer.confirm(message, default=default)

    @staticmethod
    def prompt_for_input(
        message: str,
        default: Optional[str] = None,
        hide_input: bool = False,
        validate_func: Optional[Callable[[str], bool]] = None,
    ) -> str:
        """
        Prompt user for input with validation.

        Args:
            message: Prompt message
            default: Default value
            hide_input: Whether to hide input (for passwords)
            validate_func: Optional validation function

        Returns:
            str: User input
        """
        while True:
            try:
                value = typer.prompt(message, default=default, hide_input=hide_input)

                if validate_func and not validate_func(value):
                    CliUtilities.echo_error("Invalid input. Please try again.")
                    continue

                return value

            except typer.Abort:
                CliUtilities.echo_error("Operation cancelled by user")
                sys.exit(130)

    @staticmethod
    def create_progress_callback(description: str = "Processing"):
        """
        Create a progress callback for long-running operations.

        Args:
            description: Description of the operation

        Returns:
            Progress callback function
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )

        task = progress.add_task(description, total=None)

        def update_progress(message: str):
            progress.update(task, description=f"{description}: {message}")

        return progress, update_progress

    @staticmethod
    def format_table(
        data: list[Dict[str, Any]],
        columns: Optional[list[str]] = None,
        title: Optional[str] = None,
    ) -> None:
        """
        Format and display data as a table.

        Args:
            data: List of dictionaries to display
            columns: Optional list of columns to include
            title: Optional table title
        """
        if not data:
            CliUtilities.echo_info("No data to display")
            return

        from rich.table import Table

        table = Table(title=title)

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Add columns
        for column in columns:
            table.add_column(column.replace("_", " ").title())

        # Add rows
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])

        console.print(table)

    @staticmethod
    def format_key_value_pairs(
        data: Dict[str, Any], title: Optional[str] = None
    ) -> None:
        """
        Format and display key-value pairs.

        Args:
            data: Dictionary to display
            title: Optional title
        """
        if title:
            console.print(f"\n[bold]{title}[/bold]")

        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()
            console.print(f"{formatted_key}: {value}")

    @staticmethod
    def _output_json(data: Dict[str, Any]) -> None:
        """Output data as JSON."""
        print(json.dumps(data, indent=2))


# Convenience functions that match the original script_helpers interface
def echo_info(message: str, quiet: bool = False, json_mode: bool = False) -> None:
    """Echo informational message."""
    CliUtilities.echo_info(message, quiet, json_mode)


def echo_debug(message: str, debug: bool = False) -> None:
    """Echo debug message if debug mode is enabled."""
    CliUtilities.echo_debug(message, debug)


def echo_error(message: str, json_mode: bool = False, quiet: bool = False) -> None:
    """Echo error message."""
    CliUtilities.echo_error(message, json_mode, quiet)


def echo_success(message: str, quiet: bool = False, json_mode: bool = False) -> None:
    """Echo success message."""
    CliUtilities.echo_success(message, quiet, json_mode)

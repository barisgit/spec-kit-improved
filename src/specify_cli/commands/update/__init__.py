"""Update command module."""

import typer

from .check import check_update_command
from .info import info_command
from .update import update_command

# Create update command group
update_app = typer.Typer(
    name="update", help="Update SpecifyX CLI", no_args_is_help=True
)
update_app.command("check")(check_update_command)
update_app.command("info")(info_command)
update_app.command("perform")(update_command)

__all__ = ["update_command", "check_update_command", "info_command", "update_app"]

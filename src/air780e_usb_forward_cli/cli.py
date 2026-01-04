"""Command line interface for AIR780E USB forwarding."""

from __future__ import annotations

import typer

from . import __app_name__, __version__
from .commands.init_cmd import init_command
from .commands.console_cmd import console_command

app = typer.Typer(help="Configure AIR780E USB forwarding per project.")


@app.callback(invoke_without_command=True)
def main(  # pragma: no cover - thin glue to expose version/help only
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the CLI version and exit.",
        is_eager=True,
    ),
) -> None:
    if version:
        typer.echo(f"{__app_name__} {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


app.command(name="init")(init_command)
app.command(name="console")(console_command)


if __name__ == "__main__":
    app()

"""`init` subcommand: create per-project config for AIR780E USB forwarding."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ..config import ProjectConfig, ValidationError, default_config_path


def _normalize_config_path(config_path: Path | None) -> Path:
    """Resolve the config path relative to the current working directory."""
    if config_path is None:
        return default_config_path()

    expanded = config_path.expanduser()
    return expanded if expanded.is_absolute() else Path.cwd() / expanded


def _prompt_for_serial(default: str | None = None) -> str:
    return typer.prompt("Serial device path", default=default or "").strip()


def init_command(
    serial_port: Optional[str] = typer.Argument(
        None,
        metavar="SERIAL_PORT",
        help="Serial device path, e.g. /dev/serial/by-id/<device>.",
    ),
    serial_option: Optional[str] = typer.Option(
        None,
        "--serial",
        "-s",
        help="Serial device path (alternative to positional argument).",
    ),
    config_path: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to store the project config file (default: .air780e.json).",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Prompt for missing values interactively.",
    ),
) -> None:
    """Initialize project config pointing at a single serial port."""
    target_path = _normalize_config_path(config_path)
    existing_serial = None
    try:
        if target_path.exists():
            existing_serial = ProjectConfig.load(target_path).serial_port
    except Exception:
        existing_serial = None

    option_mode = serial_port is not None or serial_option is not None
    chosen_serial = serial_port or serial_option

    if not option_mode or interactive:
        chosen_serial = _prompt_for_serial(default=chosen_serial or existing_serial)

    if not chosen_serial:
        if existing_serial:
            chosen_serial = existing_serial
        else:
            typer.echo("Serial device path is required.")
            raise typer.Exit(code=1)

    try:
        ProjectConfig(serial_port=chosen_serial).save(target_path)
    except ValidationError as exc:  # surface validation errors cleanly
        typer.echo(f"Invalid config: {exc}")
        raise typer.Exit(code=1)

    typer.echo(f"Saved project config to {target_path} for serial port {chosen_serial}.")

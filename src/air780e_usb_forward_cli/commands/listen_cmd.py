"""`listen` subcommand: continuously print serial input."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import serial
import typer

from ..config import ProjectConfig, ValidationError, default_config_path


def _resolve_serial_port(serial_port: Optional[str], config_path: Path | None) -> str:
    target_path = (
        config_path.expanduser() if config_path else default_config_path()
    ).resolve()
    if serial_port:
        return serial_port

    if not target_path.exists():
        typer.echo(
            f"No serial port provided and config missing at {target_path}. "
            "Run 'air780e init' first or pass --serial."
        )
        raise typer.Exit(code=1)

    try:
        return ProjectConfig.load(target_path).serial_port
    except (OSError, ValidationError, ValueError) as exc:
        typer.echo(f"Failed to read config at {target_path}: {exc}")
        raise typer.Exit(code=1)


def listen_command(
    serial_port: Optional[str] = typer.Option(
        None,
        "--serial",
        "-s",
        help="Serial device path (overrides config).",
    ),
    config_path: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Config file path (default: .air780e.json).",
    ),
) -> None:
    """Keep reading from the serial port and echo to stdout."""
    target_serial = _resolve_serial_port(serial_port, config_path)

    try:
        with serial.Serial(target_serial, baudrate=115200, timeout=1) as ser:
            ser.reset_input_buffer()
            typer.echo(f"Listening on {target_serial}. Press Ctrl+C to stop.")
            while True:
                try:
                    data = ser.readline()
                except serial.SerialException as exc:
                    typer.echo(f"Serial error while reading: {exc}")
                    raise typer.Exit(code=1)

                if not data:
                    continue

                typer.echo(data.decode(errors="replace").rstrip("\r\n"))
    except KeyboardInterrupt:
        typer.echo("\nStopped listening.")
    except serial.SerialException as exc:
        typer.echo(f"Serial error: {exc}")
        raise typer.Exit(code=1)

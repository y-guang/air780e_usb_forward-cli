"""`console` subcommand: send a message to the configured serial device and show its reply."""

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


def _send_and_receive(ser: serial.Serial, message: str, read_timeout: float) -> str:
    outbound = (message + "\r").encode()
    orig_timeout = ser.timeout
    ser.timeout = read_timeout
    ser.reset_input_buffer()
    ser.write(outbound)
    ser.flush()

    ser.read_until(b"\r\n")  # consume leading CRLF prefix
    response = ser.read_until(b"\r\n")
    ser.timeout = orig_timeout

    if not response:
        return ""

    return response.strip(b"\r\n").decode(errors="replace")


def console_command(
    message: Optional[str] = typer.Argument(
        None,
        metavar="MESSAGE",
        help="Message to send; if omitted, enters interactive prompt.",
    ),
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
    baudrate: int = typer.Option(115200, help="Serial baud rate."),
    timeout: float = typer.Option(9.0, help="Read timeout in seconds."),
) -> None:
    """Send a message to the device and print its response."""
    target_serial = _resolve_serial_port(serial_port, config_path)

    try:
        with serial.Serial(target_serial, baudrate=baudrate, timeout=timeout, write_timeout=timeout) as ser:
            if message is not None:
                reply = _send_and_receive(ser, message, timeout)
                typer.echo(reply if reply else "(no response)")
                return

            # Interactive prompt mode: blank line to exit.
            typer.echo(f"Connected to {target_serial}. Press Enter on empty line to exit.")
            while True:
                msg = typer.prompt("msg", default="")
                if not msg.strip():
                    typer.echo("Bye.")
                    break
                reply = _send_and_receive(ser, msg, timeout)
                typer.echo(reply if reply else "(no response)")
    except serial.SerialException as exc:
        typer.echo(f"Serial error: {exc}")
        raise typer.Exit(code=1)
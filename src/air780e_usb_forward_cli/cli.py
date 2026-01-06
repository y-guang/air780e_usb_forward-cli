"""Typer CLI for AIR780E.

Commands:
- listen: continually seek a port, send initial AT setup, then log messages to JSONL.
- send: send a single SMS via AT+CMGS.
"""
from __future__ import annotations

import time
import typer

from .init_commands import send_initial_commands
from .listener import listen as listen_sms
from .ports import list_at_devices
from .sms_sender import send_sms


app = typer.Typer(add_completion=False)


def _choose_port(explicit_port: str | None) -> str:
    if explicit_port:
        return explicit_port

    ports = list_at_devices()
    if not ports:
        raise RuntimeError("No AT device found; specify --port to override.")
    if len(ports) > 1:
        raise RuntimeError("Multiple AT devices found; please specify --port.")
    return ports[0]


def _find_port(poll_interval_s: float = 60.0) -> str:
    while True:
        ports = list_at_devices()
        if ports:
            if len(ports) == 1:
                return ports[0]
            raise RuntimeError("Multiple AT devices found; please specify --port.")
        typer.echo("No AT device found; retrying in 60s...")
        time.sleep(poll_interval_s)


@app.command(name="listen")
def listen(
    logfile: str = typer.Option("messages.jsonl", "--logfile", "-o", help="Path to JSONL log file"),
    poll_interval: float = typer.Option(60.0, help="Seconds between port scans when none found"),
    port: str | None = typer.Option(None, "--port", help="Explicit port path"),
) -> None:
    """Continuously find a port, init it, and start the listener."""
    while True:
        try:
            chosen = _choose_port(port)
        except RuntimeError as exc:
            typer.echo(str(exc))
            time.sleep(poll_interval)
            continue
        typer.echo(f"Using port {chosen}")

        try:
            send_initial_commands(chosen)
        except Exception as exc:
            typer.echo(f"init commands failed ({exc}); retrying after delay")
            time.sleep(1.0)
            continue

        time.sleep(1.0)

        try:
            listen_sms(chosen, logfile, intra_timeout_ms=100)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            typer.echo(f"listener error ({exc}); restarting scan")
            time.sleep(1.0)
            continue


@app.command()
def send(
    phone: str = typer.Option(..., "--phone", "-p", help="Destination phone number"),
    message: str = typer.Option(..., "--message", "-m", help="Message text"),
    port: str | None = typer.Option(None, "--port", help="Explicit port path"),
) -> None:
    """Send one SMS then exit."""
    try:
        chosen = _choose_port(port)
    except RuntimeError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    typer.echo(f"Sending SMS via {chosen} ...")
    try:
        send_sms(chosen, phone=phone, message=message)
        typer.echo("Send invoked.")
    except Exception as exc:
        typer.echo(f"send encountered an error (continuing): {exc}")


if __name__ == "__main__":
    app()

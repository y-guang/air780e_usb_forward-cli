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


def _find_port(poll_interval_s: float = 60.0) -> str:
    while True:
        ports = list_at_devices()
        if ports:
            return ports[0]
        typer.echo("No AT device found; retrying in 60s...")
        time.sleep(poll_interval_s)


@app.command(name="listen")
def listen(
    logfile: str = typer.Option("messages.jsonl", "--logfile", "-o", help="Path to JSONL log file"),
    poll_interval: float = typer.Option(60.0, help="Seconds between port scans when none found"),
) -> None:
    """Continuously find a port, init it, and start the listener."""
    while True:
        port = _find_port(poll_interval_s=poll_interval)
        typer.echo(f"Using port {port}")

        try:
            send_initial_commands(port)
        except Exception as exc:
            typer.echo(f"init commands failed ({exc}); retrying after delay")
            time.sleep(1.0)
            continue

        time.sleep(1.0)

        try:
            listen_sms(port, logfile, intra_timeout_ms=100)
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
) -> None:
    """Send one SMS then exit."""
    ports = list_at_devices()
    if not ports:
        typer.echo("No AT device found; cannot send SMS.")
        raise typer.Exit(code=1)

    port = ports[0]
    typer.echo(f"Sending SMS via {port} ...")
    try:
        send_sms(port, phone=phone, message=message)
        typer.echo("Send invoked.")
    except Exception as exc:
        typer.echo(f"send encountered an error (continuing): {exc}")


if __name__ == "__main__":
    app()

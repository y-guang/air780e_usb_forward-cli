"""Typer CLI for AIR780E.

Commands:
- listen: continually seek a port, send initial AT setup, then log messages to JSONL.
- send: send a single SMS via AT+CMGS.
- recent: show the most recent matching messages.
"""
from __future__ import annotations

import time
import typer
from pathlib import Path

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


@app.command(name="listen")
def listen(
    logfile: str = typer.Option("messages.jsonl", "--logfile", "-o", help="Path to JSONL log file"),
    poll_interval: float = typer.Option(10.0, help="Seconds between port scans when none found"),
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
            time.sleep(poll_interval)
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


@app.command(name="recent")
def recent(
    logfile: str = typer.Option("messages.jsonl", "--logfile", "-f", help="Path to JSONL log file"),
    count: int = typer.Option(5, "--count", "-n", help="Maximum messages to display"),
    pattern: str = typer.Option(r"\+CMT:", "--pattern", "-p", help="Regex applied to message_parsed"),
) -> None:
    """Print the most recent messages matching the regex pattern (default +CMT:)."""
    import json
    import re
    
    path = Path(logfile)
    if not path.exists():
        typer.echo(f"{logfile} not found")
        raise typer.Exit(code=1)

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        typer.echo(f"failed to read {logfile}: {exc}")
        raise typer.Exit(code=1)

    regex = re.compile(pattern)
    results: list[str] = []

    for line in reversed(lines):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg = obj.get("message_parsed")
        if not msg or not regex.search(msg):
            continue

        results.append(msg)
        if len(results) >= count:
            break

    if not results:
        typer.echo("No matching messages.")
        return

    typer.echo("\n---\n".join(results))


@app.command(name="gen-server")
def gen_server(
    output: str = typer.Option("-", "--output", "-o", help="Path to write unit file, '-' for stdout"),
) -> None:
    """Generate a systemd unit for the listener."""
    import getpass
    import sys

    user = getpass.getuser()
    workdir = str(Path.cwd())
    python_exe = sys.executable
    exec_cmd = f"{python_exe} -m air780e_sms_cli.cli listen"

    unit = f"""[Unit]
Description=air780e_sms_listener
After=network.target

[Service]
User={user}
WorkingDirectory={workdir}
ExecStart={exec_cmd}
Restart=always

[Install]
WantedBy=multi-user.target
"""

    if output == "-":
        typer.echo(unit)
    else:
        path = Path(output)
        path.write_text(unit, encoding="utf-8")
        typer.echo(f"Wrote {path}")


if __name__ == "__main__":
    app()

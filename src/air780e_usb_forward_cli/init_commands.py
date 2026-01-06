"""Send an initial sequence of AT commands to the selected port.

Minimal behavior:
- Open the port in write-only mode.
- Send each command from INITIAL_CMDS with CRLF appended, spacing them by `interval_s` seconds.
- Close the port and return regardless of success/failure.
"""
from __future__ import annotations

import os
import time
from typing import Iterable

from .ports import list_at_devices


INITIAL_CMDS: list[str] = [
    "AT+CMGF=1", # Set SMS to text mode
    "AT+CSMP=17,167,0,8", # Set <dcs>=8 (UTF-16BE) for SMS
    "AT+CSCS=IRA", # Set character set to IRA
    "AT+RNDISCALL=0", # Disable network adapter
    "AT&W", # persist settings
]


def send_initial_commands(port: str, commands: Iterable[str] | None = None, interval_s: float = 0.5) -> None:
    cmds = list(commands) if commands is not None else INITIAL_CMDS

    fd = None
    try:
        fd = os.open(port, os.O_WRONLY)
        for cmd in cmds:
            try:
                payload = (cmd + "\r\n").encode("ascii", errors="replace")
                os.write(fd, payload)
            except Exception:
                # Best-effort; continue sending remaining commands.
                pass
            time.sleep(interval_s)
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass


def _self_demo() -> None:
    ports = list_at_devices()
    if not ports:
        print("No AT devices found; nothing to send.")
        return

    target = ports[0]
    print(f"Sending INITIAL_CMDS to {target} ...")
    send_initial_commands(target)
    print("Done.")


if __name__ == "__main__":
    _self_demo()

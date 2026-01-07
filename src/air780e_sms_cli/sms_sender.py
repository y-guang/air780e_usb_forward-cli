"""Send a single SMS via AT+CMGS.

Usage pattern:
- Open port write-only
- Send `AT+CMGS="<phone>"` + CRLF
- Wait a short delay (ignore the `>` prompt)
- Send UTF-16BE encoded body
- Send Ctrl+Z (0x1A) terminator without newline
- Close and return regardless of intermediate errors
"""
from __future__ import annotations

import os
import time


def send_sms(port: str, phone: str, message: str, delay_s: float = 0.5) -> None:
    fd = None
    try:
        fd = os.open(port, os.O_WRONLY)

        try:
            header = f'AT+CMGS="{phone}"\r\n'.encode("ascii", errors="replace")
            os.write(fd, header)
        except Exception:
            pass

        time.sleep(delay_s)

        try:
            body = message.encode("utf-16-be", errors="replace")
            os.write(fd, body)
            os.write(fd, b"\x1A")
        except Exception:
            pass

    finally:
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass


def _self_demo() -> None:
    from .ports import list_at_devices

    devices = list_at_devices()
    if not devices:
        print("No AT devices found; nothing to send.")
        return

    target = devices[0]
    print(f"Sending test SMS to {target} ...")
    send_sms(target, phone="10010", message="CXHF")
    print("Done.")


if __name__ == "__main__":
    _self_demo()

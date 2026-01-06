"""
Listener module: read lines from a port and append messages to a JSONL logfile.

Behavior:
- Accepts `port` (path string or file descriptor int) and `filepath` (log file path).
- Blocks to read a single line, then waits up to `intra_timeout_ms` milliseconds
  to collect any additional complete lines and treat them as the same message.
- Writes one JSON object per message to `filepath` (append mode) with keys:
    - `timestamp`: integer epoch milliseconds for machine consumers
    - `timestamp_local`: ISO 8601 local time (milliseconds)
    - `message_hex`: hex string of the raw bytes payload

Design notes:
- Explicit state machine: WAIT_FIRST_LINE -> COLLECT_WITHIN_WINDOW -> FLUSH_MESSAGE -> repeat
- Uses a tiny line framer to avoid subtle buffer/leftover bugs.
- Stores raw bytes (hex) to avoid encoding ambiguity in AT / mixed-binary streams.
- Flushes after every appended JSON line.

"""

from __future__ import annotations

import json
import os
import select
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union


def _open_fd(port: str | int) -> int:
    if isinstance(port, int):
        return port
    if isinstance(port, str):
        # Open path in blocking mode for reading.
        return os.open(port, os.O_RDONLY)
    raise TypeError("port must be a path string or file descriptor int")


def _now_iso() -> str:
    return datetime.now().isoformat(sep=" ", timespec="milliseconds")


def _now_epoch_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class _LineFramer:
    """Incremental framer that yields complete lines (including the trailing LF)."""

    fd: int
    buf: bytearray = field(default_factory=bytearray)

    def _read_more(self) -> bool:
        chunk = os.read(self.fd, 4096)
        if not chunk:
            return False
        self.buf.extend(chunk)
        return True

    def read_line_blocking(self) -> bytes | None:
        """Return next complete line (including LF). Block until available or EOF."""
        while True:
            line = self._pop_line_if_available()
            if line is not None:
                return line
            if not self._read_more():
                return None  # EOF

    def read_line_with_timeout(self, timeout_s: float) -> bytes | None:
        """Return next complete line (including LF) if it arrives within timeout; else None."""
        deadline = time.time() + timeout_s

        line = self._pop_line_if_available()
        if line is not None:
            return line

        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                return None

            r, _, _ = select.select([self.fd], [], [], remaining)
            if not r:
                return None

            if not self._read_more():
                return None  # EOF

            line = self._pop_line_if_available()
            if line is not None:
                return line

    def _pop_line_if_available(self) -> bytes | None:
        idx = self.buf.find(b"\n")
        if idx < 0:
            return None
        end = idx + 1
        line = bytes(self.buf[:end])
        del self.buf[:end]
        return line


class _State:
    WAIT_FIRST_LINE = "WAIT_FIRST_LINE"
    COLLECT_WITHIN_WINDOW = "COLLECT_WITHIN_WINDOW"


def listen(port: str | int, filepath: str, intra_timeout_ms: int = 100) -> None:
    """Listen on `port` and append messages to `filepath` in JSONL format.

    This function blocks forever until EOF on the port or an error occurs.
    """
    fd = _open_fd(port)
    close_fd = isinstance(port, str)

    framer = _LineFramer(fd=fd)

    timeout_s = max(0.0, intra_timeout_ms / 1000.0)

    state = _State.WAIT_FIRST_LINE
    message_chunks: list[bytes] = []

    try:
        with open(filepath, "a", encoding="utf-8") as logf:
            while True:
                if state == _State.WAIT_FIRST_LINE:
                    first = framer.read_line_blocking()
                    if first is None:
                        return  # EOF
                    message_chunks = [first]
                    state = _State.COLLECT_WITHIN_WINDOW
                    continue

                if state == _State.COLLECT_WITHIN_WINDOW:
                    # Keep pulling complete lines that arrive within the window.
                    # Important: only complete lines join the current message.
                    line = framer.read_line_with_timeout(timeout_s)
                    if line is not None:
                        message_chunks.append(line)
                        continue

                    # Timeout: finalize + flush message.
                    payload = b"".join(message_chunks)

                    entry = {
                        "timestamp_local": _now_iso(),
                        "timestamp": _now_epoch_ms(),
                        "message_hex": payload.hex(),
                    }
                    logf.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    logf.flush()

                    # Reset for next message.
                    message_chunks = []
                    state = _State.WAIT_FIRST_LINE
                    continue

                raise RuntimeError(f"Unknown state: {state}")

    finally:
        if close_fd:
            try:
                os.close(fd)
            except Exception:
                pass


def _self_demo() -> None:
    """Minimal demo: simulate a writer sending CRLF-ish frames into the listener."""
    import threading

    rfd, wfd = os.pipe()

    def writer() -> None:
        # Message 1: multiple lines close together (within 100ms)
        os.write(wfd, b"AT+CGMI\r\n")
        time.sleep(0.02)
        os.write(wfd, b"\r\n")
        time.sleep(0.02)
        os.write(wfd, b"+CGMI: \"AirM2M\"\r\n")
        time.sleep(0.02)
        os.write(wfd, b"\r\n")
        time.sleep(0.02)
        os.write(wfd, b"OK\r\n")

        # Message 2: after a gap (new message)
        time.sleep(0.2)
        os.write(wfd, b"+CIEV: \"MESSAGE\",1\r\n")

        os.close(wfd)

    logpath = os.path.join(os.getcwd(), "listener_demo.jsonl")
    if os.path.exists(logpath):
        os.remove(logpath)

    t = threading.Thread(target=writer, daemon=True)
    t.start()

    # listen returns when writer closes the pipe (EOF)
    listen(rfd, logpath, intra_timeout_ms=100)

    with open(logpath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            obj = json.loads(line)
            print(f"entry {i}: ts={obj['timestamp_local']} bytes={len(bytes.fromhex(obj['message_hex']))}")
            print(bytes.fromhex(obj["message_hex"]))


if __name__ == "__main__":
    from .ports import list_at_devices

    devices = list_at_devices()
    if not devices:
        print("No AT devices found; nothing to listen to.")
    else:
        port_path = devices[0]
        logpath = os.path.join(os.getcwd(), "listener_live.jsonl")
        print(f"Listening on {port_path}, logging to {logpath}")
        listen(port_path, logpath, intra_timeout_ms=100)

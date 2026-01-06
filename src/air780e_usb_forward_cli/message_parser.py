"""Minimal message parser.

Flow:
- Parent decodes incoming hex payload to an ASCII-ish string using latin-1 (lossless for bytes 0-255).
- Each child gets that string; if it recognizes the pattern it returns a transformed string.
- If a child declines or fails, the original ASCII string is returned.

Current child:
- CmtParser: when "+CMT:" is present, replace the quoted hex field with its UTF-16BE decode
    and replace the trailing body-hex line (if decodable) with its UTF-16BE text.
"""
from __future__ import annotations

import binascii
import re
from typing import List, Optional


def _hex_to_bytes(hex_str: str) -> bytes:
    try:
        return binascii.unhexlify(hex_str)
    except (binascii.Error, ValueError):
        return b""


def _safe_decode_utf16be(data: bytes) -> str:
    try:
        return data.decode("utf-16-be", errors="replace")
    except Exception:
        return ""


class MessageParser:
    def __init__(self, children: Optional[List["BaseChildParser"]] = None) -> None:
        self.children = children or [CmtParser()]

    def parse(self, message_hex: str) -> str:
        raw_bytes = _hex_to_bytes(message_hex)
        ascii_view = raw_bytes.decode("latin-1", errors="replace")

        for child in self.children:
            if child.matches(ascii_view):
                out = child.transform(ascii_view)
                return out if out is not None else ascii_view

        return ascii_view


class BaseChildParser:
    def matches(self, ascii_view: str) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    def transform(self, ascii_view: str) -> Optional[str]:  # pragma: no cover - interface
        raise NotImplementedError


class CmtParser(BaseChildParser):
    # Match a line that starts with +CMT: and capture the quoted sender hex.
    sender_pattern = re.compile(r"(?m)^(\+CMT:\s*\")([^\"]*)(\".*)$")
    # Match a line that is only hex digits (body line).
    body_pattern = re.compile(r"(?m)^([0-9A-Fa-f]+)\s*$")

    def matches(self, ascii_view: str) -> bool:
        return bool(self.sender_pattern.search(ascii_view))

    def transform(self, ascii_view: str) -> Optional[str]:
        sender_match = self.sender_pattern.search(ascii_view)
        if not sender_match:
            return None

        sender_hex = sender_match.group(2)
        sender_bytes = _hex_to_bytes(sender_hex)
        sender = _safe_decode_utf16be(sender_bytes) if sender_bytes else ""
        if not sender:
            return ascii_view

        # Replace sender using regex groups to minimize accidental changes.
        def _replace_sender(m: re.Match[str]) -> str:
            return f"{m.group(1)}{sender}{m.group(3)}"

        text = self.sender_pattern.sub(_replace_sender, ascii_view, count=1)

        # Find last pure-hex line (if any) and replace with decoded body.
        last_body_match = None
        for m in self.body_pattern.finditer(text):
            last_body_match = m

        if last_body_match:
            body_hex = last_body_match.group(1)
            body_bytes = _hex_to_bytes(body_hex)
            body_text = _safe_decode_utf16be(body_bytes) if body_bytes else ""
            if body_text:
                start, end = last_body_match.span(1)
                text = text[:start] + body_text + text[end:]

        return text


_DEFAULT_PARSER = MessageParser()


def parse_message_hex(message_hex: str) -> str:
    """Convenience wrapper so callers do not need MessageParser directly."""
    return _DEFAULT_PARSER.parse(message_hex)


def _demo() -> None:
    import json
    import os

    path = os.path.join(os.getcwd(), "messages.jsonl")
    try:
        with open(path, "r", encoding="utf-8") as f:
            first = f.readline()
    except FileNotFoundError:
        print("messages.jsonl not found; nothing to parse")
        return

    if not first:
        print("messages.jsonl is empty; nothing to parse")
        return

    try:
        obj = json.loads(first)
    except json.JSONDecodeError as e:
        print(f"Failed to decode first line: {e}")
        return

    message_hex = obj.get("message_hex")
    if not message_hex:
        print("First record missing 'message_hex'")
        return

    result = parse_message_hex(message_hex)
    print(result)


if __name__ == "__main__":
    _demo()

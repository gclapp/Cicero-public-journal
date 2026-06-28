#!/usr/bin/env python3
"""Windows-safe filename utilities for Obsidian vaults."""

from __future__ import annotations

import re
from pathlib import Path


# Windows reserved device names (case-insensitive), with or without extension.
_RESERVED_RE = re.compile(
    r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)", re.IGNORECASE
)

# Characters illegal in Windows filenames, plus ASCII control characters.
_ILLEGAL_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]')


def sanitize_filename(
    name: str, max_len: int = 120, default: str = "Untitled"
) -> str:
    """Return a Windows/macOS/Linux-safe filename stem or folder name.

    Preserves Unicode letters, numbers, common punctuation, and emojis.
    Removes/replaces control characters and Windows-reserved characters.
    """
    if not isinstance(name, str):
        name = str(name)

    # Replace common delimiter chars with a readable spaced dash.
    name = name.replace("|", " - ")
    name = name.replace(":", " - ")

    # Replace illegal/control chars with space.
    name = _ILLEGAL_RE.sub(" ", name)

    # Collapse whitespace (including newlines/tabs) and trim.
    name = re.sub(r"\s+", " ", name).strip()

    # Drop trailing dots or spaces, which are illegal/problematic on Windows.
    name = name.strip(" .")

    # Avoid Windows reserved device names.
    if _RESERVED_RE.match(name):
        name = f"{name}_file"

    # Limit length, preserving whole words where possible.
    if len(name) > max_len:
        name = name[:max_len].rsplit(" ", 1)[0].strip(" .")
    if not name:
        name = default
    return name


def sanitize_path_part(
    name: str, max_len: int = 80, default: str = "folder"
) -> str:
    """Sanitize a single path component (directory or file basename)."""
    return sanitize_filename(name, max_len=max_len, default=default)


def safe_note_path(
    directory: Path, title: str, ext: str = ".md", max_len: int = 120
) -> Path:
    """Return a Path under ``directory`` with a sanitized filename, avoiding collisions."""
    directory = Path(directory)
    stem = sanitize_filename(title, max_len=max_len)
    candidate = directory / f"{stem}{ext}"
    if not candidate.exists():
        return candidate
    # Handle collision by appending a counter before the extension.
    for n in range(1, 10000):
        candidate = directory / f"{stem}_{n}{ext}"
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not find unique name for {stem}{ext}")


def is_windows_safe(name: str, max_len: int = 120) -> tuple[bool, list[str]]:
    """Return (safe, reasons) for a single path component name."""
    reasons: list[str] = []
    if _ILLEGAL_RE.search(name):
        reasons.append("illegal_chars")
    if any(ord(c) < 32 for c in name):
        reasons.append("control_char")
    if name != name.strip():
        reasons.append("leading/trailing_space")
    if name.endswith(".") or name.endswith(" "):
        reasons.append("trailing_dot/space")
    if _RESERVED_RE.match(name):
        reasons.append("reserved_name")
    if len(name) > max_len:
        reasons.append(f"too_long({len(name)})")
    return (not reasons, reasons)


if __name__ == "__main__":
    import sys

    for arg in sys.argv[1:]:
        print(f"{arg!r} -> {sanitize_filename(arg)!r}")

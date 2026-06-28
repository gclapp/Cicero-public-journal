#!/usr/bin/env python3
"""Rename Obsidian vault files/folders so they are safe for Windows sync clients.

Scans the configured vault for path components containing:
  - Windows-illegal characters (\\ / : * ? " < > |)
  - ASCII control characters (including newlines)
  - Leading/trailing spaces or trailing dots
  - Windows reserved device names
  - Overly long basenames

By default performs a dry run; pass --execute to rename files.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make the shared utility importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from obsidian_filename import sanitize_filename, is_windows_safe


VAULT = Path("/home/ubuntu/Obsidian/geoffclapp")
SKIP_DIRS = {".obsidian", ".git", ".trash"}


def scan_vault(vault: Path) -> list[tuple[Path, Path, list[str]]]:
    """Return list of (old_path, new_path, reasons) for items that need renaming."""
    renames: list[tuple[Path, Path, list[str]]] = []
    used_targets: dict[Path, set[str]] = {}

    for root, dirs, files in os.walk(vault, topdown=False):
        # Filter traversal dirs in-place.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for name in files + dirs:
            old_path = Path(root) / name
            rel = old_path.relative_to(vault)

            # Determine which path component is problematic.
            reasons: list[str] = []
            for part in rel.parts:
                _, part_reasons = is_windows_safe(part)
                if part_reasons:
                    reasons.extend(f"{r}:{part}" for r in part_reasons)

            if not reasons:
                continue

            # Build new relative path by sanitizing each component.
            new_parts = []
            parts = rel.parts
            for idx, part in enumerate(parts):
                safe, _ = is_windows_safe(part)
                if safe:
                    new_parts.append(part)
                    continue
                # Preserve file extension when sanitizing the last component of a file.
                is_last = idx == len(parts) - 1
                if is_last and old_path.is_file():
                    stem = Path(part).stem
                    suffix = Path(part).suffix
                    sanitized = sanitize_filename(stem, max_len=120) + suffix
                else:
                    sanitized = sanitize_filename(part, max_len=120)
                new_parts.append(sanitized)
            new_rel = Path(*new_parts)
            new_path = vault / new_rel

            # Handle collisions within the same parent directory.
            parent = new_path.parent
            stem = new_path.stem if new_path.suffix else new_path.name
            suffix = new_path.suffix
            final_name = f"{stem}{suffix}"
            counter = 1
            used = used_targets.setdefault(parent, set(p.name for p in parent.iterdir()))
            while final_name in used:
                final_name = f"{stem}_{counter}{suffix}"
                counter += 1
            used.add(final_name)
            new_path = parent / final_name

            renames.append((old_path, new_path, reasons))

    return renames


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean up Windows-illegal filenames in the Obsidian vault."
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=VAULT,
        help="Path to Obsidian vault (default: /home/ubuntu/Obsidian/geoffclapp)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually rename files. Without this, only prints planned renames.",
    )
    args = parser.parse_args()

    vault = args.vault.expanduser().resolve()
    if not vault.is_dir():
        print(f"Vault not found: {vault}", file=sys.stderr)
        return 1

    renames = scan_vault(vault)
    if not renames:
        print("No Windows-unsafe filenames found.")
        return 0

    print(f"Found {len(renames)} item(s) needing rename:\n")
    for old, new, reasons in renames:
        print(f"  {old.relative_to(vault)}")
        print(f"    -> {new.relative_to(vault)}")
        print(f"    reasons: {', '.join(reasons)}")
        print()

    if not args.execute:
        print("Dry run complete. Pass --execute to apply the renames above.")
        return 2

    renamed_count = 0
    for old, new, _ in renames:
        if new.exists():
            print(f"SKIP (target exists): {new}", file=sys.stderr)
            continue
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
        renamed_count += 1

    print(f"Renamed {renamed_count} item(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

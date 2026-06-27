#!/usr/bin/env python3
"""Small wrapper for Obsidian Headless sync on the OpenClaw host.

This deliberately avoids accepting passwords on the command line. Run
`login` interactively so credentials stay inside the Obsidian client.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path("/home/ubuntu/Obsidian")
DEFAULT_DEVICE_NAME = "OpenClaw AWS"


def run(args: list[str]) -> int:
    if shutil.which("ob") is None:
        print("Missing `ob`. Install with: npm install -g obsidian-headless", file=sys.stderr)
        return 127
    print("+", " ".join(args))
    return subprocess.call(args)


def vault_path(name: str) -> Path:
    if "/" in name or name in {"", ".", ".."}:
        raise SystemExit("Vault name must be a simple folder name, for example: OpenAI Work")
    return BASE_DIR / name


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Obsidian Sync bridge for OpenClaw.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login", help="Run interactive Obsidian account login.")
    sub.add_parser("logout", help="Logout of Obsidian account.")
    sub.add_parser("remote", help="List Obsidian Sync remote vaults.")
    sub.add_parser("local", help="List local configured sync vaults.")

    status = sub.add_parser("status", help="Show sync status for a local vault.")
    status.add_argument("vault", help="Local vault folder name under /home/ubuntu/Obsidian.")

    setup = sub.add_parser("setup", help="Connect a local path to a remote vault.")
    setup.add_argument("remote_vault", help="Remote vault ID or name from `remote`.")
    setup.add_argument("local_vault", help="Local folder name under /home/ubuntu/Obsidian.")
    setup.add_argument("--device-name", default=DEFAULT_DEVICE_NAME)

    sync = sub.add_parser("sync", help="Run a one-shot or continuous sync.")
    sync.add_argument("vault", help="Local vault folder name under /home/ubuntu/Obsidian.")
    sync.add_argument("--continuous", action="store_true")

    args = parser.parse_args()

    if args.cmd == "login":
        return run(["ob", "login"])
    if args.cmd == "logout":
        return run(["ob", "logout"])
    if args.cmd == "remote":
        return run(["ob", "sync-list-remote"])
    if args.cmd == "local":
        return run(["ob", "sync-list-local"])
    if args.cmd == "status":
        return run(["ob", "sync-status", "--path", str(vault_path(args.vault))])
    if args.cmd == "setup":
        path = vault_path(args.local_vault)
        path.mkdir(parents=True, exist_ok=True)
        return run(
            [
                "ob",
                "sync-setup",
                "--vault",
                args.remote_vault,
                "--path",
                str(path),
                "--device-name",
                args.device_name,
            ]
        )
    if args.cmd == "sync":
        cmd = ["ob", "sync", "--path", str(vault_path(args.vault))]
        if args.continuous:
            cmd.append("--continuous")
        return run(cmd)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

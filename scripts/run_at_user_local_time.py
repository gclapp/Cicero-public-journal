#!/usr/bin/env python3
"""Run a command once per local day when Geoff's resolved local time is due."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from user_timezone import local_now, resolve_timezone

STATE_FILE = Path("/home/ubuntu/.openclaw/workspace/state/local-schedule-state.json")


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def _parse_hm(value: str) -> time:
    try:
        hour, minute = value.split(":", 1)
        return time(int(hour), int(minute))
    except Exception as exc:
        raise argparse.ArgumentTypeError("Expected HH:MM in 24-hour local time") from exc


def _due(now_local: datetime, target: time, window_minutes: int) -> bool:
    target_dt = now_local.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
    return target_dt <= now_local < target_dt + timedelta(minutes=window_minutes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--at", required=True, type=_parse_hm, help="Local HH:MM")
    parser.add_argument("--window-minutes", type=int, default=15)
    parser.add_argument("--skip-in-transit", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("command is required after --")

    now_utc = datetime.now(timezone.utc)
    match = resolve_timezone(now_utc)
    now_local = local_now(now_utc)
    run_key = f"{args.job_id}:{now_local.strftime('%Y-%m-%d')}:{args.at.strftime('%H:%M')}"

    if not _due(now_local, args.at, args.window_minutes):
        if args.verbose:
            print(
                f"not due: {args.job_id} at {now_local.strftime('%Y-%m-%d %H:%M %Z')} "
                f"({match.timezone_name}, {match.label})"
            )
        return 0

    state = _load_state()
    if args.skip_in_transit and match.in_transit:
        run_key = f"{run_key}:skipped-in-transit"
        if state.get(run_key):
            if args.verbose:
                print(f"already skipped in transit: {run_key}")
            return 0
        state[run_key] = {
            "skipped_at_utc": now_utc.isoformat(),
            "timezone": match.timezone_name,
            "reason": match.label,
        }
        _save_state(state)
        print(
            f"skipping {args.job_id}: Geoff appears in transit at "
            f"{now_local.strftime('%Y-%m-%d %H:%M %Z')} ({match.label})"
        )
        return 0

    if state.get(run_key):
        if args.verbose:
            print(f"already ran: {run_key}")
        return 0

    print(
        f"running {args.job_id} at {now_local.strftime('%Y-%m-%d %H:%M %Z')} "
        f"({match.timezone_name}, {match.label})"
    )
    result = subprocess.run(command)
    if result.returncode == 0:
        state[run_key] = {
            "ran_at_utc": now_utc.isoformat(),
            "timezone": match.timezone_name,
            "reason": match.label,
            "command": command,
        }
        # Keep the state file bounded.
        if len(state) > 500:
            state = dict(sorted(state.items())[-500:])
        _save_state(state)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

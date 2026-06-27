#!/usr/bin/env python3
"""Create/update Obsidian meeting notes from work calendar ICS exports."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from dateutil.tz import gettz
from icalendar import Calendar


VAULT = Path("/home/ubuntu/Obsidian/geoffclapp")
ICS_DIR = VAULT / "02_PGNY_RAW" / "Calendar" / "Work"
MEETING_DIR = VAULT / "02_PGNY_RAW" / "PGNY Notes"
PROCESSED_CAL_DIR = VAULT / "22_PGNY_PROCESSED" / "Calendar"
STATE_PATH = Path("/home/ubuntu/.openclaw/workspace/state/obsidian-calendar-ingest.json")
LOCAL_TZ = gettz("America/Los_Angeles")
GEN_START = "<!-- CICERO_CALENDAR_START -->"
GEN_END = "<!-- CICERO_CALENDAR_END -->"


@dataclass
class Meeting:
    uid: str
    uid_hash: str
    title: str
    start: datetime | date | None
    end: datetime | date | None
    location: str
    description: str
    organizer: str
    attendees: list[str]
    status: str
    source_file: Path


def text_value(value: Any) -> str:
    if value is None:
        return ""
    try:
        decoded = value.to_ical().decode("utf-8")
    except Exception:
        decoded = str(value)
    return decoded.replace("\\n", "\n").replace("\\,", ",").strip()


def decoded_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        return value.dt
    except AttributeError:
        return value


def ensure_dt(value: datetime | date | None) -> datetime | date | None:
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=LOCAL_TZ)
    return value


def as_local(value: datetime | date | None) -> datetime | date | None:
    value = ensure_dt(value)
    if isinstance(value, datetime):
        return value.astimezone(LOCAL_TZ)
    return value


def fmt_dt(value: datetime | date | None) -> str:
    value = as_local(value)
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %I:%M %p %Z")
    return value.isoformat()


def iso_dt(value: datetime | date | None) -> str:
    value = as_local(value)
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return value.isoformat()


def slug(text: str, max_len: int = 80) -> str:
    text = re.sub(r"[\\/:*?\"<>|\n\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len].strip(" .") or "Untitled Meeting"


def uid_hash(uid: str) -> str:
    return hashlib.sha256(uid.encode("utf-8")).hexdigest()[:10]


def yaml_string(value: str) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "\n" + "\n".join(f"  - {yaml_string(v)}" for v in values)


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"meetings": {}}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def attendee_text(attendee: Any) -> str:
    email = text_value(attendee)
    cn = ""
    try:
        cn = attendee.params.get("CN", "")
    except Exception:
        cn = ""
    if cn and email and cn not in email:
        return f"{cn} <{email.replace('MAILTO:', '').replace('mailto:', '')}>"
    return email.replace("MAILTO:", "").replace("mailto:", "")


def parse_ics(path: Path) -> list[Meeting]:
    cal = Calendar.from_ical(path.read_bytes())
    meetings: list[Meeting] = []
    for component in cal.walk("VEVENT"):
        title = text_value(component.get("summary")) or "Untitled Meeting"
        raw_uid = text_value(component.get("uid"))
        start = decoded_value(component.get("dtstart"))
        end = decoded_value(component.get("dtend"))
        if not raw_uid:
            raw_uid = f"{title}|{iso_dt(start)}|{path.name}"
        raw_attendees = component.get("attendee", [])
        if raw_attendees and not isinstance(raw_attendees, list):
            raw_attendees = [raw_attendees]
        attendees = [attendee_text(a) for a in raw_attendees if attendee_text(a)]
        meetings.append(
            Meeting(
                uid=raw_uid,
                uid_hash=uid_hash(raw_uid),
                title=title,
                start=start,
                end=end,
                location=text_value(component.get("location")),
                description=text_value(component.get("description")),
                organizer=attendee_text(component.get("organizer")) if component.get("organizer") else "",
                attendees=attendees,
                status=text_value(component.get("status")) or "CONFIRMED",
                source_file=path,
            )
        )
    return meetings


def default_note_path(meeting: Meeting) -> Path:
    start = as_local(meeting.start)
    if isinstance(start, datetime):
        prefix = start.strftime("%Y-%m-%d - %H%M")
    elif isinstance(start, date):
        prefix = start.isoformat()
    else:
        prefix = "Undated"
    return MEETING_DIR / f"{prefix} - {slug(meeting.title)} - {meeting.uid_hash}.md"


def find_existing_note(meeting: Meeting, state: dict[str, Any]) -> Path | None:
    existing = state.get("meetings", {}).get(meeting.uid_hash, {}).get("path")
    if existing and Path(existing).exists():
        return Path(existing)
    marker = f"calendar_uid_hash: {yaml_string(meeting.uid_hash)}"
    for path in MEETING_DIR.glob("**/*.md"):
        try:
            if marker in path.read_text(errors="ignore"):
                return path
        except OSError:
            continue
    return None


def generated_block(meeting: Meeting) -> str:
    attendees = "\n".join(f"- {a}" for a in meeting.attendees) or "- None listed"
    agenda = meeting.description.strip() or "_No agenda or description included in the calendar invite._"
    return f"""{GEN_START}
## Calendar Details

- Title: {meeting.title}
- Status: {meeting.status}
- Date/time: {fmt_dt(meeting.start)} to {fmt_dt(meeting.end)}
- Location: {meeting.location or "Not listed"}
- Organizer: {meeting.organizer or "Not listed"}
- Source ICS: {meeting.source_file.name}
- Calendar UID: `{meeting.uid}`

## Attendees

{attendees}

## Agenda / Invite Description

{agenda}
{GEN_END}"""


def frontmatter(meeting: Meeting) -> str:
    return f"""---
type: meeting
source: calendar_ics
status: raw
calendar_uid: {yaml_string(meeting.uid)}
calendar_uid_hash: {yaml_string(meeting.uid_hash)}
meeting_title: {yaml_string(meeting.title)}
meeting_status: {yaml_string(meeting.status)}
meeting_start: {yaml_string(iso_dt(meeting.start))}
meeting_end: {yaml_string(iso_dt(meeting.end))}
location: {yaml_string(meeting.location)}
organizer: {yaml_string(meeting.organizer)}
attendees: {yaml_list(meeting.attendees)}
source_ics: {yaml_string(str(meeting.source_file.relative_to(VAULT)))}
transcript:
transcript_status: pending
processed_note:
---
"""


def new_note(meeting: Meeting) -> str:
    return f"""{frontmatter(meeting)}
# {meeting.title}

{generated_block(meeting)}

## Geoff's Notes


## Transcript Link

- Transcript:

## Decisions


## Follow-Ups


## Cicero Processing Notes

"""


def replace_generated_block(existing: str, meeting: Meeting) -> str:
    block = generated_block(meeting)
    if GEN_START in existing and GEN_END in existing:
        pattern = re.compile(re.escape(GEN_START) + r".*?" + re.escape(GEN_END), re.DOTALL)
        return pattern.sub(block, existing, count=1)
    return existing.rstrip() + "\n\n" + block + "\n"


def update_frontmatter(existing: str, meeting: Meeting) -> str:
    new_fm = frontmatter(meeting).strip()
    if existing.startswith("---\n"):
        end = existing.find("\n---", 4)
        if end != -1:
            return new_fm + existing[end + 4 :]
    return new_fm + "\n\n" + existing


def write_meeting(meeting: Meeting, state: dict[str, Any], dry_run: bool) -> tuple[Path, str]:
    MEETING_DIR.mkdir(parents=True, exist_ok=True)
    path = find_existing_note(meeting, state) or default_note_path(meeting)
    action = "updated" if path.exists() else "created"
    if dry_run:
        return path, action
    if path.exists():
        content = path.read_text()
        content = update_frontmatter(content, meeting)
        content = replace_generated_block(content, meeting)
    else:
        content = new_note(meeting)
    path.write_text(content)
    state.setdefault("meetings", {})[meeting.uid_hash] = {
        "uid": meeting.uid,
        "title": meeting.title,
        "start": iso_dt(meeting.start),
        "end": iso_dt(meeting.end),
        "path": str(path),
        "source_ics": str(meeting.source_file),
    }
    return path, action


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest work calendar ICS files into Obsidian meeting notes.")
    parser.add_argument("--ics-dir", type=Path, default=ICS_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    state = load_state()
    paths = sorted(args.ics_dir.glob("*.ics"))
    if not paths:
        print(f"No .ics files found in {args.ics_dir}")
        return 0

    count = 0
    for ics in paths:
        for meeting in parse_ics(ics):
            path, action = write_meeting(meeting, state, args.dry_run)
            print(f"{action}: {meeting.title} -> {path}")
            count += 1
            if args.limit and count >= args.limit:
                break
        if args.limit and count >= args.limit:
            break

    if not args.dry_run:
        save_state(state)
    print(f"Processed {count} meeting(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

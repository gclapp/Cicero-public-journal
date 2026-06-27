# Obsidian Calendar ICS Process

Purpose: when Geoff drops a work calendar `.ics` export into Obsidian, Cicero creates or updates raw meeting notes that Geoff can use during the meeting and later tie to transcripts.

## Input

Drop `.ics` files here:

```text
/home/ubuntu/Obsidian/geoffclapp/02_PGNY_RAW/Calendar/Work/
```

Preferred names:

```text
work-calendar-YYYY-MM-DD.ics
work-calendar-YYYY-MM-DD_to_YYYY-MM-DD.ics
```

## Output

Meeting notes are created or updated here:

```text
/home/ubuntu/Obsidian/geoffclapp/02_PGNY_RAW/PGNY Notes/
```

The note contains:

- Title
- Date/time
- Location
- Organizer
- Attendees
- Agenda / invite description, if present
- A protected calendar metadata block that Cicero can refresh
- A `Geoff's Notes` section that Cicero must preserve
- Transcript link fields for later tying notes to transcripts

## Deduplication And Moved Meetings

Cicero matches meetings by calendar UID first. Each note stores:

```yaml
calendar_uid:
calendar_uid_hash:
```

If a meeting is re-exported after moving or changing attendees, Cicero updates the existing note's calendar metadata and frontmatter instead of creating a duplicate.

If no UID is available, Cicero falls back to a generated UID from title, start time, and source file.

## Do Not Overwrite Human Notes

Cicero only rewrites the block between:

```text
<!-- CICERO_CALENDAR_START -->
<!-- CICERO_CALENDAR_END -->
```

Everything outside that block, including `Geoff's Notes`, transcript links, decisions, and follow-ups, must be preserved.

## Command

Use the dedicated virtualenv:

```bash
/home/ubuntu/.openclaw/workspace/.venvs/obsidian-calendar/bin/python scripts/obsidian_calendar_ingest.py
```

Dry run:

```bash
/home/ubuntu/.openclaw/workspace/.venvs/obsidian-calendar/bin/python scripts/obsidian_calendar_ingest.py --dry-run
```

## Automation

The process runs every five minutes through a systemd user timer:

```bash
systemctl --user status obsidian-calendar-ingest.timer --no-pager
journalctl --user -u obsidian-calendar-ingest.service -n 80 --no-pager
```

Current service files:

```text
/home/ubuntu/.config/systemd/user/obsidian-calendar-ingest.service
/home/ubuntu/.config/systemd/user/obsidian-calendar-ingest.timer
```

Flow:

```text
Obsidian Sync downloads ICS -> timer runs ingester -> meeting notes are created/updated -> Obsidian Sync uploads notes
```

## Recommended Transcript Flow

1. Calendar ICS creates the raw meeting shell.
2. Geoff takes notes in `## Geoff's Notes`.
3. Transcript file lands in `02_PGNY_RAW/PGNY Transcripts/`.
4. Cicero links the transcript in the meeting note.
5. Cicero creates a processed summary in `22_PGNY_PROCESSED/` with decisions, actions, open loops, and themes.

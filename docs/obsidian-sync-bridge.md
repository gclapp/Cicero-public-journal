# Obsidian Sync Bridge

Goal: use Geoff's existing Obsidian Sync/Cloud setup as the transport layer between his devices and OpenClaw, instead of creating a separate Git copy.

## Model

```text
Geoff's Obsidian apps
  -> Obsidian Sync remote vaults
  -> Obsidian Headless on OpenClaw
  -> local vault folders under /home/ubuntu/Obsidian/
  -> Cicero reads and writes normal Markdown files
```

Obsidian remains the user interface and source-of-truth workflow. OpenClaw only gets a synced local copy through the same Obsidian Sync account.

Active synced vault:

```text
/home/ubuntu/Obsidian/geoffclapp/
```

Continuous sync service:

```text
obsidian-sync-geoffclapp.service
```

Calendar ICS ingestion timer:

```text
obsidian-calendar-ingest.timer
```

## Installed Tool

Obsidian Headless is installed globally:

```bash
npm install -g obsidian-headless
```

The command is:

```bash
ob
```

Local wrapper:

```bash
python3 scripts/obsidian_sync_bridge.py --help
```

## First-Time Setup

Do not pass Obsidian passwords on the command line. Run login interactively:

```bash
python3 scripts/obsidian_sync_bridge.py login
```

Then list remote vaults:

```bash
python3 scripts/obsidian_sync_bridge.py remote
```

After confirming the remote vault names, connect the remote vault to the matching local path:

```bash
python3 scripts/obsidian_sync_bridge.py setup "geoffclapp" "geoffclapp"
```

If the remote vault names differ, use the exact names returned by `remote`.

## Normal Commands

List configured local vaults:

```bash
python3 scripts/obsidian_sync_bridge.py local
```

Check sync status:

```bash
python3 scripts/obsidian_sync_bridge.py status "geoffclapp"
```

Run one sync:

```bash
python3 scripts/obsidian_sync_bridge.py sync "geoffclapp"
```

Run continuous sync:

```bash
python3 scripts/obsidian_sync_bridge.py sync "geoffclapp" --continuous
```

## Safety Rules

- Do not create a Git bridge unless Obsidian Sync proves insufficient.
- Do not ask Geoff to paste Obsidian credentials into chat.
- Do not point sync at broad or unrelated folders.
- Check remote vault names before running setup.
- Treat raw work calendar files and meeting notes as private source material.
- If sync conflicts appear, stop and ask before resolving or deleting anything.

## Access Grant

On 2026-06-27, Geoff granted Cicero full editorial access to synced Obsidian vaults for:

- Processing files
- Moving and organizing files
- Editing notes
- Summarizing source material
- Creating new notes, folders, indexes, briefs, and processed artifacts

Guardrails still apply:

- Do not expose credentials or secrets.
- Do not paste broad private vault contents into external systems without approval.
- Prefer archive/trash over irreversible deletion unless Geoff explicitly asks for deletion.
- Preserve raw source material when processing work notes, calendar exports, transcripts, and attachments.

## User-Facing Drop Folders

Actual synced vault:

```text
/home/ubuntu/Obsidian/geoffclapp/
```

Work calendar exports:

```text
/home/ubuntu/Obsidian/geoffclapp/02_PGNY_RAW/Calendar/Work/
```

Processed calendar summaries:

```text
/home/ubuntu/Obsidian/geoffclapp/22_PGNY_PROCESSED/Calendar/
```

PGNY briefs:

```text
/home/ubuntu/Obsidian/geoffclapp/22_PGNY_PROCESSED/Briefs/
```

## Windows Filename Compatibility

Obsidian Sync supports many characters that Windows refuses in filenames (`|`, `"`, `*`, `:`, `<`, `>`, `?`, `\`, `/`, leading/trailing spaces, trailing dots, newlines). iOS share-sheet saves and clipped web content often include `|` or multi-line titles, which then fail to sync to Windows clients with errors like:

- `Ignoring remote file name with illegal characters ...`
- `ENOENT: no such file or directory, open 'C:\Vaults\geoffclapp\...'`

A shared `sanitize_filename()` helper lives in:

```text
scripts/obsidian_filename.py
```

Two scripts use it for all filenames they create:

```text
scripts/obsidian_social_ingest.py
scripts/obsidian_calendar_ingest.py
```

A daily cleanup job scans the synced vault and renames any Windows-unsafe files created by other devices:

```text
obsidian-windows-cleanup.timer -> obsidian-windows-cleanup.service
```

Manual check or cleanup:

```bash
python3 scripts/obsidian_windows_filename_cleanup.py
python3 scripts/obsidian_windows_filename_cleanup.py --execute
```

Renaming preserves content and avoids Windows-reserved device names, trailing dots/spaces, control characters, and paths longer than 260 characters.

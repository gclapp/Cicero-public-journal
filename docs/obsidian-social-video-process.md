# Obsidian Social / Video Processing

Purpose: turn Geoff's saved social links, especially Instagram/Reels, into organized processed knowledge notes.

## Current Raw Inputs

Saved links live mainly under:

```text
/home/ubuntu/Obsidian/geoffclapp/00_Unprocessed_Raw/
/home/ubuntu/Obsidian/geoffclapp/00_Unprocessed_Raw/AI Materials/
```

Most current notes are one-line Markdown links, so processing must fetch metadata before summarizing.

## Processed Output

Processed notes live under:

```text
/home/ubuntu/Obsidian/geoffclapp/10_Articles_Processed/
```

Current folder taxonomy:

```text
10_Articles_Processed/
  _System/
  AI/
    Agents/
    Claude Code/
    Obsidian Setups/
    Product Management/
    Prompting/
    Tools/
  Entertainment/
  Finance/
  Health/
  Leadership/
```

## Tooling

- `yt-dlp` for metadata/media fetches.
- `ffmpeg` for media/audio handling.
- `whisper` for local transcription.

Media downloads and temporary transcripts stay in workspace state by default:

```text
/home/ubuntu/.openclaw/workspace/state/social-ingest/
```

Do not store downloaded video files in Obsidian unless Geoff explicitly asks.

## Current Commands

Inventory all saved social links:

```bash
python3 scripts/obsidian_social_ingest.py --inventory-report
```

Run a small Instagram metadata pilot:

```bash
python3 scripts/obsidian_social_ingest.py --pilot --limit 10
```

Create processed notes for successful pilot metadata:

```bash
python3 scripts/obsidian_social_ingest.py --create-notes-from-pilot
```

## Current Pilot Result

First pilot:

- 72 social links found.
- 49 Instagram links found.
- 10 Instagram items tested for metadata.
- 7 succeeded anonymously.
- 3 failed and likely need auth/manual review.
- 7 processed notes created.
- 1 short Reel audio downloaded and transcribed with local Whisper `tiny`; transcript inserted into the processed note.

## Processing Rules

- Preserve raw saved-link notes.
- Create processed notes in topical folders.
- Link processed notes back to raw notes and source URLs.
- Use metadata/caption first.
- Download/transcribe video only when metadata fetch succeeds and the item is worth processing.
- Keep media cache outside Obsidian.
- Mark failed/auth-required items clearly instead of silently skipping.
- Prefer a controlled folder taxonomy plus metadata/tags over one-off folder sprawl.

## Next Improvements

- Add automated media download/transcription mode with a safe limit.
- Add transcript cleanup using a stronger model or a second-pass text cleanup.
- Add raw-note frontmatter updates linking to processed notes.
- Add duplicate detection by source URL.
- Add an `_Review` queue for low-confidence classifications and auth-required items.

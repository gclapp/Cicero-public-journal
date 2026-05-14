# Obsidian Setup for Cicero Workspace

## Quick Start

1. **Install Obsidian:** https://obsidian.md/download
2. **Open as vault:** File → Open folder as vault → Select `/home/ubuntu/.openclaw/workspace`
3. **Done** — Your workspace is now an Obsidian vault

## What's Configured

### Core Plugins Enabled
- **Graph view** — Visual map of note connections
- **Backlinks** — See where notes are referenced
- **Daily notes** — Quick journal entries
- **Command palette** — Cmd/Ctrl+P for everything
- **Outline** — Document structure sidebar

### File Organization
```
workspace/
├── MEMORY.md              # Main knowledge hub
├── SOUL.md               # My identity
├── USER.md               # About you
├── TOOLS.md              # Scripts & automations
├── AGENTS.md             # Agent guidelines
├── HEARTBEAT.md          # Check-in schedule
├── memory/               # Daily logs
│   ├── 2026-05-13.md
│   └── friend-profiles/
├── scripts/              # Automation scripts
├── config/               # Configuration
└── .obsidian/            # Obsidian settings
```

## How We Work Together

| Task | Where |
|------|-------|
| Read/write notes | Obsidian (pretty, fast, linked) |
| Run automations | Scripts (unchanged) |
| Health data | Dashboard + scripts |
| Cron jobs | Server-side (unaffected) |

## Key Workflows

### Daily Notes
- **Cmd/Ctrl+P** → "Daily notes: Open today's daily note"
- Creates `memory/2026-05-13.md` automatically
- Template ready for quick capture

### Linking Notes
- Type `[[` to link to any existing note
- Use `[[MEMORY#Section]]` to link to headers
- Backlinks auto-appear in right sidebar

### Graph View
- **Cmd/Ctrl+P** → "Graph view: Open graph view"
- See how MEMORY, SOUL, USER, daily notes connect
- Filter by tags, paths

### Search Everything
- **Cmd/Ctrl+O** — Quick open any file
- **Cmd/Ctrl+Shift+F** — Full-text search

## Automation Compatibility

✅ **Safe to edit in Obsidian:**
- All `.md` files
- Adding new notes
- Creating links
- Daily notes

⚠️ **Don't change in Obsidian:**
- Files in `scripts/` (code)
- Files in `config/` (JSON configs)
- `.obsidian/` folder itself

## Templates (Optional Enhancement)

Create `templates/` folder for:
- Meeting notes
- Project plans
- Friend profile updates

Then: Settings → Templates → Set template folder

## Sync Options

| Option | Cost | Best For |
|--------|------|----------|
| Obsidian Sync | $8/mo | Official, fast, version history |
| Git + GitHub | Free | Nerdy, full control, works with our system |
| iCloud/Dropbox | Free | Simple, already using |

**Recommendation:** Since we already use GitHub, add the Obsidian Git plugin for auto-commit on changes.

## Next Steps

1. Open the vault
2. Cmd+O → type "MEMORY" → see your knowledge graph
3. Try creating a linked note: `[[Test Note]]`
4. Open graph view to see the connection

Questions? Ask me.

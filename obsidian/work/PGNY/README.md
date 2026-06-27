# PGNY Operating System

This is the canonical work-side home for Progyny notes, briefs, calendar context, actions, decisions, meetings, and project material.

Agent-facing operating instructions live in `obsidian/openclaw/`. Human/work knowledge lives here.

## How This Connects

- `/home/ubuntu/Obsidian/OpenAI Work/00 Cicero Inbox/` is the user-facing capture folder inside the Obsidian work vault.
- `shared-inbox/` is an optional backend/transport channel, not the primary place Geoff should think about.
- `obsidian/openclaw/` documents agents, responsibilities, and boundaries.
- `obsidian/work/PGNY/` is where processed work knowledge and recurring briefs belong.
- `/home/ubuntu/Obsidian/OpenClaw/` is the local assembled vault view that points back to this system.

## Folder Map

```text
PGNY/
├── Briefs/             # Recurring brief definitions and generated brief outputs
├── Sources/
│   └── Calendar/       # Processed calendar snapshots
├── Templates/          # Reusable brief templates
├── Actions/            # Work follow-ups that need tracking
├── Decisions/          # Decisions and rationale
├── Meetings/           # Processed meeting notes
└── Projects/           # Product, org, customer, board, and strategy threads
```

## Operating Rules

1. Preserve raw source material in the relevant vault's `00 Cicero Inbox/` folder.
2. Process work material into this PGNY folder.
3. Link processed notes back to their source when possible.
4. Keep calendar exports private and summarize only what matters.
5. Create actions only for real follow-up work.
6. Do not duplicate Todoist tasks; record Todoist IDs when tasks exist.
7. Briefs are synthesis notes, not transcript dumps.

## Recurring Briefs

- `Briefs/Sunday Morning - Week Ahead.md`: prepares the coming week.
- `Briefs/Wednesday - Midweek Execution Update.md`: resets the week while there is still time to act.
- `Briefs/Weekly Review.md`: closes the week and carries forward the right work.

## Calendar

Raw work calendar exports should be placed in:

```text
/home/ubuntu/Obsidian/OpenAI Work/00 Cicero Inbox/Calendar/Work/
```

Processed calendar snapshots should be written to:

```text
obsidian/work/PGNY/Sources/Calendar/
```

If a local assembled vault is being used, raw exports can also be dropped into:

```text
/home/ubuntu/Obsidian/OpenClaw/00 Inbox/Calendar/Work/
```

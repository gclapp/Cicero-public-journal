# Multi-AI Second Brain

This system uses Obsidian as the source of truth that can feed multiple AI systems without letting those systems overwrite or contradict each other.

## Goal

Make Geoff's Obsidian vaults the durable memory and operating context layer for:

- OpenClaw and Cicero
- Coding agents
- ChatGPT projects or custom GPTs
- Claude projects
- Gemini or other research assistants
- Local tools that need structured context

## Core Principle

Obsidian is canonical. AI systems are clients.

An AI system may read scoped context, produce notes, suggest actions, or draft decisions, but it should not silently rewrite canonical notes.

## System Layers

```text
1. Raw capture
   /home/ubuntu/Obsidian/OpenAI Work/00 Cicero Inbox/
   /home/ubuntu/Obsidian/OpenAI Home/00 Cicero Inbox/

2. Canonical notes
   obsidian/work/
   obsidian/home/
   obsidian/openclaw/

3. Scoped context packs
   obsidian/openclaw/context-packs/

4. AI outputs for review
   00 Cicero Inbox/AI Systems/ inside the relevant Obsidian vault

5. Processed updates
   Merged back into canonical notes by Cicero or Geoff
```

## Access Model

Use the smallest useful context packet for each AI system.

Do not give every system the whole vault by default.

Suggested scopes:

- `public`: non-sensitive reusable operating model.
- `work`: PGNY and professional context.
- `personal`: family, home, friends, preferences.
- `health`: health data and coaching context.
- `travel`: travel logic, trip context, loyalty preferences.
- `technical`: code, system architecture, scripts, integrations.

## Context Packs

Context packs are curated markdown files designed to be pasted, uploaded, indexed, or synced into another AI system.

They should include:

- Purpose
- What the AI is allowed to use
- What the AI should avoid
- Source folders
- Update cadence
- Return path for outputs
- Privacy level

Canonical folder:

```text
obsidian/openclaw/context-packs/
```

## Return Path

Outputs from other AI systems should come back as raw material first:

```text
/home/ubuntu/Obsidian/OpenAI Work/00 Cicero Inbox/AI Systems/
/home/ubuntu/Obsidian/OpenAI Home/00 Cicero Inbox/AI Systems/
```

Then Cicero or Geoff can decide whether to promote the output into:

```text
obsidian/work/
obsidian/home/
obsidian/openclaw/
```

## Conflict Rules

1. The newest AI output is not automatically correct.
2. Canonical notes beat generated notes.
3. Source material beats summaries.
4. Calendar and email data should be treated as private source material.
5. Work, health, family, and travel context should not be exported broadly.
6. If two systems disagree, preserve both views in a review note and ask for resolution only when needed.
7. No system should delete or rewrite source material.

## Write Policy

External AI systems should write only to:

```text
<Relevant Obsidian Vault>/00 Cicero Inbox/AI Systems/<system-name>/
```

OpenClaw/Cicero can process those notes and promote durable material.

## Minimum Context Pack Template

```markdown
# Context Pack - <System / Use Case>

## Purpose

## Allowed Context

## Excluded Context

## Source Folders

## How To Use This

## Return Path

## Privacy Level

## Last Updated
```

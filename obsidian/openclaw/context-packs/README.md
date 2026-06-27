# Context Packs

Context packs are curated markdown bundles for feeding specific AI systems.

Each pack should be narrow enough to avoid leaking irrelevant private context and specific enough that the target AI can do useful work.

## Naming

```text
Context Pack - <System or Use Case>.md
```

Examples:

- `Context Pack - OpenClaw General.md`
- `Context Pack - PGNY Briefing Assistant.md`
- `Context Pack - Coding Agent.md`
- `Context Pack - Travel Assistant.md`

## Return Path

Outputs from other AI systems should be saved in:

```text
<Relevant Obsidian Vault>/00 Cicero Inbox/AI Systems/<system-name>/
```

Do not let an external AI write directly into canonical notes unless Geoff explicitly approves that workflow.

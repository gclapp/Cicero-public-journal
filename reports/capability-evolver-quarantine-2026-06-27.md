# Capability Evolver Removal Decision

Date: 2026-06-27  
Skill: `capability-evolver`  
Version: `1.32.2`  
Original path: `skills/capability-evolver`  
Former quarantine path: `quarantine/skills/capability-evolver-20260627T1449Z`

## Decision

Remove from the workspace instead of patching in place.

## Reason

The skill is a self-evolution engine with broad local and network reach. Its own metadata declares:

- `permissions: [network, shell]`
- external network endpoints including EvoMap, GitHub, and optional remote memory graph services
- environment variables for node secrets, GitHub tokens, and remote memory graph API keys
- read access to workspace memory
- write access to workspace memory and source paths
- shell commands including `git`, `node`, `npm`, process discovery commands, and disk checks
- rollback modes that include `git reset --hard`

OpenClaw's built-in deep audit also flagged it as critical because it contains multiple shell-exec patterns and environment/network patterns.

This may be a legitimate experimental self-improvement tool, but it is not a good fit for an always-on personal assistant host that stores credentials, personal memory, messaging integrations, and production-like automation.

## Actions Taken

First moved the entire skill directory out of the active `skills/` tree:

```bash
mv skills/capability-evolver quarantine/skills/capability-evolver-20260627T1449Z
```

Then removed the quarantined copy from the workspace:

```bash
gio trash quarantine/skills/capability-evolver-20260627T1449Z
```

The active workspace no longer contains the skill under `skills/` or `quarantine/`.

## Verification

- `openclaw skills list` no longer shows `capability-evolver`.
- `openclaw security audit --deep` no longer reports the capability-evolver critical finding.
- Deep audit now reports `0 critical · 4 warn · 1 info`.

## Functional Replacement

Removing this skill loses autonomous self-evolution: automated history scanning, mutation/promotion of skill code, EvoMap/A2A sharing, and continuous self-repair loops.

The safer replacement pattern for this host is human-reviewed improvement:

- `self-improvement` for recording mistakes and lessons.
- `skill-creator` and `skill_workshop` for proposed skill changes with review.
- `proactive-agent` for structured proactive behavior without self-modifying code.
- `lossless-claw` and `memory-core` for recall and continuity.
- `taskflow`/cron/Todoist for durable operational follow-through.

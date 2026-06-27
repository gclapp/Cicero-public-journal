---
name: "obsidian-sync-bridge"
description: "Operate Obsidian Sync vaults on OpenClaw via Obsidian Headless."
---

# Obsidian Sync Bridge

Use this skill when Geoff wants OpenClaw/Cicero to read or write his Obsidian vaults through Obsidian Sync/Cloud rather than a Git bridge.

## Model

Obsidian is the user interface. Obsidian Sync is the transport. The vault files are the data. OpenClaw should run Obsidian Headless to keep local copies synced under `/home/ubuntu/Obsidian/`.

```text
Geoff's Obsidian apps
  -> Obsidian Sync remote vaults
  -> Obsidian Headless on OpenClaw
  -> /home/ubuntu/Obsidian/<Vault Name>/
  -> Cicero reads/writes normal Markdown files
```

## Commands

Use the local wrapper from the OpenClaw workspace:

```bash
python3 scripts/obsidian_sync_bridge.py --help
python3 scripts/obsidian_sync_bridge.py login
python3 scripts/obsidian_sync_bridge.py remote
python3 scripts/obsidian_sync_bridge.py local
python3 scripts/obsidian_sync_bridge.py status "OpenAI Work"
python3 scripts/obsidian_sync_bridge.py sync "OpenAI Work"
python3 scripts/obsidian_sync_bridge.py sync "OpenAI Work" --continuous
```

Underlying tool:

```bash
ob
```

Install if missing:

```bash
npm install -g obsidian-headless
```

## Setup Procedure

1. Verify Node is at least v22:

```bash
node --version
```

2. Verify `ob` exists:

```bash
command -v ob
ob --help
```

3. Do not ask Geoff to paste Obsidian credentials into chat. Run login only in an interactive secure shell:

```bash
python3 scripts/obsidian_sync_bridge.py login
```

4. List remote vaults:

```bash
python3 scripts/obsidian_sync_bridge.py remote
```

5. Map remote vaults to local folders only after names are confirmed:

```bash
python3 scripts/obsidian_sync_bridge.py setup "<remote vault name>" "OpenAI Work"
python3 scripts/obsidian_sync_bridge.py setup "<remote vault name>" "OpenAI Home"
python3 scripts/obsidian_sync_bridge.py setup "<remote vault name>" "OpenClaw"
```

6. Check status and run a one-shot sync before enabling continuous sync:

```bash
python3 scripts/obsidian_sync_bridge.py status "OpenAI Work"
python3 scripts/obsidian_sync_bridge.py sync "OpenAI Work"
```

7. After successful one-shot sync, create systemd services for continuous sync. Do not mark setup complete until a file created from another device appears on OpenClaw and a harmless test note created by OpenClaw appears back in Obsidian.

## Safety Rules

- Prefer Obsidian Sync bridge over Git bridge for Geoff's active vaults.
- Do not create or require a second Git copy unless Obsidian Sync fails or Geoff asks for Git.
- Do not expose, paste, log, or store Obsidian passwords in notes or chat.
- Do not pass passwords with `--password` in command history. Let `ob` prompt interactively.
- Do not point sync at unrelated broad folders.
- Check remote vault names before `sync-setup`.
- Treat raw work calendar files, meeting notes, and personal notes as private source material.
- Preserve raw material. Do not delete sync conflicts without explicit approval.

## Canonical Local Paths

Work vault:

```text
/home/ubuntu/Obsidian/OpenAI Work/
```

Home vault:

```text
/home/ubuntu/Obsidian/OpenAI Home/
```

OpenClaw operating vault:

```text
/home/ubuntu/Obsidian/OpenClaw/
```

Work drop folder:

```text
/home/ubuntu/Obsidian/OpenAI Work/00 Cicero Inbox/
```

Work calendar exports:

```text
/home/ubuntu/Obsidian/OpenAI Work/00 Cicero Inbox/Calendar/Work/
```

Home drop folder:

```text
/home/ubuntu/Obsidian/OpenAI Home/00 Cicero Inbox/
```

## Completion Standard

A real integration is complete only after:

- `ob login` is done.
- Remote vaults are listed.
- Each intended vault is configured locally.
- One-shot sync succeeds.
- Continuous sync is supervised.
- A test file syncs device -> OpenClaw.
- A harmless test note syncs OpenClaw -> device.
- Daily memory records the result and any caveats.

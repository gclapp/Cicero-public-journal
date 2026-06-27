# OpenClaw Host Incident And Security Review

Date: 2026-06-27  
Host: ip-172-31-4-228  
Reviewer: Cicero

## Executive Summary

The June 27 downtime was not a classic in-guest kernel panic. The strongest evidence is two ACPI-style power events:

- 2026-06-27 14:31:38 UTC: `systemd-logind` logged `Power key pressed short` and `The system will power off now`.
- 2026-06-27 14:32:33 UTC: the same power-key shutdown pattern repeated on the short intermediate boot.

There was real memory pressure: during shutdown, `user-1000.slice` logged an OOM kill and `user@1000.service` showed a 3.4 GiB memory peak plus 1.7 GiB swap peak on a 3.8 GiB RAM host. Cron also reported a 1.6 GiB memory peak over the boot. The likely story is therefore:

1. DNS/network failures began before the shutdown and made agent/provider work unreliable.
2. The host was already running with tight memory headroom.
3. A host/control-plane power event rebooted the instance.
4. During shutdown, memory pressure caused at least one user-slice process to be OOM-killed.

Root cause confidence:

- High confidence: shutdown was initiated by host/control-plane power-key event, not a kernel panic.
- High confidence: memory headroom is too low for the current OpenClaw + Codex + cron workload.
- Medium confidence: DNS/network failure was an upstream/provider or host networking symptom rather than the primary cause.
- Low confidence: a single specific process caused the outage; the evidence points to cumulative pressure.

## Incident Timeline

- 2026-06-27 12:48-14:05 UTC: repeated model/provider failures, including OpenAI stream disconnects and Moonshot `EAI_AGAIN` DNS failures.
- 2026-06-27 13:32 UTC: Ubuntu Pro apt checks fail with `Temporary failure resolving 'esm.ubuntu.com'`.
- 2026-06-27 14:31:38 UTC: `Power key pressed short`; system begins poweroff.
- 2026-06-27 14:31:40 UTC: `cron.service` reports 2h 48m CPU and 1.6 GiB memory peak.
- 2026-06-27 14:31:44 UTC: `user@1000.service` reports 3.4 GiB memory peak and 1.7 GiB swap peak; `user-1000.slice` and `user.slice` report OOM-killed process.
- 2026-06-27 14:31:53 UTC: short boot starts on kernel `6.17.0-1017-aws`.
- 2026-06-27 14:32:33 UTC: second `Power key pressed short`; system powers off again.
- 2026-06-27 14:34:30 UTC: current boot starts on kernel `6.17.0-1017-aws`.

## Current Reliability Findings

- Instance class appears to be 4 GiB RAM class (`t4g.medium` from DMI).
- Swap is 2 GiB.
- OpenClaw gateway and child OpenClaw/Codex workers are the largest resident processes after reboot.
- Cron launches many `run_at_user_local_time.py` wrappers every 5 minutes. Most are lightweight, but the fan-out increases process churn and can create bad overlaps around daily check-in/report windows.
- Disk is not the incident cause; root disk was comfortably below alert thresholds in current checks.
- OpenClaw is not managed by a visible system `openclaw.service`; it is currently a user process under the OpenClaw gateway process tree.

## Monitoring Implemented

`scripts/system_health_check.py` now includes a host-level check that records:

- Available RAM and percentage.
- Swap usage.
- DNS resolution for `api.openai.com` and `github.com`.
- OpenClaw gateway process presence and RSS.
- Recent journal evidence for OOM, power-key shutdowns, DNS failures, and poweroff events.
- Top memory-consuming processes.

Verification:

- `python3 -m py_compile scripts/system_health_check.py` succeeded.
- Direct `check_host_health()` call succeeded and returned live memory/swap/DNS/OpenClaw status.

## Recommended Reliability Actions

Priority 0:

- Resize host from 4 GiB to 8 GiB RAM, or reduce OpenClaw/Codex worker concurrency. The current memory profile is too tight for reliable 24/7 operation.
- Keep at least 4 GiB swap on this class if hibernation/swap tooling supports it. Current swap is 2 GiB.

Priority 1:

- Consolidate cron local-time wrappers so one scheduler process evaluates local-time jobs instead of launching many wrappers every 5 minutes.
- Add `flock` to long-running jobs: competitor report, watch hunt, GitHub sync, token refresh, Whoop fetches, Aero, and Resy scans.
- Add explicit OpenClaw gateway restart/watchdog under systemd or a user systemd unit with `Restart=always`, `MemoryMax`, and journald retention.
- Add a reboot detector that notices a new boot ID and sends a concise alert.

Priority 2:

- Add CloudWatch or provider-side instance-status alerts for reboot/stop/start, CPU credits, memory via CloudWatch agent, and network status checks.
- Track DNS resolution as a first-class monitor. The incident had DNS failures before the reboot.
- Reduce noisy provider fallback loops when DNS is failing; fail fast and alert instead of trying every fallback provider repeatedly.

## OpenClaw Update Review

Installed:

- OpenClaw `2026.6.9` (`c645ec4`)

Available:

- npm `latest`: `2026.6.10`
- npm `beta`: `2026.6.11-beta.1`

Recommendation:

- Install stable `2026.6.10`, but do it after a backup and during a maintenance window.
- Do not install `2026.6.11-beta.1` on this host unless a specific beta fix is needed.

Reasoning:

- `2026.6.10` is a small stable release over `2026.6.9`.
- It improves session/channel state, cron delivery awareness, model routing, and trusted hook policy retention.
- Those changes are relevant to this host because it relies heavily on cron-delivered messages, messaging channels, Codex, and approval-sensitive tools.
- It does not appear to directly fix this host's memory pressure. Host resizing and cron cleanup remain necessary.

## OpenClaw Security Review

Built-in deep audit:

- 1 critical, 4 warnings, 1 info.

Critical:

- `skills/capability-evolver` contains multiple shell execution patterns and environment/network patterns. The audit labels this as critical. This skill is currently disabled, but the safest posture is to quarantine/remove it unless explicitly needed.

Warnings:

- `~/.openclaw` mode is `775`; should be `700`.
- `~/.openclaw/config` mode is `775`; should be `700`.
- `openclaw.json` contains plaintext secret-bearing fields: gateway auth token, gateway remote token, Telegram bot token. Migrate to OpenClaw SecretRefs.
- Plugin install metadata has conflicts for brave, codex, lossless-claw, voice-call, whatsapp.
- Plugin install specs are unpinned for codex and whatsapp; Brave metadata is missing integrity.

Positive findings:

- OpenClaw production npm audit found 0 vulnerabilities across production dependencies.
- Enabled OpenClaw plugins are limited: memory-core, moonshot, openai, telegram, brave, codex, lossless-claw, whatsapp.
- UFW allows only 22/80/443 inbound.
- Fail2ban and unattended-upgrades are active.
- OpenClaw gateway binds to loopback.

Concerns:

- CUPS listens on `0.0.0.0:631` and `[::]:631`. UFW blocks it externally, but it should be disabled or bound to loopback unless printing is needed.
- A gunicorn service listens on `0.0.0.0:5001`; UFW blocks it externally, but it should bind to loopback or be explicitly documented.
- Several credential-adjacent files under credentials/config are `664`. The most sensitive files are already `600`, but the rest should be tightened unless they are intentionally shareable.
- Docker is active. The current container is bound to loopback, which is acceptable.

## Patch/Upgrade Plan

Recommended sequence:

1. Backup current OpenClaw state:
   - `tar -czf ~/openclaw-backup-$(date +%Y%m%dT%H%M%SZ).tgz ~/.openclaw/openclaw.json ~/.openclaw/plugins ~/.openclaw/npm ~/.openclaw/agents/main ~/.openclaw/workspace/config ~/.openclaw/workspace/state`
2. Tighten permissions:
   - `chmod 700 ~/.openclaw ~/.openclaw/config`
   - review and set credential-adjacent files to `600`.
3. Quarantine/remove `skills/capability-evolver` unless Geoff explicitly wants it kept.
4. Migrate plaintext OpenClaw config secrets to SecretRefs.
5. Dry-run OpenClaw stable update:
   - `openclaw update --dry-run --channel stable`
6. Install OpenClaw `2026.6.10` in a maintenance window:
   - `openclaw update --channel stable`
7. Restart and verify:
   - `openclaw --version`
   - `openclaw doctor`
   - `openclaw security audit --deep`
   - direct WebChat message round trip
   - Telegram/WhatsApp delivery test if desired
   - `python3 scripts/system_health_check.py`
8. Apply Ubuntu package updates, prioritizing:
   - `nodejs`
   - `containerd`
   - `runc`
   - `apparmor`
   - `snapd`
   - `cloud-init`
   - `fwupd`
   - `rsyslog`
   - `nftables`

## Open Questions

- Whether `0.0.0.0:5001` is intentionally public behind nginx or should be loopback-only.
- Whether CUPS is needed on this host.
- Whether `capability-evolver` has trusted local provenance or should be removed immediately.
- Whether AWS instance resize is acceptable now, or whether the first move should be cron cleanup and swap expansion.

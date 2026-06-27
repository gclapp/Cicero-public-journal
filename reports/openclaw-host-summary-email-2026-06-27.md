# OpenClaw Host Incident, Update, and Security Review

Geoff,

Here is the concise version of the host incident and follow-up plan.

## What Happened

This was not a clean "the box ran out of memory and crashed" event.

The strongest evidence is that the host received ACPI-style power events at 2026-06-27 14:31:38 UTC and again at 14:32:33 UTC. That points to a host/control-plane poweroff/reboot rather than an in-guest kernel panic.

There was real memory pressure, though. During shutdown, the user slice logged an OOM kill, and `user@1000.service` showed about 3.4 GiB RAM peak plus 1.7 GiB swap peak on a 3.8 GiB RAM host. DNS/network failures began before the reboot and made provider/API workflows look broken.

My read: DNS/network trouble plus an external/ACPI reboot, with dangerously low memory headroom making the system fragile.

## Best Reliability Ideas

1. Resize the host from 4 GB to 8 GB RAM.
2. Increase swap from 2 GB to 4-8 GB.
3. Consolidate the many every-5-minute cron wrappers into one scheduler or stagger them.
4. Add `flock` around long jobs so duplicate runs cannot pile up.
5. Put OpenClaw gateway under an explicit systemd/user-systemd watchdog with restart and memory accounting.
6. Add reboot/boot-ID monitoring so we get a short alert after any unexpected restart.
7. Treat DNS as a first-class health check and suppress provider-specific retry storms when DNS is broken.
8. Add CloudWatch/provider-side instance alerts for reboot, status checks, CPU credits, memory, and network health.

## OpenClaw Update Recommendation

Installed: `2026.6.9`.

Latest stable: `2026.6.10`.

Recommendation: install `2026.6.10` during a maintenance window after backup. Do not install the current beta unless we need a specific beta fix.

The stable update improves session/channel state, cron delivery awareness, model routing, and trusted policy retention. It does not solve the RAM issue by itself.

## Security Findings

1. Critical: disabled `skills/capability-evolver` was flagged for shell-exec and env/network patterns. I recommend quarantining/removing it unless we explicitly trust and need it.
2. `~/.openclaw` and `~/.openclaw/config` are too permissive at `775`; tighten to `700`.
3. `openclaw.json` contains plaintext secret-bearing fields; migrate those to SecretRefs.
4. Plugin install metadata has conflicts, unpinned specs, and one missing integrity record.
5. CUPS and one gunicorn service listen on wildcard addresses. UFW blocks them externally, but they should be loopback-only unless intentionally exposed.

## Already Implemented

I added host health checks to `scripts/system_health_check.py`:

- RAM and swap thresholds
- DNS resolution checks
- OpenClaw gateway presence and RSS
- recent journal checks for OOM, DNS failures, power-key events, and poweroff
- top memory consumers

The full detailed report is attached.

- Cicero

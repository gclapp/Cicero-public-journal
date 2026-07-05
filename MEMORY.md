# MEMORY.md - Bootstrap Index

Purpose: keep only the highest-signal context in the always-loaded bootstrap. Detailed history now lives in daily/topic files under `memory/` and can be retrieved with `memory_search` / `memory_get` or lossless-claw recall.

Full pre-index archive: `memory/MEMORY-full-2026-06-23.md`.
Recent daily notes to keep hot: `memory/2026-06-23.md`, `memory/2026-06-22.md`.

## Identity
- Name: Cicero.
- Vibe: warm, sharp, quietly effective. Useful before theatrical.
- Default stance: verify before claiming done; preserve private data; report real errors quickly; do not make external/public actions without approval.
- Primary user: Geoffrey Clapp, Pacific time, CPO at Progyny.
- Core rule: always know UTC and Pacific time before scheduling, reminders, travel, or check-ins.

## Recall Protocol
- Use this file for current priorities and rules only.
- For exact old details, search memory first:
  - `memory_search` over `MEMORY.md` + `memory/*.md`.
  - `memory_get` for exact line excerpts.
  - For compacted conversation/session details, use lossless-claw tools: `lcm_grep` -> `lcm_expand_query` when exact commands, paths, timestamps, or root cause are needed.
- Do not guess exact historical facts from this index. Pull the source.

## Current High-Priority Personal Context

### Grace Birthday Trip 2026
- Dates: July 21-26, 2026.
- Destination: Truckee/Tahoe.
- Occasion: Grace's 30th birthday on July 22.
- Stay: two houses on Donner Lake via Airbnb.
- Flights: DL 4126 outbound, DL 3902 return.
- Car: rental pickup at Reno airport.
- Who: Geoff + Grace, no kids.
- Why it matters: milestone romantic trip; proactively track reservations, gift/surprise, weather, lodging, rental car, and activities.
- Open items: birthday dinner reservation for July 22, special activity/experience, gift/surprise, weather, lodging confirmations, car rental verification.
- Source details: `memory/MEMORY-full-2026-06-23.md` and June 17 notes.

### Progyny Executive Offsite
- Dates: July 12-13, 2026.
- Destination: Providence, RI via Atlanta.
- Purpose: Progyny executive team offsite.
- Outbound: DL 782 LAX -> ATL at 8:05 AM July 12; DL 2659 ATL -> PVD at 2:40 PM July 12.
- Confirmation: JMCGIZ.
- Treat as high-priority work travel.

### Family And Relationships
- Grace is Geoff's #1 priority after kids. Treat messages/emails involving Grace as high priority.
- Kids: Mackenzie, Oliver, Sophie.
- Normal Oliver/Sophie custody pattern: pick up Thursday 1:50 PM from Chaparral Elementary, drop off Saturday 5 PM with Stacey Borden.
- Stacey Borden: monitor for job/career changes if reasonably discoverable.
- Greta: Geoff's English Labrador. Needs Rover/dog sitter only when Geoff is leaving home, not when returning to LA/SoCal.

## Travel Rules
- Home airports: LAX, BUR, VNY, LGB, ONT. Any SoCal airport generally means home.
- Outbound from SoCal: create/check Rover, hotel/lodging at destination, pack, check-in, Uber to airport.
- Inbound to SoCal: no Rover, no hotel, create Uber from airport, check-in/pack as appropriate.
- Aero is the current travel system.
  - Main: `agents/travel-bot/aero_travel_manager.py`.
  - State: `state/aero-travel-state.json`.
  - Logs: `logs/aero-cron.log`, `logs/aero-monitor.log`.
  - Cron: task creation and 30-minute day-of-travel monitoring.

## Operating Rules Geoff Cares About

### Timezone
- Geoff's timezone: America/Los_Angeles.
- System time is UTC. Convert explicitly and state both when time-sensitive.
- Never guess relative dates. Use exact dates when clarifying.

### Error Handling
- If a system/action is failing, report it and try to fix it. No silent failures.
- Distinguish real failures from noisy monitors. Tune monitors rather than letting them cry wolf.
- Test before saying done. For code: compile/run/check output. For monitors: run manual check and wait for cron when appropriate.

### Integration Completion Standard
OAuth/auth setup alone is not complete. A real integration needs:
- Automated fetch/use path.
- Refresh token handling where applicable.
- Monitoring/alerting for stale or failed data.
- End-to-end test.
- Documentation in daily memory.

### External Actions
- Ask before sending emails, public posts, purchases, or actions that leave the machine unless already clearly authorized.
- Never delete Geoff's email.
- Never expose credentials or personal data in chat.

## Active Systems Index

### Calendar
- Google Calendar is active and central to proactive assistance.
- Token: `~/.openclaw/credentials/calendar-token.pickle`.
- Daily refresh before morning check-in.
- Calendar should drive travel tasks, dinner/restaurant prep, kids event ideas, and profile building.

### Check-Ins / Heartbeats
- Heartbeat/check-in instructions live in `HEARTBEAT.md`.
- Daily check-ins: morning 7 AM PT, evening 8 PM PT.
- Pending check-in delivery: `scripts/deliver_checkin.py`.
- Health check: `scripts/system_health_check.py`.
- On June 23, fixed false travel automation warning by teaching system health check to recognize Aero cron/logs.

### Telegram Health
- Monitor: `scripts/telegram_health_monitor.py`.
- State: `state/telegram-health-state.json`.
- Logs: `logs/telegram-health.log`, `logs/telegram-health-alerts.log`.
- June 22: fixed stale SQLite schema query and structured gateway log parsing.
- June 23: fixed false alert where normal message-cache text containing words like `error` or `failure` was counted as Telegram failure. Monitor now excludes normal cache namespaces and uses real error-ish state plus gateway errors.

### Model / API Health
- Primary model: `openai/gpt-5.5`.
- Fallback monitor: `scripts/model_fallback_monitor.py`, cron every 5 minutes, log `logs/model-monitor-cron.log`.
- June 23: removed invalid `audio` input capability from custom `gpt-5.5` and `gpt-5.4-mini` OpenAI definitions in `openclaw.json` and generated OpenAI catalog sidecar; doctor model catalog schema warning cleared.

### Token Health
- Token auto-refresh: `scripts/token_auto_refresh_v2.py`, every 30 minutes.
- Token health monitor: `scripts/token_health_monitor.py`, 9 AM and 9 PM PT.
- Whoop token monitor runs every 6 hours.
- Recovery reminders are in the archived full memory and TOOLS.md.

### Competitive Intelligence
- Monitor Progyny competitors: Maven, Carrot, KindBody, WIN Fertility; Maven/Kate Ryder is priority.
- Alerts: product launches, funding, partnerships, leadership changes, strategic moves.
- Reports should be professional HTML, source-linked, concise, and not raw URL dumps.
- Include Progyny comparison where relevant.

### Watch Hunt
- Dashboard: `https://gclapp.github.io/geoff-watch-hunt/`.
- Current focus: 1973 Rolex watches; gold or two-tone; 36mm+; sigma preferred; blue/black dials favored.
- Multi-site automation exists; see TOOLS.md for commands.

### Health / Vitus
- Health questions should delegate to Vitus where appropriate.
- Whoop is active; health dashboard exists.
- Preserve privacy around health data.

## Recent Operational Context - Keep Hot

### June 22-23, 2026: Model/API And Monitor Cleanup
- Geoff reported frequent model/API-looking errors.
- Root cause: stale auth/config plus gateway/Codex restarts and noisy monitors, not a broad OpenAI outage.
- OpenAI and Moonshot auth were repaired/verified.
- `openai/gpt-5.5` and fallback probes succeeded.
- June 23 cleanup removed invalid OpenAI model `audio` capability and added fallback monitor cron every 5 minutes.
- Verification at 11:40/11:45 UTC: primary model active.

### June 23, 2026: Orphan Transcript Cleanup
- Reviewed 37 orphan plain transcript JSONL files.
- No unique long-term facts needed rescue; one check-in design session already reflected in heartbeat scripts, WhatsApp/SMS reminder already in memory, rest were repeated cron/heartbeat/status transcripts.
- Archived recoverably: `/home/ubuntu/.openclaw/agents/main/sessions/orphan-transcripts-archive/20260623T115148Z`.
- Doctor no longer reports orphan transcript warning.
- Completed Todoist task: `Archive orphan OpenClaw transcripts and trim session storage`.

### June 23, 2026: Bootstrap Issue
- Old `MEMORY.md` was too large: about 31.8k chars, 65% truncated at bootstrap.
- `TOOLS.md` was about 19.2k chars, near 20k per-file limit.
- Total bootstrap raw was about 80.7k chars capped at 60k injected.
- Decision: keep `MEMORY.md` as this compact index, preserve full archive under `memory/MEMORY-full-2026-06-23.md`, and rely on memory/lossless recall for details.

### June 23, 2026: Telegram False Alert / Queue Lag
- Telegram alert at 11:35 UTC was false positive from scanning normal message text in SQLite cache.
- Patched Telegram health monitor and verified manual run: SQLite failures 0, log errors 0, total 0.
- Rapid Telegram messages were briefly processed out of order; outbound delivery itself was working.

## Important Memory Files And Where Details Live
- Full old long-term memory archive: `memory/MEMORY-full-2026-06-23.md`.
- Current daily context: `memory/2026-06-23.md`.
- Prior cleanup context: `memory/2026-06-22.md`.
- Todoist standards: `memory/TODOIST_STANDARDS.md`.
- Health/weight loss details: `memory/weight-loss-2026.md`, `memory/health-dashboard-2026.md`.
- Friend profiles: `memory/friend-profiles/`.
- Calendar/profile details: `memory/geoff-profile-calendar.md`.
- Operational commands and credentials notes: `TOOLS.md`.

## Better Memory System Direction
- Current best approach: compact bootstrap index + daily/topic memory files + lossless-claw for exact session recall.
- No new skill is required immediately. `lossless-claw` is already installed and is the right deep-recall layer.
- Good maintenance cadence:
  - Keep this file under 12k chars.
  - Keep `TOOLS.md` under 14k-16k chars by moving long setup docs into topic files.
  - During heartbeats, periodically promote durable facts from recent daily notes into this index or topic files.
  - Use `/lossless` or `/lcm` for LCM health; use `/lossless doctor` if summary health looks wrong.
- Alternatives if this grows again:
  - Raise OpenClaw bootstrap limits: fastest, but increases token cost and can still clip under large sessions.
  - More aggressive topic-file split: best long-term; keeps startup responsive.
  - Dedicated memory curator cron: useful, but only after this manual index pattern proves stable.

## Operating Standards

### Cron Job Flock Locking (MANDATORY DEFAULT)
**Rule:** All long-running cron jobs MUST use flock locking to prevent overlapping executions.

**What is flock locking?**
`flock` (file lock) is a Linux system call that provides advisory locking on files. When a script acquires a lock, any subsequent attempt to run the same script will either wait or exit gracefully instead of creating multiple overlapping instances. This prevents:
- Race conditions when the same job triggers before the previous run finishes
- Resource exhaustion from piled-up processes
- Data corruption from concurrent file/database writes
- Log spam from duplicate job output

**Implementation:**
- **Bash scripts:** Source `scripts/flock_utils.sh` and call `acquire_lock "script-name" || exit 0`
- **Python scripts:** Import `scripts/flock_utils.py` and use `with acquire_lock("script-name"):`
- Lock directory: `/tmp/openclaw-locks/`
- Lock files are automatically cleaned up on script exit

**Jobs now protected:**
- `daily-competitor-report-v3.sh` — Competitive intelligence
- `watch-hunt-cron.sh` — Watch hunt automation
- `aero_travel_cron.sh` / `aero_monitor_cron.sh` — Travel management
- `progyny-intel-cron.sh` — Progyny intelligence
- `weekly-security-audit.sh` — Security reports
- `daily-github-sync.sh` — Git synchronization
- `imap-check-cron.sh` — Email checking
- `disk-monitor.sh` — Disk monitoring
- `reddit-weekly-report.sh` — Reddit sentiment
- `token_auto_refresh_v2.py` — Token refresh
- `api_health_monitor.py` — API health checks
- `model_fallback_monitor.py` — Model fallback tracking
- `telegram_health_monitor.py` — Telegram health
- `whoop_alerts.py` / `whoop_daily_fetch.py` — Whoop data
- `heartbeat_sender.py` — Check-in emails
- `fetch_stock_data.py` — Stock data
- `calendar_reader.py` — Calendar sync
- `coach_engine.py` (Vitus) — Health coaching
- `loseit_integration.py` — Nutrition sync
- `whoop_token_monitor.py` — Token monitoring

**When creating new cron jobs:** Always add flock locking. Use the existing patterns in `scripts/flock_utils.sh` and `scripts/flock_utils.py`.

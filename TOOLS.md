# TOOLS.md - Bootstrap Tool Index

Purpose: keep active operational commands and system notes in bootstrap without loading long setup docs or secrets. Full redacted archive: `config/bootstrap-archives/TOOLS-full-2026-06-23.redacted.md`.

## Safety
- Never print, paste, or expose API keys/tokens/passwords.
- Credential paths are pointers only; read them only when needed for an internal operation.
- For external actions (email, public posts, purchases), ask first unless already explicitly authorized.

## Model And Monitor
- Primary model: `openai/gpt-5.5`.
- Main fallback: `openai/gpt-5.4-mini`; third-party fallback: Moonshot/Kimi.
- Fallback monitor: `scripts/model_fallback_monitor.py`.
- Cron: every 5 minutes, log `logs/model-monitor-cron.log`; state/history `logs/model-fallbacks.json`.
- Manual check:
```bash
python3 scripts/model_fallback_monitor.py "openai/gpt-5.5"
```
- Current June 23 status: custom OpenAI model definitions no longer include invalid `audio` input; model catalog warning cleared.

## Email
- Sender: `[REDACTED]`.
- Script: `scripts/send_email.py`.
- Config: `~/.openclaw/email_config.json`.
- Always send HTML for formatted reports.
```bash
python3 scripts/send_email.py --to "[REDACTED]" --subject "Subject" --body "<p>Body</p>" --html
python3 scripts/send_email.py --to "[REDACTED]" --cc "geoffrey.clapp@progyny.com" --subject "Subject" --body-file /path/to/body.html --html
```

## TTS
- Provider: ElevenLabs.
- Default voice: George (`JBFqnCBsd6RMkjVDRZzb`).
- Script: `scripts/elevenlabs_tts.py`.
```bash
python3 scripts/elevenlabs_tts.py "Text to narrate"
```

## GitHub
- GitHub user: `gclapp`.
- Git email: `[REDACTED]`.
- Prefer SSH. If HTTPS/PAT is needed, read token from a secure credential file; do not place tokens in bootstrap notes.
- Active repos to remember:
  - `Cicero-public-journal`.
  - `geoff-watch-hunt` / GitHub Pages: `https://gclapp.github.io/geoff-watch-hunt/`.
  - `health-dashboard` / GitHub Pages: `https://gclapp.github.io/health-dashboard/`.

## Memory And Bootstrap
- Session memory init: `scripts/session_memory_init.py`.
- Run at session start and verify `memory/YYYY-MM-DD.md` exists.
- Long-term bootstrap index: `MEMORY.md`.
- Full old long-term archive: `memory/MEMORY-full-2026-06-23.md`.
- Full old tools archive, redacted: `config/bootstrap-archives/TOOLS-full-2026-06-23.redacted.md`.
- Weekly consolidation: `scripts/weekly_memory_consolidation.py`, Sundays 11 PM PT.

## Heartbeat / Check-Ins
- Main instructions: `HEARTBEAT.md`.
- Queue check-ins: `scripts/heartbeat_sender.py`.
- Deliver pending check-ins: `scripts/deliver_checkin.py`.
- Mandatory system health: `scripts/system_health_check.py`.
- Logs: `logs/heartbeat.log`, `logs/checkin-delivery.log`.

## Cron Management
- System updates/restarts can wipe cron. Verify after updates.
```bash
bash scripts/cron-backup.sh backup
bash scripts/cron-backup.sh verify
bash scripts/cron-backup.sh restore
```
- Current critical crons include heartbeat, watch hunt, calendar refresh, IMAP, competitor report, security audit, Reddit report, weekly email, stock tracker, token health, Whoop refresh/monitor, Vitus briefings, model fallback monitor, Aero travel.

## Calendar / Travel
- Calendar refresh: `scripts/calendar_reader.py`, daily before morning check-in.
- Cached events: `config/calendar-events.json`.
- Aero travel manager: `agents/travel-bot/aero_travel_manager.py`.
- Aero logs: `logs/aero-cron.log`, `logs/aero-monitor.log`.
- Aero state: `state/aero-travel-state.json`.
```bash
python3 agents/travel-bot/aero_travel_manager.py tasks
python3 agents/travel-bot/aero_travel_manager.py monitor
python3 agents/travel-bot/aero_travel_manager.py full
python3 agents/travel-bot/aero_travel_manager.py test
```

## Watch Hunt
- Dashboard: `https://gclapp.github.io/geoff-watch-hunt/`.
- Repo: `https://github.com/gclapp/geoff-watch-hunt`.
- Manual run:
```bash
source ~/.openclaw/venvs/scrapling/bin/activate
python3 scripts/watch_search_multi.py
bash scripts/watch-hunt-cron.sh
```
- Logs: `logs/watch-hunt.log`.
- Search manager:
```bash
python3 scripts/search_manager.py list
python3 scripts/search_manager.py toggle <search_id>
python3 scripts/search_manager.py complete <search_id>
python3 scripts/search_manager.py delete <search_id>
```

## Health / Weight / Whoop
- Health dashboard: `https://gclapp.github.io/health-dashboard/`.
- Weight loss tracker: `memory/weight-loss-2026.md`.
- Health dashboard memory: `memory/health-dashboard-2026.md`.
- Delegate health-specific analysis to Vitus.
- Vitus spawn helpers: `scripts/spawn_health_agent.py`, `scripts/spawn_vitus.py`.
- Whoop/token logs: `logs/whoop-*.log`, `logs/token-refresh.log`, `logs/token-alert-state.json`.

## Stocks
- Script: `scripts/fetch_stock_data.py`.
- Current data: `data/stock-data.json`.
- History: `data/stock-history.json`.
- Schedule: daily 6 PM PT.
- Tracked: PGNY, AAPL, NVDA, OMDA, plus market indices.
```bash
python3 scripts/fetch_stock_data.py
python3 -c "from scripts.fetch_stock_data import get_stock_summary; print(get_stock_summary())"
```

## Competitive Intelligence
- Main cron/report script: `scripts/daily-competitor-report-v3.sh`.
- Logs: `logs/competitor-v3-cron.log`, `logs/competitor-v3.log`, `logs/progyny-intel.log`.
- Key competitors: Maven, Carrot, KindBody, WIN Fertility; Maven/Kate Ryder priority.
- Send CEO-ready HTML with citations and embedded hyperlinks, not raw URL dumps.

## Script Archive Policy
- Active scripts stay in `scripts/` only if called by cron, active scripts, or regular manual ops.
- Old/experimental versions belong in `scripts/archive/` with README updates.
- Never execute archived scripts without review; use them only as references.

## Skill Status
- Ready: voice-call, email, blogwatcher (needs feeds), weather, whoop, SAG/TTS, opentable (needs API credentials to activate).
- Future/research: Delta, Marriott, Beli, deeper calendar travel/hotel detection.
- Memory/recall: `lossless-claw` is already installed; no new memory skill needed immediately.

## Planned / Lower-Priority Programs
- Python learning plan: `python-learning-plan.md`, tracker `memory/python-learning-2026.md`.
- Private infrastructure plan: `private-infrastructure-plan.md`.
- Details moved out of bootstrap; search memory/files when needed.

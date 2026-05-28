# Aero Travel Manager v2.0

**The complete travel automation system for Geoff.**

---

## What is Aero?

Aero is your travel concierge. It handles everything from detecting trips in your calendar to alerting you about gate changes on the day of travel.

### Before Aero
- Manual task creation for each trip
- Checking flight status manually
- Missing gate changes
- Duplicate tasks
- No proactive alerts

### With Aero
- Automatic trip detection from calendar
- Smart task creation (no duplicates)
- Real-time flight monitoring
- Instant alerts for gate changes, delays, cancellations
- Validated flight information

---

## Quick Start

### 1. Set up FlightAware API

```bash
# Get API key from https://flightaware.com/commercial/aeroapi/
# Then run:
python3 agents/travel-bot/aero_travel_manager.py setup YOUR_API_KEY
```

### 2. Run the migration

```bash
bash scripts/migrate-to-aero.sh
```

### 3. Test it

```bash
# Test API connection
python3 agents/travel-bot/aero_travel_manager.py test

# Create tasks for upcoming trips
python3 agents/travel-bot/aero_travel_manager.py tasks

# Monitor flights today
python3 agents/travel-bot/aero_travel_manager.py monitor
```

---

## How It Works

### Smart Task Creation

Aero scans your calendar and creates tasks only for trips that don't already have tasks:

```
Tasks for NYC Trip on Jun 15 - DL123 ABC123
├── 🧳 Pack (due Jun 14)
├── 🏢 Contact Marriott Ambassador (due Jun 8)
├── 🐕 Schedule Rover for Greta (due today)
├── 🚗 Schedule Uber TO airport for DL123 to NYC (due Jun 12)
└── 🚗 Schedule Uber FROM airport for DL456 from NYC (due Jun 18)
```

**Smart duplicate detection:**
- Tracks processed trips in state file
- Checks Todoist for existing tasks
- Fuzzy matching for similar trips
- Never creates the same task twice

### Day-of-Travel Monitoring

Every 30 minutes, Aero checks flights departing today/tomorrow:

- **Gate assignments** — Alerts when gate is assigned or changed
- **Terminal changes** — Notifies if terminal changes
- **Delays** — Alerts for delays 15+ minutes
- **Cancellations** — Immediate critical alert
- **Status changes** — Any change in flight status

**Alert channels:**
- Email (detailed HTML)
- Telegram (instant push)

### Flight Validation

Before trusting flight information, Aero validates it:

```bash
python3 agents/travel-bot/aero_travel_manager.py validate DL123 2026-06-15
```

**Sources checked:**
1. FlightAware API (real-time status)
2. Calendar cross-reference
3. Schedule search

**Confidence scoring:**
- 80%+ = CONFIRMED
- 50-79% = LIKELY
- <50% = UNVERIFIED

---

## Commands

| Command | Description |
|---------|-------------|
| `tasks` | Create travel tasks for upcoming trips |
| `monitor` | Monitor flights today/tomorrow for changes |
| `full` | Run both tasks + monitoring |
| `validate <flight> <date>` | Validate flight information |
| `test` | Test FlightAware API connection |
| `setup <api_key>` | Configure FlightAware API key |

---

## Cron Schedule

| Job | Schedule | Purpose |
|-----|----------|---------|
| Task Creation | Mon/Wed/Fri 4 PM PT | Create tasks for upcoming trips |
| Monitoring | Every 30 minutes | Check for flight changes |
| Full Run | Daily 6 AM PT | Comprehensive check |

---

## File Locations

| File | Path |
|------|------|
| Main script | `agents/travel-bot/aero_travel_manager.py` |
| Config | `agents/travel-bot/config.json` |
| State | `~/.openclaw/workspace/state/aero-travel-state.json` |
| Flight tracking | `~/.openclaw/workspace/state/aero-tracked-flights.json` |
| Logs | `~/.openclaw/workspace/logs/aero-cron.log` |

---

## Rover Logic

Aero is smart about Greta:

- **Creates Rover task** for outbound flights FROM LAX/Burbank (you're leaving home)
- **No Rover task** for inbound flights TO LAX/Burbank (you're coming home)

This prevents unnecessary Rover bookings when you're returning.

---

## Testing & Validation

### How Flight Information is Tested

1. **API Connection Test**
   ```bash
   python3 agents/travel-bot/aero_travel_manager.py test
   ```
   Verifies FlightAware API credentials and connectivity.

2. **Flight Validation**
   ```bash
   python3 agents/travel-bot/aero_travel_manager.py validate DL123 2026-06-15
   ```
   Cross-references multiple sources for confidence scoring.

3. **Live Monitoring Test**
   ```bash
   python3 agents/travel-bot/aero_travel_manager.py monitor
   ```
   Checks today's flights and reports status.

### Validation Sources

| Source | Weight | Data |
|--------|--------|------|
| FlightAware API | 50% | Real-time status, gates, delays |
| Calendar | 30% | Confirms flight is in your schedule |
| Schedule Search | 20% | Validates route exists |

---

## Troubleshooting

### "FlightAware not configured"

Run setup:
```bash
python3 agents/travel-bot/aero_travel_manager.py setup YOUR_API_KEY
```

### Duplicate tasks being created

Check state file:
```bash
cat ~/.openclaw/workspace/state/aero-travel-state.json
```

Clear if needed:
```bash
rm ~/.openclaw/workspace/state/aero-travel-state.json
```

### No alerts for gate changes

Check monitoring is running:
```bash
tail -f ~/.openclaw/workspace/logs/aero-cron.log
```

Verify crontab:
```bash
crontab -l | grep aero
```

---

## Migration from Old System

### What Changed

| Old | New |
|-----|-----|
| `scripts/calendar_travel_checker.py` | `agents/travel-bot/aero_travel_manager.py tasks` |
| `scripts/travel_flight_monitor.py` | `agents/travel-bot/aero_travel_manager.py monitor` |
| `scripts/flight_alert_system.py` | Integrated into monitoring |
| Multiple scripts | Single unified script |
| Basic duplicate check | Smart multi-layer detection |
| No validation | Multi-source validation |

### To Migrate

```bash
bash scripts/migrate-to-aero.sh
```

This will:
1. Backup your crontab
2. Remove old travel jobs
3. Add new Aero jobs
4. Test the installation

---

## Support

For issues or questions, check:
- Logs: `~/.openclaw/workspace/logs/aero-cron.log`
- State: `~/.openclaw/workspace/state/aero-travel-state.json`
- Documentation: `agents/travel-bot/AGENTS.md`

---

**Version:** 2.0  
**Maintained by:** Cicero  
**Last updated:** 2026-05-28

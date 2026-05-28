# Aero Travel Manager — Overview

**Last Updated:** May 28, 2026  
**Version:** 2.0  
**Status:** ✅ Active & Operational

---

## What Aero Does

Aero is your complete travel concierge. Once configured, it runs automatically to handle everything from trip planning to day-of-travel intelligence.

---

## 1. Smart Task Creation

**When:** Monday, Wednesday, Friday at 4:00 PM PT  
**What it does:** Scans your calendar and creates tasks for upcoming trips

### Task Structure
```
Tasks for [Destination] Trip on [Date] - [Flight#] [Confirmation]
├── 🧳 Pack (due day before departure)
├── 🏢 Contact Marriott Ambassador (due 7 days before)
├── 🐕 Schedule Rover for Greta (only outbound from LAX/Burbank)
├── 🚗 Schedule Uber TO airport for [Flight] to [Destination] (due 3 days before)
└── 🚗 Schedule Uber FROM airport for [Flight] from [Destination] (due 3 days before)
```

### Smart Duplicate Detection
Aero never creates duplicate tasks. It checks:
1. **State file** — Tracks processed trips in `aero-travel-state.json`
2. **Todoist** — Queries existing tasks (including completed)
3. **Fuzzy matching** — Detects similar trips and Uber tasks

### Rover Logic (Smart)
- **Creates Rover task** for outbound flights FROM LAX/Burbank (you're leaving home)
- **No Rover task** for inbound flights TO LAX/Burbank (you're coming home)

---

## 2. Day-of-Travel Monitoring

**When:** Every 30 minutes  
**Scope:** Flights departing today and tomorrow  
**Data Source:** FlightAware AeroAPI v4

### What It Monitors
| Change | Alert Trigger |
|--------|---------------|
| Gate assignment | When gate is first assigned |
| Gate change | Any departure gate change |
| Terminal change | Any terminal change |
| Arrival gate | Assignment and changes |
| Delays | 15+ minutes |
| Cancellations | Immediate critical alert |
| Status changes | Any flight status update |

### Alert Channels
- **Email:** Detailed HTML to [REDACTED]
- **Telegram:** Instant push notification

### Example Alert
```
✈️ DL979 Alert

LAX → JFK
Status: DELAYED

Changes:
• ⏰ DELAY ALERT: Flight delayed by 45 minutes
• 🔄 GATE CHANGE: Departure gate changed from 42B to 45A

Current Info:
Gate: 45A
Terminal: 4
Aircraft: Boeing 767-300
Delay: 45 minutes

Checked at: 2026-06-21 08:30 UTC
```

---

## 3. Flight Validation

**Command:** `python3 aero_travel_manager.py validate <flight> <date>`

### Multi-Source Validation
| Source | Weight | Data Provided |
|--------|--------|---------------|
| **FlightAware API** | 50% | Real-time status, gates, delays, aircraft type |
| **Calendar Cross-Reference** | 30% | Confirms flight is in your schedule |
| **Schedule Search** | 20% | Validates route exists in published schedules |

### Confidence Scoring
- **80%+ CONFIRMED** — Reliable for critical decisions
- **50-79% LIKELY** — Use with minor verification
- **<50% UNVERIFIED** — Manual check recommended

---

## 4. What You Don't Have To Do

✅ No manual flight checking  
✅ No wondering which gate to go to  
✅ No surprise delays  
✅ No duplicate task creation  
✅ No missing Rover bookings  
✅ No forgotten Uber scheduling

**Bottom line:** Show up at the airport with the right gate info. Aero handles the rest.

---

## Commands

```bash
# Setup FlightAware API
python3 agents/travel-bot/aero_travel_manager.py setup <api_key>

# Create travel tasks
python3 agents/travel-bot/aero_travel_manager.py tasks

# Monitor flights today/tomorrow
python3 agents/travel-bot/aero_travel_manager.py monitor

# Full run (tasks + monitoring)
python3 agents/travel-bot/aero_travel_manager.py full

# Validate specific flight
python3 agents/travel-bot/aero_travel_manager.py validate DL979 2026-06-21

# Test API connection
python3 agents/travel-bot/aero_travel_manager.py test
```

---

## Cron Schedule

| Job | Frequency | Purpose |
|-----|-----------|---------|
| Task Creation | Mon/Wed/Fri 4 PM PT | Create tasks for upcoming trips |
| Monitoring | Every 30 minutes | Check for flight changes |
| Full Run | Daily 6 AM PT | Comprehensive check |

---

## Configuration

### FlightAware API
- **Portal:** https://www.flightaware.com/aeroapi/portal
- **Config File:** `agents/travel-bot/config.json`
- **Rate Limit:** 100 requests/minute

### Geoff's Preferences (in config.json)
```json
{
  "home_airports": ["LAX", "BUR", "VNY", "LGB", "ONT"],
  "preferred_airlines": ["Delta", "American", "Alaska"],
  "seat_preference": "aisle",
  "loyalty_programs": {
    "delta": "SkyMiles",
    "marriott": "Bonvoy"
  }
}
```

---

## State Files

| File | Location | Purpose |
|------|----------|---------|
| `aero-travel-state.json` | `~/.openclaw/workspace/state/` | Tracks processed trips and tasks |
| `aero-tracked-flights.json` | `~/.openclaw/workspace/state/` | Last known flight status for change detection |
| `aero-cron.log` | `~/.openclaw/workspace/logs/` | Cron execution logs |

---

## File Structure

```
agents/travel-bot/
├── SOUL.md                 # Identity and personality
├── AGENTS.md              # Technical documentation
├── README.md              # User guide
├── AERO_OVERVIEW.md       # This file — high-level overview
├── aero_travel_manager.py # Main orchestrator
├── config.json            # API keys and preferences
├── aero-cron-tasks.sh     # Task creation cron wrapper
├── aero-cron-monitor.sh   # Monitoring cron wrapper
├── aero-cron-full.sh      # Full run cron wrapper
└── memory/                # Travel history
    ├── trips/
    ├── preferences.json
    └── patterns.json
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | May 28, 2026 | Migrated from legacy scripts, added FlightAware integration, smart duplicate detection, validation system |
| 1.0 | May 2026 | Initial creation — Basic flight monitoring, travel briefings |

---

## Enhancement Ideas (Future)

- [ ] Weather integration (origin/destination forecasts)
- [ ] Lounge access reminders
- [ ] Upgrade opportunity alerts
- [ ] Connection risk assessment
- [ ] Ground transport coordination (Uber/Lyft API)
- [ ] Hotel check-in reminders
- [ ] TSA wait time estimates
- [ ] Alternative flight suggestions on delays
- [ ] Calendar auto-update on flight changes
- [ ] Family coordination (custody schedule awareness)

---

**Maintained by:** Cicero  
**Questions?** Check `agents/travel-bot/AGENTS.md` for technical details

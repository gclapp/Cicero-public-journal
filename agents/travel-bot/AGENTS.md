# AGENTS.md — Aero: The Travel Concierge

**Agent ID:** `travel-bot`  
**Name:** Aero  
**Purpose:** Complete travel automation — from trip detection to day-of-travel intelligence  
**Version:** 2.0

---

## Overview

Aero is your travel partner. Not just a flight tracker — a complete travel concierge that:

1. **Detects trips** from your calendar automatically
2. **Creates smart tasks** (pack, Uber, Rover, Marriott) with duplicate detection
3. **Monitors flights** in real-time via FlightAware
4. **Alerts on changes** — gate changes, delays, cancellations
5. **Provides travel briefings** with actionable intelligence

---

## Capabilities

### 1. Smart Task Creation (`aero_travel_manager.py tasks`)

**What it does:**
- Scans calendar for flights, hotels, and travel events
- Groups flights into logical trips
- Creates one parent task per trip with subtasks:
  - 🧳 Pack (due day before)
  - 🏢 Contact Marriott Ambassador (due 7 days before)
  - 🐕 Schedule Rover for Greta (only for outbound flights from LAX/Burbank)
  - 🚗 Schedule Uber to/from airport for each flight leg (due 3 days before)

**Smart Duplicate Detection:**
- Checks state file (`aero-travel-state.json`) for processed trips
- Queries Todoist for existing tasks (including completed)
- Fuzzy matching for similar trips and Uber tasks
- Never creates duplicate tasks

**Schedule:** Monday, Wednesday, Friday at 4:00 PM PT

### 2. Day-of-Travel Monitoring (`aero_travel_manager.py monitor`)

**What it does:**
- Monitors flights departing today and tomorrow
- Fetches real-time status from FlightAware
- Detects changes:
  - Gate assignments and changes
  - Terminal changes
  - Delays (15+ minutes)
  - Flight cancellations
  - Status changes

**Alerts sent via:**
- Email (HTML formatted)
- Telegram (instant push)

**Schedule:** Every 30 minutes

### 3. Flight Validation (`aero_travel_manager.py validate <flight> <date>`)

**What it does:**
- Validates flight information across multiple sources
- Confidence scoring:
  - 80%+ = CONFIRMED
  - 50-79% = LIKELY
  - <50% = UNVERIFIED
- Sources: FlightAware API, Calendar cross-reference, Schedule search

### 4. Connection Testing (`aero_travel_manager.py test`)

Tests FlightAware API connectivity and credentials.

---

## File Structure

```
agents/travel-bot/
├── SOUL.md                    # Identity, personality, philosophy
├── AGENTS.md                  # This file — technical documentation
├── aero_travel_manager.py     # Main orchestrator (all commands)
├── flight_monitor.py          # FlightAware client (legacy, integrated)
├── config.json                # API keys and preferences
├── aero-cron-tasks.sh         # Cron wrapper: task creation
├── aero-cron-monitor.sh       # Cron wrapper: day-of-travel monitoring
├── aero-cron-full.sh          # Cron wrapper: full run
└── memory/                    # Travel history & state
    ├── trips/                 # Past trip records
    ├── preferences.json       # Geoff's travel preferences
    └── patterns.json          # Learned travel patterns
```

---

## State Files

| File | Location | Purpose |
|------|----------|---------|
| `aero-travel-state.json` | `~/.openclaw/workspace/state/` | Tracks processed trips and tasks |
| `aero-tracked-flights.json` | `~/.openclaw/workspace/state/` | Last known flight status for change detection |
| `aero-cron.log` | `~/.openclaw/workspace/logs/` | Cron execution logs |

---

## Cron Jobs

Add these to crontab:

```bash
# Aero: Create travel tasks (Mon/Wed/Fri at 4 PM PT)
0 16 * * 1,3,5 /home/ubuntu/.openclaw/workspace/agents/travel-bot/aero-cron-tasks.sh

# Aero: Day-of-travel monitoring (every 30 minutes)
*/30 * * * * /home/ubuntu/.openclaw/workspace/agents/travel-bot/aero-cron-monitor.sh

# Aero: Full run (daily at 6 AM PT)
0 6 * * * /home/ubuntu/.openclaw/workspace/agents/travel-bot/aero-cron-full.sh
```

---

## Configuration

### FlightAware API Setup

1. Get API key from [FlightAware](https://flightaware.com/commercial/aeroapi/)
2. Run setup:
   ```bash
   python3 agents/travel-bot/aero_travel_manager.py setup YOUR_API_KEY
   ```

Or manually edit `config.json`:
```json
{
  "flightaware": {
    "api_key": "your_api_key_here",
    "base_url": "https://aeroapi.flightaware.com/aeroapi"
  }
}
```

### Geoff's Preferences (in config.json)

```json
{
  "geoff_preferences": {
    "home_airports": ["LAX", "BUR", "VNY", "LGB", "ONT"],
    "preferred_airlines": ["Delta", "American", "Alaska"],
    "seat_preference": "aisle",
    "loyalty_programs": {
      "delta": "SkyMiles",
      "marriott": "Bonvoy"
    }
  }
}
```

---

## Usage

### Manual Commands

```bash
# Create travel tasks only
python3 agents/travel-bot/aero_travel_manager.py tasks

# Monitor flights today/tomorrow only
python3 agents/travel-bot/aero_travel_manager.py monitor

# Full run (tasks + monitoring)
python3 agents/travel-bot/aero_travel_manager.py full

# Validate a specific flight
python3 agents/travel-bot/aero_travel_manager.py validate DL123 2026-06-15

# Test FlightAware connection
python3 agents/travel-bot/aero_travel_manager.py test
```

### From Main Agent (Cicero)

```python
# Spawn Aero for a specific trip
sessions_spawn(
    task="Monitor Geoff's flight DL123 from LAX to JFK on June 15",
    agentId="travel-bot",
    taskName="flight_monitor_dl123"
)

# Or run via subprocess for immediate execution
subprocess.run([
    "python3", "agents/travel-bot/aero_travel_manager.py",
    "validate", "DL123", "2026-06-15"
])
```

---

## Migration from Old System

### What Was Migrated

| Old Script | New Location | Notes |
|------------|--------------|-------|
| `scripts/calendar_travel_checker.py` | Integrated into `aero_travel_manager.py` | Enhanced with FlightAware |
| `scripts/travel_flight_monitor.py` | Integrated into `aero_travel_manager.py` | Enhanced with change detection |
| `scripts/flight_alert_system.py` | Integrated into `aero_travel_manager.py` | Enhanced with email + Telegram |
| `scripts/flight_monitor.py` | Integrated into `aero_travel_manager.py` | Unified monitoring |

### Key Improvements

1. **Unified codebase** — One script handles everything
2. **Better duplicate detection** — State + Todoist + fuzzy matching
3. **Real-time monitoring** — FlightAware API for live data
4. **Smarter alerts** — Only alerts on actual changes
5. **Validation** — Multi-source flight verification
6. **Rover logic** — Only creates Rover tasks for outbound flights from home

---

## Testing & Validation

### How Flight Information is Validated

1. **FlightAware API (Primary)**
   - Real-time flight status
   - Official airline data
   - Gate assignments, delays, cancellations
   - 50% confidence weight

2. **Calendar Cross-Reference**
   - Validates flight exists in Geoff's calendar
   - Confirms date/time alignment
   - 30% confidence weight

3. **Schedule Search (Secondary)**
   - Confirms flight is in published schedule
   - Validates route exists
   - 20% confidence weight

**Confidence Thresholds:**
- 80%+ = CONFIRMED (use for critical decisions)
- 50-79% = LIKELY (use with minor verification)
- <50% = UNVERIFIED (manual check recommended)

### Testing Commands

```bash
# Test API connection
python3 agents/travel-bot/aero_travel_manager.py test

# Validate a flight
python3 agents/travel-bot/aero_travel_manager.py validate DL4099 2026-06-15

# Check logs
tail -f ~/.openclaw/workspace/logs/aero-cron.log

# Check state
cat ~/.openclaw/workspace/state/aero-travel-state.json
```

---

## Alert Priorities

| Priority | Trigger | Channels | Immediate |
|----------|---------|----------|-----------|
| 🔴 CRITICAL | Flight cancelled, >2hr delay, missed connection | Email + Telegram | Yes |
| 🟡 WARNING | Gate change, 15-120min delay, weather advisory | Email + Telegram | No |
| 🟢 INFO | Minor delay, on-time, lounge reminder | Briefing only | No |

---

## Integration with Cicero

Aero reports to Cicero (main agent) via:
- State files (shared data)
- Email alerts (for critical issues)
- Telegram (for immediate notifications)

Cicero can spawn Aero for:
- Specific flight monitoring
- Travel briefing generation
- Emergency rebooking assistance

---

## Success Metrics

- Zero missed connections due to late alerts
- No duplicate tasks created
- Proactive rebooking before Geoff asks
- Accurate gate/terminal information
- Stress-free travel experience

---

## Version History

- **2.0 (Current):** Migrated from legacy scripts, added FlightAware integration, smart duplicate detection, validation system
- **1.0:** Initial creation — Basic flight monitoring, travel briefings

---

**Maintained by:** Cicero (main agent)  
**Last updated:** 2026-05-28

# Aero Travel Automation

Comprehensive day-of-travel monitoring and automation system using FlightAware API.

## Overview

Aero Travel Automation is a unified system that handles all travel-related tasks:

1. **Calendar Scanning** - Detects flights from Google Calendar
2. **Task Creation** - Creates Todoist tasks (pack, uber, rover, marriott)
3. **Flight Monitoring** - Real-time tracking via FlightAware API
4. **Smart Alerts** - Telegram, Email, and Voice notifications

## Features

### Day-of-Travel Monitoring

- ✅ **Active Flight Tracking** - Monitors flights within 48 hours of departure
- ✅ **Gate Information** - Tracks gate assignments and changes
- ✅ **Real-time Alerts** for:
  - Gate changes
  - Terminal changes
  - Departure/arrival time changes
  - Delays (15+ minutes)
  - Cancellations
  - Status changes

### Alert Delivery Methods

| Severity | Telegram | Email | Voice Call |
|----------|----------|-------|------------|
| Info (ℹ️) | ❌ | ✅ | ❌ |
| Warning (⚠️) | ✅ | ✅ | ❌ |
| Critical (🚨) | ✅ | ✅ | ✅ |

### Alert Types

- **Gate Change** - When gate assignment changes
- **Terminal Change** - When terminal changes
- **Status Change** - When flight status changes (scheduled → delayed, etc.)
- **Delay Alert** - When delay exceeds 15 minutes
- **Departure Change** - When departure time changes significantly
- **Arrival Change** - When arrival time changes

## Installation

### Prerequisites

- Python 3.8+
- FlightAware AeroAPI key (stored at `~/.openclaw/credentials/flightaware.json`)
- Todoist CLI configured
- Telegram bot (for alerts)

### Setup

1. **Install cron jobs:**
```bash
cd /home/ubuntu/.openclaw/workspace/aero
bash scripts/setup_cron.sh
```

2. **Verify installation:**
```bash
crontab -l | grep -A 20 "Aero Travel"
```

3. **Test manually:**
```bash
# Test full automation
bash scripts/aero_travel_cron.sh full

# Test flight monitoring
bash scripts/aero_travel_cron.sh monitor

# Check status
bash scripts/aero_travel_cron.sh status
```

## Cron Schedule

| Job | Frequency | Time (PT) | Purpose |
|-----|-----------|-----------|---------|
| Full Automation | Twice daily | 9 AM, 9 PM | Task creation + monitoring |
| Regular Monitor | Every 30 min | All day | Standard flight checks |
| Frequent Monitor | Every 5 min | All day | Intensive checks on travel day |

## Usage

### Command Line

```bash
# Run from aero directory
cd /home/ubuntu/.openclaw/workspace/aero

# Full automation (tasks + monitoring)
python3 -m src.aero_travel_automation full

# Task creation only
python3 -m src.aero_travel_automation tasks

# Flight monitoring only
python3 -m src.aero_travel_automation monitor

# Check monitoring status
python3 -m src.aero_travel_automation status
```

### Python API

```python
from aero_travel_automation import AeroTravelAutomation

# Initialize
automation = AeroTravelAutomation()

# Run full automation
results = automation.run_full_automation()

# Or run individual components
task_results = automation.run_task_creation()
monitor_results = automation.run_flight_monitoring("regular")

# Get status
print(automation.monitor.get_status_summary())

# Clean up
automation.close()
```

## File Structure

```
aero/
├── src/
│   ├── flightaware_client.py      # FlightAware API client
│   ├── aero_tracker.py            # Main tracking system
│   ├── travel_monitor.py          # Day-of-travel monitoring
│   └── aero_travel_automation.py  # Unified automation
├── scripts/
│   ├── aero_travel_cron.sh        # Main cron wrapper
│   ├── aero_travel_monitor.sh     # Monitor-only wrapper
│   └── setup_cron.sh              # Cron setup script
├── docs/
│   ├── API_SETUP.md               # FlightAware API setup
│   ├── USAGE.md                   # General usage guide
│   └── TRAVEL_AUTOMATION.md       # This file
└── README.md
```

## State Files

| File | Purpose |
|------|---------|
| `~/.openclaw/workspace/state/aero-travel-automation.json` | Processed trips, created tasks |
| `~/.openclaw/workspace/state/aero-travel-monitor.json` | Monitored flights, alert history |

## Log Files

| File | Purpose |
|------|---------|
| `~/.openclaw/workspace/logs/aero-travel-YYYYMMDD.log` | Daily travel logs |
| `~/.openclaw/workspace/logs/aero-cron.log` | Cron execution logs |

## Migration from Cicero

This system replaces the following Cicero scripts:

| Old Script | New Component |
|------------|---------------|
| `calendar_travel_checker.py` | `aero_travel_automation.py` (tasks) |
| `travel_flight_monitor.py` | `travel_monitor.py` |
| `flight_alert_system.py` | `travel_monitor.py` (alerts) |
| `flight_monitor.py` | `travel_monitor.py` |

## Configuration

### Environment Variables

```bash
# Optional: Override default paths
export AERO_CALENDAR_FILE=/path/to/calendar.json
export AERO_STATE_DIR=/path/to/state
export AERO_LOG_DIR=/path/to/logs
```

### Telegram Configuration

Edit `src/travel_monitor.py`:
```python
TELEGRAM_CHAT_ID = "5187735980"  # Your chat ID
```

### Email Configuration

Edit `src/travel_monitor.py`:
```python
EMAIL_RECIPIENT = "[REDACTED]"
```

### Phone Configuration

Edit `src/travel_monitor.py`:
```python
PHONE_NUMBER = "+16507767054"
```

## Troubleshooting

### Check if monitoring is active

```bash
bash /home/ubuntu/.openclaw/workspace/aero/scripts/aero_travel_cron.sh status
```

### View recent logs

```bash
tail -f ~/.openclaw/workspace/logs/aero-travel-$(date +%Y%m%d).log
```

### Test FlightAware API connection

```bash
cd /home/ubuntu/.openclaw/workspace/aero
python3 test_live_api_v2.py
```

### Reset state

```bash
# Remove state files to start fresh
rm ~/.openclaw/workspace/state/aero-travel-*.json
```

## Alert Examples

### Gate Change (Warning)
```
✈️ Flight Alert: DL1430

🚪 Gate changed from A12 to B15

_Checked at 2:30 PM_
```

### Delay Alert (Warning)
```
✈️ Flight Alert: UA123

⏰ Flight delayed by 45 minutes
New departure: 3:15 PM

_Checked at 1:45 PM_
```

### Cancellation (Critical)
```
✈️ Flight Alert: AA456

🚨 CRITICAL: Flight cancelled
Status changed: Scheduled → Cancelled

_Checked at 10:00 AM_
```

## Integration with Existing Systems

- **Calendar**: Reads from `~/.openclaw/workspace/config/calendar-events.json`
- **Todoist**: Creates tasks in "Travel" project
- **FlightAware**: Uses API key from `~/.openclaw/credentials/flightaware.json`
- **Telegram**: Sends messages via bot API
- **Email**: Uses existing `send_email.py` script

## Support

For issues or questions:
1. Check logs: `~/.openclaw/workspace/logs/aero-*.log`
2. Verify API key: `cat ~/.openclaw/credentials/flightaware.json`
3. Test manually: `bash scripts/aero_travel_cron.sh full`

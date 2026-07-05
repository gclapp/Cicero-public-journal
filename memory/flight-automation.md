# Flight Task Automation

**Status:** Active - March 9 flight tasks created  
**System:** Manual detection + automatic task creation  

## How It Works

When I detect a flight in your calendar (or you tell me about one), I create:

### Task Bundle Structure
```
✈️ FLIGHT: [Date] - [Destination/Details]
  ├─ 🐕 Rover: Schedule dog sitting/walking [Due: 4 days before flight]
  ├─ 🏨 Check: Hotel confirmation & flight details [Due: 2 days before]
  └─ 🚗 Uber: Schedule airport ride [Due: 1 day before]
```

## Current Flight Tasks

### March 9, 2026
✅ Main task created (Due: March 2 - review details)  
✅ Rover subtask (Due: March 5)  
✅ Hotel/flight check (Due: March 7)  
✅ Uber ride (Due: March 8)  

## Future Automation

**Option 1: Weekly Scan (Recommended)**
- Script scans calendar every Sunday
- Detects flight keywords automatically
- Creates task bundles
- Status: Needs Google Calendar API setup

**Option 2: Manual**
- You tell me when you book flights
- I create tasks immediately
- Status: Working now

**Option 3: Email Forwarding**
- Forward confirmations to [REDACTED]
- I parse and create tasks
- Status: Can implement if needed

## Flight Keywords Detected
- flight, depart, arrive, travel, trip
- Airport codes: JFK, LAX, SFO, etc.
- Airlines: Delta, United, American, Southwest

## Next Flights to Watch
- Scan calendar weekly for new flights
- Create task bundles automatically
- Review and adjust dates as needed

🏛️ Automated by Cicero

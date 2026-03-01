# Flight Task Automation System

## Overview
Automatically creates task bundles when flights are detected in your calendar.

## How It Works

### Detection Methods
1. **Calendar Scan** (Weekly) - Script scans Google Calendar for flight keywords
2. **Manual Trigger** - You tell me "I have a flight on [date]"
3. **Email Forward** - Forward flight confirmations to [REDACTED]

### Task Structure Created

For each flight found, I create:

```
✈️ FLIGHT: [Flight Summary] ([Date]) [Priority 2]
  ├─ 🐕 Rover: Schedule dog sitting/walking [Due: 4 days before]
  ├─ 🏨 Check: Hotel & flight confirmations [Due: 2 days before]
  └─ 🚗 Uber: Schedule airport ride [Due: 1 day before]
```

## Flight Keywords Detected
- "flight", "depart", "arrive", "travel", "trip"
- Airport codes: JFK, LAX, SFO, etc.
- Airlines: Delta, United, American, Southwest

## Your Next Flight

**March 9 Flight** - Tasks created:
- ✅ Main flight task (due March 5)
- ✅ Rover subtask (due March 5)
- ✅ Hotel/flight check (due March 7)
- ✅ Uber scheduling (due March 8)

## Automation Options

### Option 1: Weekly Calendar Scan (Recommended)
- I run a script every Sunday
- Scans next 60 days for flights
- Creates tasks automatically
- You review and adjust as needed

### Option 2: Manual Notification
- You tell me when you book flights
- I create tasks immediately
- More control, less automation

### Option 3: Email Forwarding
- Forward confirmation emails to me
- I extract details and create tasks
- Good for complex itineraries

## Implementation Status

✅ Manual task creation - Working
⏳ Automated calendar scanning - Needs Google API setup
⏳ Email parsing - Can add if needed

## Next Steps

To enable full automation, you would need to:
1. Enable Google Calendar API
2. Create credentials.json
3. Authorize access (one-time)
4. I set up weekly cron job

Or we can stick with manual - just tell me when you book flights and I'll create the task bundles immediately.

🏛️ Managed by Cicero

# HEARTBEAT.md

## Check-In Schedule (ACTIVE)

**System:** Automated heartbeat every 55 minutes  
**Status:** FIXED - Cron job running + pending check-in system active  
**Timezone:** Pacific Time (PT)  

### Daily Check-Ins

| Check-In | Time (PT) | Purpose |
|----------|-----------|---------|
| Morning | 7:00 AM | Status, calendar, day ahead |
| Midday | 12:30 PM | Progress pulse check |
| Afternoon | 4:30 PM | Wrap-up prep |
| Evening | 8:30 PM | Day review, tomorrow preview |

**Modified:** March 4, 2026  
**Current Mode:** 4x daily (Morning, Midday, Afternoon, Evening)  
**Delivery:** Email to [REDACTED] + geoffrey.clapp@progyny.com  
**Stock updates:** End-of-day only (evening check-in)

---

## Automated Actions

**Every 55 minutes, the system:**
1. Logs heartbeat (keeps cache warm)
2. Checks if check-in time is within 5-minute window
3. Logs check-in due events
4. Waits for user interaction OR external trigger

**Morning Check-In Automation:**
1. Read calendar events from `config/calendar-events.json`
2. Check for travel events in next 24-48 hours
3. Include calendar summary in morning update
4. Flag any urgent items (flights, important meetings)

**Note:** Check-ins require user message or system trigger to actually send. The heartbeat prepares the check-in but doesn't auto-send (limitation of current architecture).

---

## Pending Check-In Detection

**When user messages:**
1. Read HEARTBEAT.md (this file)
2. Run `python3 scripts/deliver_checkin.py` to check for pending check-ins
3. If pending: Script sends email + returns Telegram message for delivery
4. Send Telegram message via `message` tool
5. If no pending: Send HEARTBEAT_OK or relevant update

**Check-in delivery flow:**
- Cron job queues check-in → writes to `pending-checkin.json` (includes both Telegram text + HTML email)
- Next user message → runs `deliver_checkin.py`:
  - **Email:** Sent immediately to [REDACTED] (CC: geoffrey.clapp@progyny.com)
  - **Telegram:** Message returned for delivery via `message` tool
- This bridges the gap between cron (no message access) and main session (has message access)

**Email Subjects:**
- Morning: "Cicero Check-In: Morning — Monday, March 11"
- Midday: "Cicero Check-In: Midday — Monday, March 11"
- Afternoon: "Cicero Check-In: Afternoon — Monday, March 11"
- Evening: "Cicero Check-In: Evening — Monday, March 11"

**Scripts:**
- `scripts/heartbeat_sender.py` — Queues check-ins (called by cron)
- `scripts/deliver_checkin.py` — Delivers pending check-ins (called by main session)

**Scheduled check-ins are now logged and tracked.**

---

## Logs

Location: `/home/ubuntu/.openclaw/workspace/logs/heartbeat.log`

View: `tail -f ~/.openclaw/workspace/logs/heartbeat.log`

---

## Implementation

**Cron Job:**
```
*/55 * * * * /home/ubuntu/.openclaw/workspace/scripts/heartbeat-check.sh
```

**Script:** `scripts/heartbeat-check.sh`
- Logs heartbeat timestamp
- Checks PT time against check-in schedule
- Logs when check-ins are due
- Maintains warm cache

---

## Next Check-In

**Morning:** Tomorrow 7:00 AM PT  
**Evening:** Tomorrow 8:00 PM PT  

**Timezone handling:** Automatically adjusts for travel (see timezone-management.md)

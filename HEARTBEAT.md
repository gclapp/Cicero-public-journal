# HEARTBEAT.md

## Check-In Schedule (ACTIVE)

**System:** Automated heartbeat every 55 minutes  
**Status:** FIXED - Cron job running  
**Timezone:** Pacific Time (PT)  

### Daily Check-Ins

| Check-In | Time (PT) | Purpose |
|----------|-----------|---------|
| Morning | 7:00 AM | Status, calendar, day ahead |
| Midday | 12:30 PM | Progress pulse check |
| Afternoon | 4:30 PM | Wrap-up prep |
| Evening | 8:30 PM | Day review, tomorrow preview |

**Modified:** March 3, 2026  
**Current Mode:** 2x daily (Morning + Evening only)  
**Stock updates:** End-of-day only (evening check-in)

---

## Automated Actions

**Every 55 minutes, the system:**
1. Logs heartbeat (keeps cache warm)
2. Checks if check-in time is within 5-minute window
3. Logs check-in due events
4. Waits for user interaction OR external trigger

**Note:** Check-ins require user message or system trigger to actually send. The heartbeat prepares the check-in but doesn't auto-send (limitation of current architecture).

---

## Manual Trigger

**When user messages:**
1. Read HEARTBEAT.md (this file)
2. Check: Is check-in due?
3. If yes: Send check-in immediately
4. If no: Send HEARTBEAT_OK or relevant update

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

# Cicero Instance Improvement Plan

## Issues Fixed Today (March 12, 2026)

### ✅ 1. Email Formatting Issues
**Problem:** Status updates had broken bold formatting and weird fonts in emails
**Root Cause:** The `heartbeat_sender.py` was using a simple string replace that didn't properly close HTML tags
**Fix:** Implemented proper `markdown_to_html()` function using regex to correctly convert `**text**` to `<strong>text</strong>`
**Status:** ✅ FIXED - Emails should now render properly with clean formatting

### ✅ 2. Missing Healthcare Data  
**Problem:** Whoop data was stale (from March 3, 9 days old)
**Root Cause:** No automated daily fetch was set up; token was also not refreshing properly
**Fix:** 
- Created `fetch_whoop_daily.py` script
- Fixed `whoop_client.py` to handle JSON token files and auto-refresh
- Added cron job for 6:30 AM PT daily fetch
**Status:** ✅ FIXED - Whoop data now updating daily

### ✅ 3. Missing Todoist Tasks
**Problem:** Status updates showed "No P1 or due-today tasks" when there were many tasks
**Root Cause:** Filter was too restrictive (only P1 + due today); excluded P2 and upcoming tasks
**Fix:** Updated `fetch_todoist_tasks.py` to include:
- P1 and P2 priority tasks
- Tasks due today
- Tasks due within next 3 days
- Overdue tasks (flagged separately)
**Status:** ✅ FIXED - Tasks now showing properly

---

## Improvements We Need to Work On Together

### 🔴 HIGH PRIORITY

#### 1. Whoop Token Refresh Issues
**Issue:** The token refresh is working but the recovery data shows concerning metrics (29% recovery, 0 hours sleep)
**Questions for you:**
- Are you still wearing your Whoop strap regularly?
- The data shows 3 workouts but 0 hours sleep - does this match your recollection?
- Should we set up alerts for concerning health metrics (e.g., recovery < 33%)?

#### 2. Todoist Task Overload
**Issue:** You have 44 overdue tasks showing in every check-in
**Options:**
- Bulk reschedule overdue tasks to realistic dates?
- Create a "Backlog" project to move old tasks out of daily view?
- Set up a weekly "task triage" session to clean these up?
- Filter out tasks older than X days from check-ins?

#### 3. Email vs Telegram Format
**Issue:** We send to both email and Telegram, but the formats need optimization
**Questions:**
- Do you prefer different content for email vs Telegram?
- Should email be more detailed and Telegram be a brief summary?
- Are the current send times (7 AM, 12:30 PM, 4:30 PM, 8:30 PM PT) working for you?

### 🟡 MEDIUM PRIORITY

#### 4. Calendar Integration Enhancements
**Current State:** Calendar events are showing but could be smarter
**Ideas:**
- Detect meeting conflicts and warn you
- Suggest prep time before important meetings
- Auto-detect travel and suggest packing lists
- Integrate with restaurant reservations to suggest dishes

#### 5. Stock Data Improvements
**Current State:** Basic PGNY, AAPL, NVDA tracking
**Ideas:**
- Add competitor stock tracking (Maven, Carrot, etc.)
- Alert on significant price movements (>5% change)
- Weekly portfolio summary
- Market open/close summaries

#### 6. Weather Integration
**Current State:** Basic LA weather showing
**Ideas:**
- Auto-detect your location from calendar events
- Show weather for travel destinations
- Alert on weather that might affect plans (rain, extreme heat)
- Suggest clothing based on weather + calendar

### 🟢 LOWER PRIORITY

#### 7. Weight Loss Tracking Integration
**Current State:** Static checklist in morning updates
**Ideas:**
- Connect to Apple Health data when you set up the iPhone Shortcuts
- Track weekly weight trends
- Celebrate milestones
- Suggest adjustments based on progress

#### 8. Competitive Intelligence Integration
**Current State:** Separate daily emails for competitive intel
**Ideas:**
- Include key competitive highlights in morning check-ins?
- Alert immediately on major competitor news (funding, leadership changes)
- Weekly competitive summary

#### 9. Voice/Call Capabilities
**Current State:** Voice call is configured but rarely used
**Questions:**
- Would you like proactive voice calls for urgent items?
- Should I call you for critical alerts (flight delays, urgent emails from Grace)?
- TTS for longer briefings when you're driving?

#### 10. Memory & Learning Improvements
**Current State:** Daily logs + MEMORY.md
**Ideas:**
- Better pattern recognition from your calendar (when do you prefer meetings vs focus time?)
- Learn your restaurant preferences and suggest new spots
- Track which friends you haven't seen in a while and suggest catch-ups
- Remember your preferences and apply them proactively

---

## Technical Debt & Infrastructure

### 🔧 System Improvements

1. **Error Monitoring**
   - Set up better alerting when scripts fail
   - Create a dashboard of system health
   - Weekly system status report

2. **Data Backup**
   - Automated backup of credentials and config
   - Version control for important data files

3. **Security Review**
   - Regular audit of what data is stored where
   - Cleanup of old log files
   - Review of API key rotation needs

4. **Documentation**
   - Document all cron jobs and their purposes
   - Create runbook for common issues
   - Document the data flow for each integration

---

## Your Feedback Needed

Please let me know:

1. **Which of these improvements matter most to you?** (Rank top 3)
2. **What's working well that we should keep?**
3. **What's annoying or not useful?** (Let's remove or fix it)
4. **Any new capabilities you want to explore?**

Once you give me direction, I'll prioritize and start implementing.

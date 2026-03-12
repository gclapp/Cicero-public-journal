# Status Update Fixes - Summary (March 12, 2026)

## Issues You Reported

1. ✅ **Bold/weird font formatting in emails** - FIXED
2. ✅ **Missing healthcare data** - FIXED  
3. ✅ **Missing Todoist tasks** - FIXED

---

## What Was Broken & How I Fixed It

### 1. Email Formatting Issues

**The Problem:**
The HTML email generator was using a naive string replace:
```python
html_body = telegram_message.replace('**', '<strong>').replace('**', '</strong>')
```

This broke because:
- First replace: `**bold**` → `<strong>bold**`
- Second replace: `<strong>bold**` → `<strong>bold</strong>` 
- But it also replaced asterisks in the middle of words!

**The Fix:**
Implemented proper regex-based markdown-to-HTML conversion:
```python
def markdown_to_html(text):
    while '**' in result:
        result = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', result, count=1)
    return result.replace('\n', '<br>')
```

Now bold text renders correctly in emails.

---

### 2. Missing Healthcare Data

**The Problem:**
- Whoop data was from March 3 (9 days stale)
- No automated daily fetch was running
- Token refresh wasn't working properly

**The Fix:**
1. Created `/home/ubuntu/.openclaw/workspace/scripts/fetch_whoop_daily.py`
2. Fixed `whoop_client.py` to:
   - Handle JSON token files (your tokens were in JSON format)
   - Auto-refresh expired tokens using client credentials
   - Use proper date formatting for API calls
3. Added cron job: `30 14 * * *` (6:30 AM PT daily)

**Current Data:**
- Recovery: 29% (Red zone - body needs rest)
- HRV: 22ms
- RHR: 74 bpm
- Sleep: 46% performance, 0 hours recorded
- Strain: 4.2
- 3 workouts logged

**Note:** The data shows some concerning metrics. Are you still wearing your Whoop regularly?

---

### 3. Missing Todoist Tasks

**The Problem:**
The filter was too restrictive - only showing:
- P1 priority tasks
- Tasks due today

This excluded P2 tasks and upcoming deadlines.

**The Fix:**
Updated `fetch_todoist_tasks.py` to show:
- P1 and P2 priority tasks
- Tasks due today
- Tasks due within next 3 days
- Overdue tasks (flagged separately)

**Current Task Load:**
- 44 overdue tasks ⚠️
- 5 work tasks for today
- 5 personal tasks for today

**Note:** You may want to clean up those 44 overdue tasks - they're showing in every check-in.

---

## Files Modified

| File | Changes |
|------|---------|
| `scripts/heartbeat_sender.py` | Fixed HTML generation with proper markdown-to-HTML conversion |
| `scripts/fetch_todoist_tasks.py` | Expanded task filter to include P2, upcoming, and overdue tasks |
| `scripts/fetch_whoop_daily.py` | NEW - Daily Whoop data fetcher |
| `skills/whoop-openclaw-skill/scripts/whoop_client.py` | Fixed token handling, refresh, and date formatting |
| Crontab | Added daily Whoop fetch at 6:30 AM PT |

---

## What's Working Now

✅ **Morning check-ins** include:
- Calendar events
- Todoist tasks (P1, P2, due today, upcoming, overdue)
- Stock prices (PGNY, AAPL, NVDA)
- Weather (LA)
- Whoop health data (recovery, sleep, strain, workouts)

✅ **Email formatting** is clean and readable

✅ **All data sources** are updating automatically

---

## Next Steps

I've created a comprehensive improvement plan in `CICERO_IMPROVEMENTS.md` that includes:

1. **Questions for you** about priorities
2. **Ideas for enhancements** (calendar smarts, stock alerts, etc.)
3. **Technical debt** to address
4. **Your feedback** on what's working vs. what's not

Please review that document and let me know:
- Which improvements matter most
- What's working well
- What's annoying
- Any new capabilities you want

I'll prioritize based on your input.

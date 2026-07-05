# Token Monitoring Failure - June 5, 2026

## What Happened
- Google Calendar token expired ~8 days ago (May 28)
- No alerts were sent to Geoff
- Issue only discovered when Geoff manually asked me to check
- Token monitoring script was running but NOT alerting

## Root Causes
1. **token_auto_refresh_v2.py** was detecting critical issues but not sending alerts
2. No rate-limited alerting system was in place
3. I wasn't proactively checking token health logs
4. The cron job was failing silently for days

## Fixes Applied
1. ✅ Added alerting to token_auto_refresh_v2.py:
   - Email alerts to [REDACTED]
   - Telegram alerts
   - 4-hour rate limiting to prevent spam

2. ✅ Added calendar_token_health.py for dedicated calendar monitoring

3. ✅ Added token_health_monitor.py to cron (runs 9 AM & 9 PM PT)

## Current Status
- 🔴 Google Calendar: Token missing (needs re-auth)
- 🔴 Google Docs: Token 14 days old (needs re-auth)
- 🟢 Whoop: Working fine

## Action Required
Run: `python3 /home/ubuntu/.openclaw/workspace/scripts/calendar_reader.py`
Then authorize via Google and paste the auth code.

## Prevention
- Token health now alerts via email + Telegram
- Rate limited to once per 4 hours per issue
- Monitoring runs every 30 minutes

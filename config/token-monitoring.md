# Token Monitoring System

## Overview
Automated daily monitoring of all OAuth tokens to prevent silent failures.

## Monitored Tokens

| Token | Service | Location | Alert Threshold | Critical |
|-------|---------|----------|-----------------|----------|
| **calendar-token.pickle** | Google Calendar | `~/.openclaw/credentials/` | 6 days | 🔴 Yes |
| **.whoop_token** | Whoop API | `~/` | 25 days | 🟡 No |
| **.whoop_refresh_token** | Whoop Refresh | `~/` | 25 days | 🟡 No |
| **email_config.json** | Gmail SMTP | `~/.openclaw/` | 30 days | 🔴 Yes |

## Schedule

**Daily Check:** 7:25 AM PT (5 minutes before morning check-in)
- Script: `scripts/token-health-cron.sh`
- Log: `logs/token-health.log`
- Report: `logs/token-health.json`

## Alert Levels

### 🔴 Critical (Immediate Action)
- Calendar token >6 days old
- Email config missing
- Any token file not found

**Response:** Alert user immediately, provide re-auth instructions

### 🟡 Warning (Attention Soon)
- Whoop token >25 days old
- Any token approaching threshold

**Response:** Include in morning check-in, plan refresh

### ✅ Healthy
- All tokens within thresholds

**Response:** Silent (no action needed)

## Manual Check

```bash
# Run token health check manually
python3 scripts/token_health_check.py

# View logs
tail -f ~/.openclaw/workspace/logs/token-health.log
```

## Token Refresh Procedures

### Google Calendar
```bash
# When token expires:
rm ~/.openclaw/credentials/calendar-token.pickle
python3 scripts/calendar_auth.py --url
# Follow instructions to authorize
```

### Whoop
```bash
# When token expires:
# Re-run OAuth flow (see whoop_oauth.py)
python3 skills/whoop-openclaw-skill/scripts/whoop_oauth.py
```

### Gmail SMTP
- App passwords don't expire
- If issues: regenerate at https://myaccount.google.com/apppasswords

## Integration with Morning Check-In

The token health check runs at 7:25 AM PT and its results are included in the 7:30 AM morning check-in:

1. **7:25 AM:** Token health check runs
2. **7:30 AM:** Morning check-in includes token status
3. **If critical issues:** Immediate alert sent
4. **If warnings:** Included in daily report

## History

- **2026-03-22:** Token monitoring system implemented
- **Calendar token:** Refreshed today (valid for 6+ days)

---
*Last Updated: 2026-03-22*

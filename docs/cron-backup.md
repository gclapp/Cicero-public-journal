---
layout: default
title: Cron Job Backup & Restore
---

# Cron Job Backup & Restore

**Critical:** System updates and restarts can silently wipe cron jobs. This page documents the backup and recovery system.

## The Problem

On March 5-8, 2026, all cron jobs were silently lost during a system update:
- No heartbeat check-ins for 3 days
- No watch hunt alerts (missed potential 1973 Rolex listings)
- No calendar sync (stale data in briefings)
- No security audits or Reddit reports

There was no error message. No alert. Just silence.

## The Solution

### Backup Script

Located at: `scripts/cron-backup.sh`

```bash
# Backup current crontab
bash scripts/cron-backup.sh backup

# Restore from latest backup
bash scripts/cron-backup.sh restore

# Verify all expected jobs present
bash scripts/cron-backup.sh verify
```

### Active Cron Jobs

| Job | Schedule | Script | Purpose |
|-----|----------|--------|---------|
| Heartbeat | Every 55 min | `heartbeat-check.sh` | Keep cache warm, check-ins |
| Watch Hunt | 9 AM & 6 PM PT | `watch-hunt-cron.sh` | 1973 Rolex search |
| Calendar Refresh | 6:55 AM PT | `calendar_reader.py` | Daily calendar sync |
| IMAP Check | Every 15 min | `imap-check-cron.sh` | Email monitoring |
| Competitor Report | 2 PM PT daily | `daily-competitor-report.sh` | Competitive intel |
| Security Audit | Sundays 8 AM PT | `weekly-security-audit.sh` | Security report |
| Reddit Report | Sundays 9 AM PT | `reddit-weekly-report.sh` | Sentiment analysis |
| Weekly Email | Saturdays 9 AM PT | `weekly-email-report.py` | Week summary |

## Post-Update Checklist

After ANY system update or restart:

- [ ] Run `bash scripts/cron-backup.sh verify`
- [ ] If jobs missing, run `bash scripts/cron-backup.sh restore`
- [ ] Check logs: `tail ~/.openclaw/workspace/logs/*.log`

## Key Lesson

> "The most dangerous failures are the ones you don't notice. When a cron job disappears, there's no error message, no alert, no smoke. Just silence."

**Verification after any system change is non-negotiable.**

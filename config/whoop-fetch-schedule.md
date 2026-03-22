# Whoop Data Fetch Schedule

## Automated Fetches (3x Daily)

| Time (PT) | Time (UTC) | Purpose | Data Captured |
|-----------|------------|---------|---------------|
| **7:30 AM** | 2:30 PM | Morning review | Overnight recovery, sleep data |
| **12:00 PM** | 7:00 PM | Midday check | Morning workout, current strain |
| **6:00 PM** | 1:00 AM+1 | Evening review | Full day strain, workout completion |

## Data Dimensions Captured

Each fetch retrieves:
1. **Recovery** - Score, RHR, HRV, SpO2, skin temp
2. **Sleep** - Performance, duration, stages, efficiency
3. **Cycles** - Strain, calories, heart rate data
4. **Workouts** - Activity type, strain, zones, calories
5. **Profile** - Baseline reference
6. **Trends** - 7-day rolling averages

## Storage Location

- Daily data: `~/.openclaw/workspace/data/whoop/whoop-YYYY-MM-DD.json`
- Recovery trends: `~/.openclaw/workspace/data/whoop/recovery-trend-YYYY-MM-DD.json`
- Sleep trends: `~/.openclaw/workspace/data/whoop/sleep-trend-YYYY-MM-DD.json`
- Workout trends: `~/.openclaw/workspace/data/whoop/workout-trend-YYYY-MM-DD.json`
- Logs: `~/.openclaw/workspace/logs/whoop-cron.log`

## Manual Fetch

```bash
# Fetch today's data
bash ~/.openclaw/workspace/scripts/whoop-fetch-cron.sh

# View logs
tail -f ~/.openclaw/workspace/logs/whoop-cron.log
```

## Last Updated
2026-03-22 - Schedule: 7:30 AM, 12:00 PM, 6:00 PM PT

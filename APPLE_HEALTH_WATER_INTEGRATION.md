# Apple Health Water Integration

## Overview
Your Apple Health water data is now automatically integrated into Vitus's aggressive health coaching system.

## How It Works

### 1. Data Collection
- **Source:** Apple Health → iPhone Shortcut → Email to [REDACTED]
- **Format:** 10-day rolling history as email attachments
- **Processing:** Automated every 30 minutes via cron job

### 2. Data Storage
- **File:** `~/.openclaw/workspace/data/water-intake-history.json`
- **Includes:** Daily ounces, liters, cups, metadata
- **Retention:** Persistent, growing history

### 3. Vitus Integration
- **Morning Briefings:** 7-day hydration chart displayed
- **Mission Priority:** Low hydration triggers red/yellow missions
- **Insights:** Hydration alerts appear alongside recovery/sleep insights
- **Coaching:** Aggressive hydration targets (80oz = ~2.4L = 10 cups)

## Hydration Targets

| Level | Ounces | Coaching Response |
|-------|--------|-------------------|
| Critical | < 20 oz | 🔴 RED MISSION: "Hydration Emergency" |
| Low | < 40 oz | 🟡 YELLOW MISSION: "Hydration Focus" |
| Good | 40-79 oz | 🟢 Standard coaching |
| Optimal | 80+ oz | 🟢 GREEN: "Excellent Hydration" |

## What Vitus Does With This Data

### Morning Briefing
- Shows 7-day hydration bar chart
- Compares today vs yesterday
- Displays progress toward 80oz goal
- Includes hydration in overall status

### Mission Generation
- **Red Mission:** <20oz today AND <30oz yesterday
- **Yellow Mission:** <40oz today OR yesterday
- **Green Mission:** Meeting hydration goals

### Coaching Insights
- "CRITICAL DEHYDRATION" — <20oz average
- "Low Hydration" — <40oz average  
- "Excellent Hydration" — 80oz+ average

## Files Modified/Created

| File | Purpose |
|------|---------|
| `scripts/process_water_email.py` | Email processor + data storage |
| `agents/health-agent/data_collection.py` | Apple Health water integration |
| `agents/health-agent/coach_engine.py` | Hydration analysis + mission logic |
| `data/water-intake-history.json` | Stored water data |

## Cron Job
```
*/30 * * * * python3 scripts/process_water_email.py
```

## Current Status
✅ 11 days of data stored
✅ Automated processing active
✅ Vitus integration complete
✅ Aggressive coaching enabled

## Next Steps
1. Keep sending water data from Apple Health
2. Vitus will automatically include it in every briefing
3. Expect hydration-focused missions when you're low

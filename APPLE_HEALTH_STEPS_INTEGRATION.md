# Apple Health Steps Integration

## Overview
Your Apple Health steps data is now integrated into Vitus's aggressive health coaching system, alongside water and Whoop data.

## How It Works

### 1. Data Collection
- **Source:** Apple Health → iPhone Shortcut → Email to [REDACTED]
- **Format:** 10-day rolling history as email attachments (same as water)
- **Processing:** Automated every 30 minutes via cron job
- **Target:** 10,000 steps/day

### 2. Data Storage
- **File:** `~/.openclaw/workspace/data/steps-history.json`
- **Includes:** Daily steps, miles, calories, % of goal
- **Retention:** Persistent, growing history

### 3. Vitus Integration
- **Morning Briefings:** 7-day steps chart with 10k target line
- **Mission Priority:** Low steps triggers red/yellow missions
- **Insights:** Steps alerts appear alongside recovery/sleep/hydration
- **Coaching:** Aggressive 10k step target with no excuses

## Steps Targets

| Level | Steps | Coaching Response |
|-------|-------|-------------------|
| Crisis | < 2,000 | 🔴 RED: "SEDENTARY CRISIS" - Health emergency |
| Emergency | < 2,000 (6pm+) | 🔴 RED: "MOVEMENT EMERGENCY" |
| Low | < 5,000 | 🔴 RED: "CRITICAL INACTIVITY" |
| Behind | < 5,000 (6pm+) | 🟡 YELLOW: "Steps Behind - Catch Up" |
| Slipping | < 7,500 (2 days) | 🟡 YELLOW: "Steps Slipping - Fix This" |
| Below | < 7,500 | 🟡 YELLOW: "Steps Low - Move More" |
| Good | 7,500-9,999 | 🟢 GREEN: "Steps Strong" |
| Optimal | 10,000+ | 🟢 GREEN: "Steps Target Crushed" |

## What Vitus Does With This Data

### Morning Briefing
- Shows 7-day steps bar chart with 10k target line
- Displays today vs 7-day average
- Shows % of goal progress
- Includes coach's note with contextual messaging

### Mission Generation
- **Red Mission:** <2,000 steps for 2 days = "SEDENTARY CRISIS"
- **Red Mission:** <2,000 steps at 6pm = "MOVEMENT EMERGENCY"
- **Yellow Mission:** <7,500 steps = "Steps Low - Move More"

### Coaching Insights
- "SEDENTARY CRISIS" - Priority 10/10
- "MOVEMENT EMERGENCY" - Priority 9/10
- "Steps Slipping" - Priority 6/10
- "Steps Target Crushed" - Priority 3/10

## Files Modified/Created

| File | Purpose |
|------|---------|
| `scripts/process_steps_email.py` | Email processor + data storage |
| `agents/health-agent/data_collection.py` | Apple Health steps integration |
| `agents/health-agent/coach_engine.py` | Steps analysis + visualization |
| `data/steps-history.json` | Stored steps data |

## Cron Job
```
*/30 * * * * python3 scripts/process_steps_email.py
```

## Current Status
⏳ Waiting for first steps emails from Apple Health
✅ Processor ready
✅ Vitus integration complete
✅ Aggressive coaching enabled

## Next Steps
1. Send steps data from Apple Health (same shortcut as water, just change to steps)
2. Vitus will automatically include it in every briefing
3. Expect movement-focused missions when you're sedentary

## Combined with Water Data
Now Vitus tracks:
- 💧 **Hydration** (80oz target)
- 👟 **Steps** (10k target)
- 🫀 **Recovery** (Whoop)
- 😴 **Sleep** (Whoop)
- 💪 **Training** (Whoop)

All with aggressive, no-excuses coaching.

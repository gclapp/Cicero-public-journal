# Health Dashboard & Weight Loss Accountability

**Dashboard URL:** https://gclapp.github.io/health-dashboard/  
**GitHub Repo:** https://github.com/gclapp/health-dashboard  
**Created:** February 28, 2026  

## System Overview

### Data Flow
```
iPhone (Apple Health + Lose It! + Whoop)
    ↓ (Automated export via Shortcuts)
Email to [REDACTED]
    ↓ (Python processor)
Dashboard + Analytics
    ↓
Weekly reports + Insights
```

### Components

1. **iPhone Shortcuts**
   - Automated daily export at 9 PM
   - Sends weight, steps, workouts, calories
   - File: `SHORTCUTS_SETUP.md`

2. **Python Processor** (`health_processor.py`)
   - Parses Apple Health XML
   - Calculates trends and insights
   - Generates dashboard JSON

3. **Web Dashboard** (`index.html`)
   - Weight loss charts
   - Activity tracking
   - Sleep analysis
   - Goal progress

4. **Weekly Reports**
   - Progress summary
   - Insights and recommendations
   - Delivered Sunday evenings

## Accountability Schedule

**Daily (Automatic):**
- 9 PM: iPhone exports data
- 9:30 PM: I review metrics
- Alerts sent if red flags

**Daily (Your Tasks):**
- Morning weigh-in
- Log food in Lose It!
- Complete workout
- Check dashboard

**Sunday:**
- Weekly report email
- Progress analysis
- Plan adjustments

**Bi-weekly:**
- Telegram check-in
- Personal check on energy/sleep

**Red Alert Triggers:**
- Weight up 3+ days
- No workouts 4+ days
- Recovery below 50% for 3 days
- Missed weigh-ins 3 days

## Goal: 20 lbs in 10-12 weeks

**Timeline:**
- Weeks 1-2: 4 lbs (aggressive start)
- Weeks 3-4: 3 lbs (building habits)
- Weeks 5-8: 6 lbs (sustained)
- Weeks 9-12: 6 lbs (finish strong)

**Current Status:**
⏳ Awaiting: iPhone Shortcuts setup
⏳ Awaiting: First health data export
⏳ Start date: March 1, 2026

## Files

- `health-dashboard/` - Dashboard code
- `health-analytics-system.md` - Full system documentation
- `aggressive-accountability-plan.txt` - Accountability details
- `SHORTCUTS_SETUP.md` - iPhone setup guide

## Integration with Weight Loss Plan

This dashboard complements the weight loss plan:
- Tracks all metrics automatically
- Provides data-driven insights
- Keeps you accountable
- Visualizes progress

Combined with Todoist reminders and my check-ins, this creates a complete accountability system.

🏛️ Managed by Cicero

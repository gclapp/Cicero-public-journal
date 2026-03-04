#!/bin/bash
# Morning Calendar Refresh & Intelligence
# Runs at 6:55 AM PT (14:55 UTC) to prepare data for 7 AM check-in

cd /home/ubuntu/.openclaw/workspace

# Refresh calendar data
python3 scripts/calendar_reader.py >> logs/calendar-refresh.log 2>&1

# Fetch Whoop health data
python3 scripts/whoop_fetch.py >> logs/whoop-fetch.log 2>&1

# Generate morning update with calendar + health integration
python3 scripts/generate_morning_update.py > config/morning-update-ready.txt 2>&1

# Analyze calendar for patterns (restaurants, travel, kids)
python3 scripts/calendar_intelligence.py >> logs/calendar-intelligence.log 2>&1

# Create travel Todoist tasks for upcoming trips
python3 scripts/travel_automation.py >> logs/travel-automation.log 2>&1

echo "[$(date)] Morning calendar refresh, Whoop data & intelligence complete" >> logs/morning-prep.log

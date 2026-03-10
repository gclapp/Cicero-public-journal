#!/bin/bash
# Dog Day Afternoon Pre-Show Reminder
# Runs 3 days before the show (March 13 at 7:30 PM ET = March 13 at 4:30 PM PT)

WORKSPACE="/home/ubuntu/.openclaw/workspace"
cd "$WORKSPACE"

# Run the reminder script
python3 scripts/dog_day_afternoon_reminder.py >> logs/dog-day-reminder.log 2>&1

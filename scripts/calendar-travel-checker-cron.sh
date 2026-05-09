#!/bin/bash
# Calendar Travel Checker Cron Script
# Runs 3x per week (Mon/Wed/Fri) at 9 AM PT
# Creates Todoist tasks for upcoming travel

# Set up environment
export PATH="/home/ubuntu/.npm-global/bin:$PATH"
export HOME="/home/ubuntu"

# Log file
LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/calendar-travel-cron.log"

# Timestamp
echo "========================================" >> "$LOG_FILE"
echo "Calendar Travel Checker - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run the checker
python3 /home/ubuntu/.openclaw/workspace/scripts/calendar_travel_checker.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Check completed successfully" >> "$LOG_FILE"
else
    echo "❌ Check failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

exit $EXIT_CODE

#!/bin/bash
# Calendar Travel Checker Cron Script
# Runs 3x per week (Mon/Wed/Fri) at 9 AM PT
# Creates Todoist tasks for upcoming travel

# Set up environment
export PATH="/home/ubuntu/.npm-global/bin:$PATH"
export HOME="/home/ubuntu"

# Log file
LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/calendar-travel-cron.log"
LOCK_FILE="/tmp/calendar_travel_checker.lock"

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another instance is running (PID: $PID). Exiting." >> "$LOG_FILE"
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi
echo $$ > "$LOCK_FILE"

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

# Clean up lock file
rm -f "$LOCK_FILE"

echo "" >> "$LOG_FILE"

exit $EXIT_CODE

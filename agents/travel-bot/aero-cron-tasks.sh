#!/bin/bash
# Aero Travel Manager - Task Creation Cron Job
# Runs Monday, Wednesday, Friday at 4 PM PT

SCRIPT_DIR="/home/ubuntu/.openclaw/workspace/agents/travel-bot"
LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/aero-cron.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Starting task creation..." >> "$LOG_FILE"

python3 "$SCRIPT_DIR/aero_travel_manager.py" tasks >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Task creation completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Task creation failed with code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

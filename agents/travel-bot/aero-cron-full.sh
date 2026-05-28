#!/bin/bash
# Aero Travel Manager - Full Run (Tasks + Monitoring)
# Runs daily at 6 AM PT for comprehensive check

SCRIPT_DIR="/home/ubuntu/.openclaw/workspace/agents/travel-bot"
LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/aero-cron.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Starting full run..." >> "$LOG_FILE"

python3 "$SCRIPT_DIR/aero_travel_manager.py" full >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Full run completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Full run failed with code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

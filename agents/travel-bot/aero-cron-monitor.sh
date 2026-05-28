#!/bin/bash
# Aero Travel Manager - Day-of-Travel Monitoring Cron Job
# Runs every 30 minutes during travel days

SCRIPT_DIR="/home/ubuntu/.openclaw/workspace/agents/travel-bot"
LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/aero-cron.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Starting day-of-travel monitoring..." >> "$LOG_FILE"

python3 "$SCRIPT_DIR/aero_travel_manager.py" monitor >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Monitoring completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aero: Monitoring failed with code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

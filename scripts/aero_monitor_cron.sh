#!/bin/bash
# Aero Day-of-Travel Monitoring Cron
# Runs every 30 minutes to check flights today/tomorrow

LOG_DIR="/home/ubuntu/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/aero-monitor.log"
LOCK_FILE="/tmp/aero_monitor.lock"
AERO_SCRIPT="/home/ubuntu/.openclaw/workspace/agents/travel-bot/aero_travel_manager.py"

mkdir -p "$LOG_DIR"

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if ps -p "$PID" > /dev/null 2>&1; then
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"

# Run monitoring only (faster, checks flights today/tomorrow)
/usr/bin/python3 "$AERO_SCRIPT" monitor >> "$LOG_FILE" 2>&1

rm -f "$LOCK_FILE"

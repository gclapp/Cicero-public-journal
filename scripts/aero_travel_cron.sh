#!/bin/bash
# Aero Travel Manager Cron Wrapper
# Runs task creation and day-of-travel monitoring

LOG_DIR="/home/ubuntu/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/aero-cron.log"
LOCK_FILE="/tmp/aero_travel.lock"
AERO_SCRIPT="/home/ubuntu/.openclaw/workspace/agents/travel-bot/aero_travel_manager.py"

# Create log directory
mkdir -p "$LOG_DIR"

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another Aero instance running (PID: $PID). Exiting." >> "$LOG_FILE"
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Aero Travel Manager Starting ===" >> "$LOG_FILE"

# Run full task creation + monitoring
if timeout 300 /usr/bin/python3 "$AERO_SCRIPT" full >> "$LOG_FILE" 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Aero completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Aero failed or timed out" >> "$LOG_FILE"
fi

rm -f "$LOCK_FILE"

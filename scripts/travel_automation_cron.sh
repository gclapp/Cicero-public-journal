#!/bin/bash
# Travel Automation Cron Wrapper
# Ensures travel tasks are created reliably

LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/travel-automation-v2.log"
LOCK_FILE="/tmp/travel_automation.lock"
SCRIPT="/home/ubuntu/.openclaw/workspace/scripts/travel_automation_v2.py"

# Add npm-global bin to PATH for todoist CLI
export PATH="$PATH:/home/ubuntu/.npm-global/bin"

# Create log directory if needed
mkdir -p "$(dirname "$LOG_FILE")"

# Verify todoist CLI is available
if ! command -v todoist &> /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: todoist CLI not found in PATH" >> "$LOG_FILE"
    exit 1
fi

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

# Run the script with timeout
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting travel automation..." >> "$LOG_FILE"

if timeout 300 /usr/bin/python3 "$SCRIPT" >> "$LOG_FILE" 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Travel automation completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Travel automation failed or timed out" >> "$LOG_FILE"
fi

rm -f "$LOCK_FILE"

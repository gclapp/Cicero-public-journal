#!/bin/bash
# Aero Travel Manager Cron Wrapper
# Runs task creation and day-of-travel monitoring
# Flock locking: prevents overlapping runs

LOG_DIR="/home/ubuntu/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/aero-cron.log"
AERO_SCRIPT="/home/ubuntu/.openclaw/workspace/agents/travel-bot/aero_travel_manager.py"

# Create log directory
mkdir -p "$LOG_DIR"

# Acquire exclusive lock to prevent overlapping runs
source "$(dirname "$0")/flock_utils.sh"
if ! acquire_lock "aero-travel"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another Aero instance running. Exiting." >> "$LOG_FILE"
    exit 0
fi
setup_lock_cleanup

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Aero Travel Manager Starting ===" >> "$LOG_FILE"

# Run full task creation + monitoring
if timeout 300 /usr/bin/python3 "$AERO_SCRIPT" full >> "$LOG_FILE" 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Aero completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Aero failed or timed out" >> "$LOG_FILE"
fi

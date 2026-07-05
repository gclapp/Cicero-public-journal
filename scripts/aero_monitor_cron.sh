#!/bin/bash
# Aero Day-of-Travel Monitoring Cron
# Runs every 30 minutes to check flights today/tomorrow
# Flock locking: prevents overlapping runs

LOG_DIR="/home/ubuntu/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/aero-monitor.log"
AERO_SCRIPT="/home/ubuntu/.openclaw/workspace/agents/travel-bot/aero_travel_manager.py"

mkdir -p "$LOG_DIR"

# Acquire exclusive lock to prevent overlapping runs
source "$(dirname "$0")/flock_utils.sh"
acquire_lock "aero-monitor" || exit 0
setup_lock_cleanup

# Run monitoring only (faster, checks flights today/tomorrow)
/usr/bin/python3 "$AERO_SCRIPT" monitor >> "$LOG_FILE" 2>&1

#!/bin/bash
# Aero Day-of-Travel Monitor Cron Script
# 
# This script runs the travel monitor with appropriate check frequency
# based on how close the departure time is.
#
# Schedule:
# - Regular checks: Every 30 minutes (default)
# - Frequent checks: Every 5 minutes on day of departure
#
# Cron setup:
# */30 * * * * /home/ubuntu/.openclaw/workspace/aero/scripts/aero_travel_monitor.sh regular
# */5 * * * * /home/ubuntu/.openclaw/workspace/aero/scripts/aero_travel_monitor.sh frequent

set -e

WORKSPACE_DIR="/home/ubuntu/.openclaw/workspace"
AERO_DIR="$WORKSPACE_DIR/aero"
SCRIPT_DIR="$AERO_DIR/scripts"
LOG_DIR="$WORKSPACE_DIR/logs"
STATE_DIR="$WORKSPACE_DIR/state"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$STATE_DIR"

# Log file with date
LOG_FILE="$LOG_DIR/aero-travel-monitor-$(date +%Y%m%d).log"

# Lock file to prevent overlapping runs
LOCK_FILE="/tmp/aero_travel_monitor.lock"

# Check type: "regular" or "frequent"
CHECK_TYPE="${1:-regular}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$CHECK_TYPE] $1" | tee -a "$LOG_FILE"
}

# Check if another instance is running
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        PID=$(cat "$LOCK_FILE" 2>/dev/null)
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Another instance is running (PID: $PID). Exiting."
            exit 0
        else
            rm -f "$LOCK_FILE"
        fi
    fi
}

# Set up lock
acquire_lock() {
    echo $$ > "$LOCK_FILE"
}

# Clean up lock on exit
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# Main execution
main() {
    log "=========================================="
    log "Aero Travel Monitor Starting"
    log "=========================================="
    
    # Check lock
    check_lock
    acquire_lock
    
    # Set up Python path
    export PYTHONPATH="$AERO_DIR/src:$PYTHONPATH"
    
    # Run the monitor
    cd "$AERO_DIR"
    
    if timeout 120 python3 -m src.travel_monitor --check "$CHECK_TYPE" >> "$LOG_FILE" 2>&1; then
        log "Monitor completed successfully"
    else
        log "ERROR: Monitor failed or timed out"
        exit 1
    fi
    
    log "=========================================="
}

main "$@"

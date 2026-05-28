#!/bin/bash
# Aero Travel Automation Cron Script
# 
# This script runs the unified Aero travel automation.
# It handles both task creation and flight monitoring.
#
# Recommended cron schedule:
# # Task creation - twice daily (9 AM and 9 PM PT)
# 0 16,4 * * * /home/ubuntu/.openclaw/workspace/aero/scripts/aero_travel_cron.sh full
#
# # Flight monitoring - regular checks every 30 minutes
# */30 * * * * /home/ubuntu/.openclaw/workspace/aero/scripts/aero_travel_cron.sh monitor
#
# # Flight monitoring - frequent checks every 5 minutes on travel days
# */5 * * * * /home/ubuntu/.openclaw/workspace/aero/scripts/aero_travel_cron.sh monitor-frequent

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
LOG_FILE="$LOG_DIR/aero-travel-$(date +%Y%m%d).log"

# Lock file
LOCK_FILE="/tmp/aero_travel_automation.lock"

# Command type
COMMAND="${1:-full}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$COMMAND] $1" | tee -a "$LOG_FILE"
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

# Run Python script with appropriate command
run_python() {
    local cmd="$1"
    local check_type="${2:-regular}"
    
    export PYTHONPATH="$AERO_DIR/src:$PYTHONPATH"
    cd "$AERO_DIR"
    
    if [ "$cmd" == "monitor" ]; then
        timeout 120 python3 -m src.aero_travel_automation monitor --check-type "$check_type" >> "$LOG_FILE" 2>&1
    else
        timeout 300 python3 -m src.aero_travel_automation "$cmd" >> "$LOG_FILE" 2>&1
    fi
}

# Main execution
main() {
    log "=========================================="
    log "Aero Travel Automation Starting"
    log "=========================================="
    
    # Check lock
    check_lock
    acquire_lock
    
    case "$COMMAND" in
        full)
            log "Running full automation (tasks + monitoring)..."
            if run_python full; then
                log "Full automation completed successfully"
            else
                log "ERROR: Full automation failed"
                exit 1
            fi
            ;;
        
        tasks)
            log "Running task creation..."
            if run_python tasks; then
                log "Task creation completed successfully"
            else
                log "ERROR: Task creation failed"
                exit 1
            fi
            ;;
        
        monitor)
            log "Running flight monitoring (regular)..."
            if run_python monitor regular; then
                log "Flight monitoring completed successfully"
            else
                log "ERROR: Flight monitoring failed"
                exit 1
            fi
            ;;
        
        monitor-frequent)
            log "Running flight monitoring (frequent)..."
            if run_python monitor frequent; then
                log "Flight monitoring completed successfully"
            else
                log "ERROR: Flight monitoring failed"
                exit 1
            fi
            ;;
        
        status)
            run_python status
            ;;
        
        *)
            log "Unknown command: $COMMAND"
            log "Usage: $0 [full|tasks|monitor|monitor-frequent|status]"
            exit 1
            ;;
    esac
    
    log "=========================================="
}

main "$@"

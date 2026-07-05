#!/bin/bash
# flock_utils.sh - Shared flock locking utilities for cron scripts
# Usage: source this file and call acquire_lock() at the start of your script

# Default lock directory
LOCK_DIR="/tmp/openclaw-locks"

# Create lock directory if it doesn't exist
mkdir -p "$LOCK_DIR"

# Acquire an exclusive lock using flock
# Usage: acquire_lock "script_name"
# Returns 0 on success, 1 if lock is held by another process
acquire_lock() {
    local script_name="${1:-$(basename "$0")}"
    local lock_file="$LOCK_DIR/${script_name}.lock"
    local lock_fd=200
    
    # Open lock file on file descriptor
    eval "exec $lock_fd>\"$lock_file\""
    
    # Try to acquire exclusive lock (non-blocking)
    if ! flock -n $lock_fd; then
        local pid=$(cat "$lock_file" 2>/dev/null || echo "unknown")
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Lock held by PID $pid, another instance of $script_name is running" >&2
        return 1
    fi
    
    # Write our PID to the lock file
    echo $$ > "$lock_file"
    
    # Store lock info for cleanup
    export FLOCK_LOCK_FILE="$lock_file"
    export FLOCK_SCRIPT_NAME="$script_name"
    
    return 0
}

# Acquire lock or wait for it (blocking)
# Usage: acquire_lock_wait "script_name" [timeout_seconds]
acquire_lock_wait() {
    local script_name="${1:-$(basename "$0")}"
    local timeout="${2:-0}"  # 0 = no timeout
    local lock_file="$LOCK_DIR/${script_name}.lock"
    local lock_fd=200
    
    # Open lock file on file descriptor
    eval "exec $lock_fd>\"$lock_file\""
    
    if [ "$timeout" -gt 0 ]; then
        # Try with timeout
        local start_time=$(date +%s)
        while ! flock -n $lock_fd 2>/dev/null; do
            local current_time=$(date +%s)
            local elapsed=$((current_time - start_time))
            if [ "$elapsed" -ge "$timeout" ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Timeout waiting for lock after ${timeout}s" >&2
                return 1
            fi
            sleep 1
        done
    else
        # Blocking wait
        flock $lock_fd
    fi
    
    # Write our PID to the lock file
    echo $$ > "$lock_file"
    
    export FLOCK_LOCK_FILE="$lock_file"
    export FLOCK_SCRIPT_NAME="$script_name"
    
    return 0
}

# Release the lock (optional - happens automatically on exit)
# Usage: release_lock
release_lock() {
    if [ -n "$FLOCK_LOCK_FILE" ] && [ -f "$FLOCK_LOCK_FILE" ]; then
        rm -f "$FLOCK_LOCK_FILE"
    fi
}

# Setup automatic lock cleanup on script exit
# Usage: setup_lock_cleanup
cleanup_on_exit() {
    release_lock
}

setup_lock_cleanup() {
    trap cleanup_on_exit EXIT
}

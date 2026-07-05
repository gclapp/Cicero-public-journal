#!/bin/bash
# IMAP Email Checker - runs every 15 minutes
# Checks [REDACTED] for new emails
# Flock locking: prevents overlapping runs

# Acquire exclusive lock to prevent overlapping runs
source "$(dirname "$0")/flock_utils.sh"
acquire_lock "imap-check" || exit 0
setup_lock_cleanup

SCRIPT_DIR="/home/ubuntu/.openclaw/workspace/scripts"
LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/imap-checker.log"

# Log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $1" >> "$LOG_FILE"
}

log "=== IMAP check started ==="

# Run the email checker
if python3 "$SCRIPT_DIR/imap_email_reader.py" >> "$LOG_FILE" 2>&1; then
    log "✅ Check completed"
else
    log "❌ Check failed"
fi

log "=== Check completed ==="

#!/bin/bash
# Check-in email sender - runs 4x daily
# Sends to both personal and work emails

LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/checkin-emails.log"
SCRIPT_DIR="/home/ubuntu/.openclaw/workspace/scripts"

# Log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $1" >> "$LOG_FILE"
}

log "=== Check-in email job started ==="

# Run the email generator
if python3 "$SCRIPT_DIR/generate_checkin_email.py" >> "$LOG_FILE" 2>&1; then
    log "✅ Check-in email sent successfully"
else
    log "❌ Check-in email failed"
fi

log "=== Job completed ==="

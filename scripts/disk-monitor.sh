#!/bin/bash
# disk-monitor.sh - Monitor disk usage and alert when above threshold
# Runs hourly via cron, logs to workspace/logs/, sends email alerts
# Flock locking: prevents overlapping runs

# Acquire exclusive lock to prevent overlapping runs
source "$(dirname "$0")/flock_utils.sh"
acquire_lock "disk-monitor" || exit 0
setup_lock_cleanup

THRESHOLD=60
LOG_DIR="/home/ubuntu/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/disk-monitor.log"
ALERT_LOG="$LOG_DIR/disk-alerts.log"
EMAIL_SCRIPT="/home/ubuntu/.openclaw/workspace/scripts/send_email.py"
ALERT_EMAIL="[REDACTED]"
HOSTNAME=$(hostname)

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Get current disk usage (root partition)
USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log current usage
echo "[$TIMESTAMP] Disk usage: ${USAGE}%" >> "$LOG_FILE"

# Check if usage exceeds threshold
if [ "$USAGE" -gt "$THRESHOLD" ]; then
    ALERT_MSG="[$TIMESTAMP] ALERT: Disk usage is ${USAGE}% (threshold: ${THRESHOLD}%)"
    echo "$ALERT_MSG" >> "$ALERT_LOG"
    echo "$ALERT_MSG" >> "$LOG_FILE"
    
    # Get detailed disk info for email
    DISK_DETAILS=$(df -h /)
    
    # Send email alert
    if [ -f "$EMAIL_SCRIPT" ]; then
        python3 "$EMAIL_SCRIPT" \
            --to "$ALERT_EMAIL" \
            --subject "Disk Alert: ${HOSTNAME} at ${USAGE}% capacity" \
            --body "## Disk Usage Alert

**Host:** ${HOSTNAME}
**Current Usage:** ${USAGE}%
**Threshold:** ${THRESHOLD}%
**Time:** ${TIMESTAMP} UTC

### Disk Details
\`\`\`
${DISK_DETAILS}
\`\`\`

Please investigate and free up disk space if needed." 2>&1 >> "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            echo "[$TIMESTAMP] Email alert sent to $ALERT_EMAIL" >> "$LOG_FILE"
        else
            echo "[$TIMESTAMP] Failed to send email alert" >> "$LOG_FILE"
        fi
    else
        echo "[$TIMESTAMP] Email script not found at $EMAIL_SCRIPT" >> "$LOG_FILE"
    fi
fi

# Keep log files from growing too large (rotate after 1000 lines)
if [ $(wc -l < "$LOG_FILE") -gt 1000 ]; then
    tail -n 500 "$LOG_FILE" > "$LOG_FILE.tmp"
    mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
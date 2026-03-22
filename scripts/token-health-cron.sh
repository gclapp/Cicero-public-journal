#!/bin/bash
# token-health-cron.sh - Daily token health check
# Run at 7:25 AM PT (before morning check-in)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/token-health.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running token health check..." >> "$LOG_FILE"

python3 "$SCRIPT_DIR/token_health_check.py" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ All tokens healthy" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Token issues detected" >> "$LOG_FILE"
fi

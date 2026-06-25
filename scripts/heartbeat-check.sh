#!/bin/bash
# heartbeat-check.sh - Triggered every 55 minutes to maintain warm cache
# Also checks for scheduled check-ins

HEARTBEAT_LOG="/home/ubuntu/.openclaw/workspace/logs/heartbeat.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S %Z')

# Log heartbeat
mkdir -p $(dirname "$HEARTBEAT_LOG")
echo "[$DATE] Heartbeat triggered" >> "$HEARTBEAT_LOG"

LOCAL_INFO=$(python3 /home/ubuntu/.openclaw/workspace/scripts/user_timezone.py --field shell 2>/dev/null || true)
if [ -n "$LOCAL_INFO" ]; then
    echo "[$DATE] Local timezone context: $LOCAL_INFO" | tr '\n' ' ' >> "$HEARTBEAT_LOG"
    echo "" >> "$HEARTBEAT_LOG"
fi

# Local-time check-ins are scheduled by run_at_user_local_time.py so they can
# follow Geoff when travel shifts his working timezone. This heartbeat stays a
# lightweight warm-up and status pulse.

echo "[$DATE] Heartbeat complete" >> "$HEARTBEAT_LOG"

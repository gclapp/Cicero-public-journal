#!/bin/bash
# heartbeat-check.sh - Triggered every 55 minutes to maintain warm cache
# Also checks for scheduled check-ins

HEARTBEAT_LOG="/home/ubuntu/.openclaw/workspace/logs/heartbeat.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S %Z')

# Log heartbeat
mkdir -p $(dirname "$HEARTBEAT_LOG")
echo "[$DATE] Heartbeat triggered" >> "$HEARTBEAT_LOG"

# Check if check-in is due
HOUR=$(date '+%H')
MIN=$(date '+%M')
TIME="$HOUR:$MIN"

# Check-in schedule (Pacific Time)
# 07:00, 12:30, 16:30, 20:30

# Convert current time to PT for comparison
PT_HOUR=$(TZ=America/Los_Angeles date '+%H')
PT_MIN=$(TZ=America/Los_Angeles date '+%M')
PT_TIME="$PT_HOUR:$PT_MIN"

# Check if it's check-in time (within 5 minute window)
# Check if it's check-in time and queue a message
CHECKIN_TRIGGERED=false

if [[ "$PT_TIME" == "07:0"* ]] || [[ "$PT_TIME" == "07:1"* ]] || [[ "$PT_TIME" == "07:2"* ]] || [[ "$PT_TIME" == "07:3"* ]] || [[ "$PT_TIME" == "07:4"* ]]; then
    echo "[$DATE] Morning check-in due (7 AM PT)" >> "$HEARTBEAT_LOG"
    python3 /home/ubuntu/.openclaw/workspace/scripts/heartbeat_sender.py
    CHECKIN_TRIGGERED=true
fi

if [[ "$PT_TIME" == "12:3"* ]] || [[ "$PT_TIME" == "12:4"* ]] || [[ "$PT_TIME" == "12:5"* ]]; then
    echo "[$DATE] Midday check-in due (12:30 PM PT)" >> "$HEARTBEAT_LOG"
    if [ "$CHECKIN_TRIGGERED" = false ]; then
        python3 /home/ubuntu/.openclaw/workspace/scripts/heartbeat_sender.py
        CHECKIN_TRIGGERED=true
    fi
fi

if [[ "$PT_TIME" == "16:3"* ]] || [[ "$PT_TIME" == "16:4"* ]] || [[ "$PT_TIME" == "16:5"* ]]; then
    echo "[$DATE] Afternoon check-in due (4:30 PM PT)" >> "$HEARTBEAT_LOG"
    if [ "$CHECKIN_TRIGGERED" = false ]; then
        python3 /home/ubuntu/.openclaw/workspace/scripts/heartbeat_sender.py
        CHECKIN_TRIGGERED=true
    fi
fi

if [[ "$PT_TIME" == "20:3"* ]] || [[ "$PT_TIME" == "20:4"* ]] || [[ "$PT_TIME" == "20:5"* ]]; then
    echo "[$DATE] Evening check-in due (8:30 PM PT)" >> "$HEARTBEAT_LOG"
    if [ "$CHECKIN_TRIGGERED" = false ]; then
        python3 /home/ubuntu/.openclaw/workspace/scripts/heartbeat_sender.py
        CHECKIN_TRIGGERED=true
    fi
fi

echo "[$DATE] Heartbeat complete" >> "$HEARTBEAT_LOG"

#!/bin/bash
# Flight Email Filter Cron Script
# Runs every 15 minutes to filter flight emails

LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/flight-email-filter.log"
SCRIPT="/home/ubuntu/.openclaw/workspace/scripts/flight_email_filter.py"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Run the filter
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"
python3 "$SCRIPT" >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"

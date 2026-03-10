#!/bin/bash
# Resend Sunday NYC Itinerary Reminder
# Runs 3 days before March 15 (March 12 at 7:00 AM PT)

WORKSPACE="/home/ubuntu/.openclaw/workspace"
cd "$WORKSPACE"

# Send the itinerary email
python3 scripts/send_email.py \
  --to "[REDACTED]" \
  --cc "keers003@gmail.com" \
  --subject "🗽 REMINDER: Sunday in NYC - March 15 (3 Days Away!)" \
  --body-file sunday-nyc-itinerary-weather.html \
  --html >> logs/sunday-reminder.log 2>&1

echo "$(date): Sunday NYC itinerary resent" >> logs/sunday-reminder.log

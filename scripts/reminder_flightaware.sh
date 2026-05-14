#!/bin/bash
# FlightAware setup reminder - runs in ~2 hours

# Telegram message
python3 -c "
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
from telegram_notify import send_message
send_message('🔔 Reminder: Time to set up FlightAware!')
"

# Email backup
python3 /home/ubuntu/.openclaw/workspace/scripts/send_email.py \
  --to "[REDACTED]" \
  --subject "Reminder: FlightAware Setup" \
  --body "<h2>⏰ Reminder</h2><p>It's time to set up FlightAware as requested.</p><p>~Cicero</p>" \
  --html 2>/dev/null

echo "FlightAware reminder sent at $(date)"

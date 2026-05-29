#!/usr/bin/env python3
"""
DMHC Delegation Search - Send Immediate Telegram Update
Usage: python3 dmhc_send_update.py "Your message here"
"""

import os
import sys
import requests
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = ***"TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5187735980")

def send_telegram_message(message: str) -> bool:
    """Send a message via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN:
        ***"[ERROR] TELEGRAM_BOT_TOKEN not set!")
        print("Set it with: export TELEGRAM_BOT_TOKEN='***'")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent successfully")
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        # Send default status update
        now = datetime.now(timezone.utc)
        pt_time = now - timedelta(hours=8)
        
        message = f"""📊 *DMHC Delegation Search - Status Check*

⏰ {pt_time.strftime('%I:%M %p PT')} | {now.strftime('%H:%M UTC')}

Monitor is active and checking progress..."""
        
        send_telegram_message(message)
    else:
        # Send custom message
        custom_message = sys.argv[1]
        send_telegram_message(custom_message)

if __name__ == "__main__":
    main()

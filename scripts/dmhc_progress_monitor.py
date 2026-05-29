#!/usr/bin/env python3
"""
DMHC Delegation Search Project - Progress Monitor
Sends Telegram updates on project progress every 10-15 minutes
Alerts immediately if main session seems stuck (>5 min no activity)

Required environment variables:
- TELEGRAM_BOT_TOKEN: Bot token from @BotFather
- TELEGRAM_CHAT_ID: Target chat ID (default: 5187735980 for [REDACTED])
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5187735980")
CHECK_INTERVAL = 60  # Check every minute
UPDATE_INTERVAL = 600  # Send update every 10 minutes (600 seconds)
STUCK_THRESHOLD = 300  # Alert if no activity for 5 minutes (300 seconds)

# Project steps
STEPS = [
    "Medical Surveys source connector",
    "Enforcement Actions source connector", 
    "Full extraction run",
    "LLM switch to real mode"
]

# State file to track progress
STATE_FILE = Path("/home/ubuntu/.openclaw/workspace/.dmhc_monitor_state.json")

def send_telegram_message(message: str) -> bool:
    """Send a message via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"[TELEGRAM NOT CONFIGURED] Would send: {message[:100]}...")
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
            print(f"[SENT] Telegram message delivered")
            return True
        else:
            print(f"[ERROR] Telegram API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")
        return False

def load_state():
    """Load monitor state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load state: {e}")
    return {
        "current_step": 0,
        "last_activity": datetime.now(timezone.utc).isoformat(),
        "last_update": datetime.now(timezone.utc).isoformat(),
        "steps_completed": [],
        "alerts_sent": []
    }

def save_state(state):
    """Save monitor state to file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[WARN] Could not save state: {e}")

def check_main_session_activity():
    """Check if main session has recent activity."""
    # This is a placeholder - in a real implementation, we would check
    # the LCM database or session logs for recent activity
    # For now, we'll rely on external updates via the state file
    return True

def format_progress_message(step_index: int, status: str = "in_progress") -> str:
    """Format a progress update message."""
    now = datetime.now(timezone.utc)
    pt_time = now - timedelta(hours=8)  # Convert to Pacific Time
    
    emoji = "🟡" if status == "in_progress" else "✅" if status == "completed" else "⏳"
    
    message = f"""📊 *DMHC Delegation Search - Progress Update*

⏰ {pt_time.strftime('%I:%M %p PT')} | {now.strftime('%H:%M UTC')}

*Current Status:*
"""
    
    for i, step in enumerate(STEPS):
        if i < step_index:
            message += f"✅ {step}\n"
        elif i == step_index:
            message += f"{emoji} *{step}* ← Current\n"
        else:
            message += f"⏳ {step}\n"
    
    progress_pct = int((step_index / len(STEPS)) * 100)
    message += f"\n📈 Progress: {progress_pct}% ({step_index}/{len(STEPS)} steps)"
    
    if status == "stuck":
        message += "\n\n⚠️ *ALERT:* No activity detected for >5 minutes!"
    
    return message

def send_startup_message():
    """Send initial startup message."""
    message = """🚀 *DMHC Progress Monitor Started*

Monitoring: DMHC Delegation Search Project
Target: [REDACTED]
Update interval: Every 10-15 minutes
Alert threshold: >5 min no activity

Tracking 4 steps:
1. Medical Surveys source connector
2. Enforcement Actions source connector
3. Full extraction run
4. LLM switch to real mode

✅ Monitor is now active"""
    
    send_telegram_message(message)

def send_completion_message():
    """Send project completion message."""
    message = """🎉 *DMHC Delegation Search - COMPLETE!*

All 4 steps have been completed:
✅ Medical Surveys source connector
✅ Enforcement Actions source connector
✅ Full extraction run
✅ LLM switch to real mode

📈 Progress: 100%

The project is ready for use!"""
    
    send_telegram_message(message)

def main():
    """Main monitoring loop."""
    print("=" * 60)
    print("DMHC Delegation Search - Progress Monitor")
    print("=" * 60)
    print(f"Telegram Bot Token: {'✅ Configured' if TELEGRAM_BOT_TOKEN else '❌ NOT CONFIGURED'}")
    print(f"Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print(f"Stuck threshold: {STUCK_THRESHOLD} seconds")
    print("=" * 60)
    
    if not TELEGRAM_BOT_TOKEN:
        print("\n⚠️ WARNING: TELEGRAM_BOT_TOKEN not set!")
        print("Set it with: export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("Get a bot token from @BotFather on Telegram")
        print("\nContinuing in dry-run mode (no messages will be sent)...\n")
    
    # Load state
    state = load_state()
    
    # Send startup message
    send_startup_message()
    
    print(f"\nCurrent step: {state['current_step']} of {len(STEPS)}")
    print(f"Last activity: {state['last_activity']}")
    print(f"Last update: {state['last_update']}")
    print("\nMonitor is running. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            now = datetime.now(timezone.utc)
            state = load_state()
            
            # Parse timestamps
            last_activity = datetime.fromisoformat(state['last_activity'])
            last_update = datetime.fromisoformat(state['last_update'])
            
            # Check if stuck (no activity for >5 minutes)
            time_since_activity = (now - last_activity).total_seconds()
            if time_since_activity > STUCK_THRESHOLD:
                # Only alert once per stuck period
                stuck_alert_key = f"stuck_{state['current_step']}"
                if stuck_alert_key not in state.get('alerts_sent', []):
                    print(f"⚠️ ALERT: No activity for {int(time_since_activity)} seconds!")
                    message = format_progress_message(state['current_step'], status="stuck")
                    send_telegram_message(message)
                    state.setdefault('alerts_sent', []).append(stuck_alert_key)
                    save_state(state)
            
            # Send regular update every 10-15 minutes
            time_since_update = (now - last_update).total_seconds()
            if time_since_update >= UPDATE_INTERVAL:
                print(f"📊 Sending progress update (step {state['current_step']})...")
                message = format_progress_message(state['current_step'])
                send_telegram_message(message)
                state['last_update'] = now.isoformat()
                save_state(state)
            
            # Check if all steps completed
            if state['current_step'] >= len(STEPS):
                print("🎉 All steps completed!")
                send_completion_message()
                break
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")
        message = """⏹️ *DMHC Progress Monitor Stopped*

Monitor has been manually stopped.
Current progress may be incomplete."""
        send_telegram_message(message)

if __name__ == "__main__":
    main()

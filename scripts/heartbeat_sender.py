#!/usr/bin/env python3
"""
heartbeat_sender.py - Sends scheduled check-ins via Telegram
Called by heartbeat-check.sh when a check-in is due
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add workspace to path for imports
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace')

def get_pt_time():
    """Get current Pacific Time"""
    import pytz
    pt = pytz.timezone('America/Los_Angeles')
    return datetime.now(pt)

def get_checkin_type(hour, minute):
    """Determine which check-in is due based on PT time"""
    time_val = hour * 100 + minute
    
    # Morning: 7:00-7:45 AM
    if 700 <= time_val <= 745:
        return "morning"
    # Midday: 12:30-12:55 PM  
    elif 1230 <= time_val <= 1255:
        return "midday"
    # Afternoon: 4:30-4:55 PM
    elif 1630 <= time_val <= 1655:
        return "afternoon"
    # Evening: 8:30-8:55 PM
    elif 2030 <= time_val <= 2055:
        return "evening"
    else:
        return None

def send_telegram_message(message):
    """Send message via Telegram bot using OpenClaw's message tool"""
    # This will be called via the OpenClaw gateway
    # For now, we'll use a marker file that the main session can detect
    
    checkin_file = Path("/home/ubuntu/.openclaw/workspace/logs/pending-checkin.json")
    checkin_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checkin_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "sent": False
        }, f, indent=2)
    
    return True

def generate_morning_update():
    """Generate morning check-in content"""
    pt_now = get_pt_time()
    
    # Read calendar events if available
    calendar_file = Path("/home/ubuntu/.openclaw/workspace/config/calendar-events.json")
    calendar_info = ""
    
    if calendar_file.exists():
        try:
            with open(calendar_file) as f:
                events = json.load(f)
            if events:
                calendar_info = "\n\n📅 **Today's Calendar:**\n"
                for event in events[:3]:  # Top 3 events
                    calendar_info += f"• {event.get('summary', 'Event')}\n"
        except:
            pass
    
    message = f"""🌅 **Morning Check-In** — {pt_now.strftime('%A, %B %d')}

Good morning! Here's your day ahead:{calendar_info}

What's your focus for today?"""
    
    return message

def generate_midday_checkin():
    """Generate midday check-in content"""
    pt_now = get_pt_time()
    
    message = f"""☀️ **Midday Pulse Check** — {pt_now.strftime('%I:%M %p')}

How's the day going? Any blockers or wins to share?"""
    
    return message

def generate_afternoon_checkin():
    """Generate afternoon check-in content"""
    pt_now = get_pt_time()
    
    message = f"""🌤️ **Afternoon Wrap-Up Prep** — {pt_now.strftime('%I:%M %p')}

What's left to close out today? Anything you need to defer to tomorrow?"""
    
    return message

def generate_evening_checkin():
    """Generate evening check-in content"""
    pt_now = get_pt_time()
    
    # Check for stock updates (end of day)
    stock_info = ""
    stock_file = Path("/home/ubuntu/.openclaw/workspace/logs/stock-update.json")
    if stock_file.exists():
        try:
            with open(stock_file) as f:
                stock_data = json.load(f)
            if stock_data.get('pgny_price'):
                stock_info = f"\n\n📈 **PGNY:** ${stock_data['pgny_price']:.2f} ({stock_data.get('change', 'N/A')})"
        except:
            pass
    
    message = f"""🌙 **Evening Review** — {pt_now.strftime('%A, %B %d')}

How did today go? Any highlights or lessons learned?{stock_info}

Tomorrow's looking good. Rest well! 🦞"""
    
    return message

def generate_html_email(checkin_type, telegram_message, pt_now):
    """Generate HTML version of check-in for email"""
    
    # Convert markdown-style bold to HTML
    html_body = telegram_message.replace('**', '<strong>').replace('**', '</strong>')
    # Convert newlines to <br>
    html_body = html_body.replace('\n', '<br>')
    
    # Add signature
    html_body += "<br><br>—<br><em>Cicero 🏛️</em>"
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ border-bottom: 2px solid #4a90d9; padding-bottom: 10px; margin-bottom: 20px; }}
        .content {{ background: #f9f9f9; padding: 20px; border-radius: 8px; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0; color: #4a90d9;">Cicero Check-In</h2>
        <p style="margin: 5px 0 0 0; color: #666;">{pt_now.strftime('%A, %B %d, %Y')}</p>
    </div>
    <div class="content">
        {html_body}
    </div>
    <div class="footer">
        <p>This is an automated check-in from Cicero 🏛️</p>
        <p>To respond, message me on Telegram: <a href="https://t.me/geoffclapp">@geoffclapp</a></p>
        <p style="font-size: 11px; color: #999; margin-top: 10px;">This email was sent from an unmonitored address. Replies will not be received.</p>
    </div>
</body>
</html>"""
    
    return html_template

def main():
    pt_now = get_pt_time()
    checkin_type = get_checkin_type(pt_now.hour, pt_now.minute)
    
    if not checkin_type:
        print(f"No check-in due at {pt_now.strftime('%I:%M %p PT')}")
        sys.exit(0)
    
    # Generate appropriate message
    if checkin_type == "morning":
        message = generate_morning_update()
    elif checkin_type == "midday":
        message = generate_midday_checkin()
    elif checkin_type == "afternoon":
        message = generate_afternoon_checkin()
    elif checkin_type == "evening":
        message = generate_evening_checkin()
    else:
        message = f"Check-in: {checkin_type}"
    
    # Write to pending check-in file
    checkin_file = Path("/home/ubuntu/.openclaw/workspace/logs/pending-checkin.json")
    checkin_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate HTML email version
    html_message = generate_html_email(checkin_type, message, pt_now)
    
    with open(checkin_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "checkin_type": checkin_type,
            "message": message,
            "html_message": html_message,
            "subject": f"Cicero Check-In: {checkin_type.title()} — {pt_now.strftime('%A, %B %d')}",
            "pt_time": pt_now.strftime('%Y-%m-%d %H:%M:%S'),
            "sent": False,
            "channels": ["telegram", "email"]
        }, f, indent=2)
    
    print(f"Check-in queued: {checkin_type} at {pt_now.strftime('%I:%M %p PT')} (Telegram + Email)")
    
    # Log it
    log_file = Path("/home/ubuntu/.openclaw/workspace/logs/heartbeat.log")
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Check-in queued: {checkin_type}\n")

if __name__ == "__main__":
    main()

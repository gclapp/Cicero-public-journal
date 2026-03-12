#!/usr/bin/env python3
"""
heartbeat_sender.py - Sends scheduled check-ins via Telegram
Called by heartbeat-check.sh when a check-in is due
"""

import os
import sys
import json
import re
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

def markdown_to_html(text):
    """Convert markdown-style formatting to proper HTML"""
    # Convert **bold** to <strong>bold</strong>
    # Use a regex to properly handle paired asterisks
    result = text
    
    # Handle bold text - replace **text** with <strong>text</strong>
    # Use a loop to handle multiple occurrences
    while '**' in result:
        result = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', result, count=1)
    
    # Convert newlines to <br> tags
    result = result.replace('\n', '<br>')
    
    return result

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
    """Generate comprehensive morning check-in with all data sources"""
    pt_now = get_pt_time()
    
    # Import the comprehensive data fetchers
    try:
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from fetch_todoist_tasks import get_todoist_summary
        from fetch_stock_data import get_stock_summary
        from fetch_weather import get_weather_summary
        todoist_summary = get_todoist_summary()
        stock_summary = get_stock_summary()
        weather_summary = get_weather_summary()
    except Exception as e:
        print(f"Error fetching data: {e}")
        todoist_summary = "📋 **Tasks:** Todoist data unavailable\n"
        stock_summary = "📈 **Markets:** Stock data unavailable\n"
        weather_summary = "🌤️ **Weather:** Data unavailable\n"
    
    # Read calendar events
    calendar_file = Path("/home/ubuntu/.openclaw/workspace/config/calendar-events.json")
    calendar_info = ""
    location = "Los Angeles"  # Default
    
    if calendar_file.exists():
        try:
            with open(calendar_file) as f:
                events = json.load(f)
            if events and events.get('events'):
                calendar_info = "\n📅 **Today's Calendar:**\n"
                for event in events['events'][:5]:  # Top 5 events
                    summary = event.get('summary', 'Event')
                    calendar_info += f"• {summary}\n"
                    # Try to detect location from events
                    if event.get('location'):
                        location = event.get('location')
        except Exception as e:
            print(f"Error reading calendar: {e}")
    
    if not calendar_info:
        calendar_info = "\n📅 **Today's Calendar:** No events scheduled.\n"
    
    # Get Whoop health data
    whoop_info = ""
    whoop_file = Path("/home/ubuntu/.openclaw/workspace/data/whoop/latest-summary.txt")
    if whoop_file.exists():
        try:
            with open(whoop_file) as f:
                whoop_data = f.read()
            if whoop_data and "No Whoop data" not in whoop_data:
                whoop_info = f"\n💪 **Health (Whoop):**\n{whoop_data[:400]}...\n"
            else:
                whoop_info = "\n💪 **Health:** Whoop data not available yet.\n"
        except Exception as e:
            whoop_info = "\n💪 **Health:** Whoop data unavailable.\n"
    else:
        whoop_info = "\n💪 **Health:** Whoop data not available.\n"
    
    message = f"""🌅 **Morning Check-In** — {pt_now.strftime('%A, %B %d')}

📍 **Location:** {location}

Good morning! Here's your day ahead:
{calendar_info}
{todoist_summary}
{stock_summary}
{weather_summary}
{whoop_info}
What's your focus for today?"""
    
    return message

def generate_midday_checkin():
    """Generate midday check-in with all data"""
    pt_now = get_pt_time()
    
    # Import the comprehensive data fetchers
    try:
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from fetch_todoist_tasks import get_todoist_summary
        from fetch_stock_data import get_stock_summary
        todoist_summary = get_todoist_summary()
        stock_summary = get_stock_summary()
    except Exception as e:
        print(f"Error fetching data: {e}")
        todoist_summary = "📋 **Tasks:** Todoist data unavailable\n"
        stock_summary = "📈 **Markets:** Stock data unavailable\n"
    
    message = f"""☀️ **Midday Pulse Check** — {pt_now.strftime('%I:%M %p')}

How's the day going? Any blockers or wins to share?

{todoist_summary}
{stock_summary}
What's your focus for the rest of the day?"""
    
    return message

def generate_afternoon_checkin():
    """Generate afternoon check-in with all data"""
    pt_now = get_pt_time()
    
    # Import the comprehensive data fetchers
    try:
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from fetch_todoist_tasks import get_todoist_summary
        from fetch_stock_data import get_stock_summary
        todoist_summary = get_todoist_summary()
        stock_summary = get_stock_summary()
    except Exception as e:
        print(f"Error fetching data: {e}")
        todoist_summary = "📋 **Tasks:** Todoist data unavailable\n"
        stock_summary = "📈 **Markets:** Stock data unavailable\n"
    
    message = f"""🌤️ **Afternoon Wrap-Up Prep** — {pt_now.strftime('%I:%M %p')}

What's left to close out today? Anything you need to defer to tomorrow?

{todoist_summary}
{stock_summary}
Ready to wrap up strong?"""
    
    return message

def generate_evening_checkin():
    """Generate evening check-in with all data"""
    pt_now = get_pt_time()
    
    # Import the comprehensive data fetchers
    try:
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from fetch_todoist_tasks import get_todoist_summary
        from fetch_stock_data import get_stock_summary
        from fetch_weather import get_weather_summary
        todoist_summary = get_todoist_summary()
        stock_summary = get_stock_summary()
        weather_summary = get_weather_summary()
    except Exception as e:
        print(f"Error fetching data: {e}")
        todoist_summary = "📋 **Tasks:** Todoist data unavailable\n"
        stock_summary = "📈 **Markets:** Stock data unavailable\n"
        weather_summary = "🌤️ **Weather:** Data unavailable\n"
    
    message = f"""🌙 **Evening Review** — {pt_now.strftime('%A, %B %d')}

How did today go? Any highlights or lessons learned?

{todoist_summary}
{stock_summary}
{weather_summary}
Tomorrow's looking good. Rest well! 🦞"""
    
    return message

def generate_html_email(checkin_type, telegram_message, pt_now):
    """Generate HTML version of check-in for email with proper formatting"""
    
    # Convert markdown to HTML properly
    html_body = markdown_to_html(telegram_message)
    
    # Add signature
    html_body += "<br><br>—<br><em>Cicero 🏛️</em>"
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 3px solid #4a90d9; padding-bottom: 15px; margin-bottom: 25px; }}
        .header h2 {{ margin: 0; color: #4a90d9; font-size: 26px; font-weight: 600; }}
        .header p {{ margin: 8px 0 0 0; color: #666; font-size: 16px; }}
        .content {{ font-size: 15px; color: #444; }}
        .content strong {{ color: #222; font-weight: 600; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; font-size: 13px; color: #666; text-align: center; }}
        .footer a {{ color: #4a90d9; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Cicero Check-In</h2>
            <p>{pt_now.strftime('%A, %B %d, %Y')}</p>
        </div>
        <div class="content">
            {html_body}
        </div>
        <div class="footer">
            <p>This is an automated check-in from Cicero 🏛️</p>
            <p>To respond, message me on Telegram: <a href="https://t.me/geoffclapp">@geoffclapp</a></p>
            <p style="font-size: 11px; color: #999; margin-top: 10px;">This email was sent from an unmonitored address. Replies will not be received.</p>
        </div>
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

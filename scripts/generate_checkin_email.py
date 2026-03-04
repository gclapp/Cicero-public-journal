#!/usr/bin/env python3
"""
Generate and email check-in updates (4x daily)
Sends to both personal and work emails
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
WHOOP_SUMMARY_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "whoop" / "latest-summary.txt"
EMAIL_CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"

# Email recipients
RECIPIENTS = [
    "[REDACTED]",
    "geoffrey.clapp@progyny.com"
]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FROM_EMAIL = "[REDACTED]"

def load_email_config():
    """Load Gmail app password"""
    if EMAIL_CONFIG_PATH.exists():
        with open(EMAIL_CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def send_email(to_list, subject, body, html=True):
    """Send email to multiple recipients"""
    config = load_email_config()
    
    if 'app_password' not in config:
        print("❌ Gmail app password not configured")
        return False
    
    app_password = config['app_password']
    
    msg = MIMEMultipart('alternative')
    msg['From'] = FROM_EMAIL
    msg['To'] = ", ".join(to_list)
    msg['Subject'] = subject
    
    content_type = 'html' if html else 'plain'
    msg.attach(MIMEText(body, content_type))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(FROM_EMAIL, app_password)
            server.send_message(msg)
        print(f"✅ Email sent to: {', '.join(to_list)}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def load_calendar():
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)

def load_whoop():
    """Load Whoop summary"""
    if not WHOOP_SUMMARY_FILE.exists():
        return None
    with open(WHOOP_SUMMARY_FILE, 'r') as f:
        return f.read()

def get_check_in_type():
    """Determine which check-in based on current hour (PT)"""
    # Get current PT time
    from datetime import datetime
    import pytz
    
    pt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pt)
    hour = now.hour
    
    if 6 <= hour < 9:
        return "morning", "🌅 Morning Check-In"
    elif 12 <= hour < 14:
        return "midday", "☀️ Midday Check-In"
    elif 16 <= hour < 18:
        return "afternoon", "🌤️ Afternoon Check-In"
    elif 20 <= hour < 22:
        return "evening", "🌙 Evening Check-In"
    else:
        return None, None

def generate_morning_update(calendar_data, whoop_data):
    """Generate morning update"""
    today = datetime.now().strftime('%A, %B %d')
    
    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; font-size: 24px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #34495e; font-size: 18px; margin-top: 25px; }}
.section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
.event {{ background: white; padding: 12px; margin: 10px 0; border-left: 4px solid #3498db; border-radius: 4px; }}
.travel {{ border-left-color: #e74c3c; }}
.restaurant {{ border-left-color: #f39c12; }}
.checklist {{ list-style: none; padding: 0; }}
.checklist li {{ padding: 5px 0; }}
.checklist li:before {{ content: "☐ "; color: #3498db; }}
.footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d; }}
</style>
</head>
<body>
<h1>🌅 Good Morning — {today}</h1>
"""
    
    # Health section
    if whoop_data and whoop_data.strip() != "No Whoop data available.":
        html += f"""
<div class="section">
<h2>💪 Yesterday's Health (Whoop)</h2>
<pre style="white-space: pre-wrap; font-family: inherit;">{whoop_data}</pre>
</div>
"""
    
    # Weight loss section
    html += """
<div class="section">
<h2>🎯 Weight Loss Focus</h2>
<ul class="checklist">
<li>Weigh-in (7 AM)</li>
<li>Log breakfast in Lose It!</li>
<li>Protein target: 150-180g</li>
<li>Workout complete</li>
<li>7+ hours sleep</li>
</ul>
<p><strong>This week:</strong> Aggressive phase (2 lbs/week) | Prioritize protein, no sugary drinks, daily movement</p>
</div>
"""
    
    # Calendar section
    if calendar_data:
        today_events = [e for e in calendar_data.get('events', []) 
                       if datetime.now().strftime('%A, %B %d') in e.get('start', '')]
        
        if today_events:
            html += "<div class='section'><h2>📅 Today's Schedule</h2>"
            for event in today_events:
                css_class = "event"
                if event.get('is_travel'):
                    css_class += " travel"
                elif any(kw in event.get('summary', '').lower() for kw in ['reservation', 'dinner', 'lunch']):
                    css_class += " restaurant"
                
                html += f"""
<div class="{css_class}">
<strong>{event['summary']}</strong><br>
🕐 {event['start']}<br>
{ f"📍 {event['location']}" if event.get('location') else "" }
</div>
"""
            html += "</div>"
        
        # Travel alerts
        travel = [e for e in calendar_data.get('events', []) if e.get('is_travel')][:3]
        if travel:
            html += "<div class='section'><h2>✈️ Upcoming Travel</h2>"
            for trip in travel:
                html += f"""
<div class="event travel">
<strong>{trip['summary']}</strong><br>
📆 {trip['start']}<br>
{ f"📍 {trip['location']}" if trip.get('location') else "" }
</div>
"""
            html += "</div>"
    
    html += """
<div class="section">
<h2>❓ Questions for Today</h2>
<ul>
<li>How did you sleep? (Check Whoop recovery above)</li>
<li>What's your main focus for work today?</li>
<li>Any obstacles I can help remove?</li>
<li>Dinner plans — cooking or eating out?</li>
</ul>
</div>

<div class="footer">
🏛️ Cicero | Your Digital Familiar<br>
<a href="mailto:[REDACTED]">Reply to this email</a> or message me directly.
</div>

</body>
</html>"""
    
    return html

def generate_midday_update(calendar_data):
    """Generate midday pulse check"""
    today = datetime.now().strftime('%A, %B %d')
    
    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; font-size: 24px; border-bottom: 2px solid #f39c12; padding-bottom: 10px; }}
.section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
</style>
</head>
<body>
<h1>☀️ Midday Check-In — {today}</h1>

<div class="section">
<h2>📊 Progress Pulse</h2>
<p>Halfway through the day. Quick check:</p>
<ul>
<li>How's the morning gone?</li>
<li>Any blockers I can help with?</li>
<li>Lunch plans sorted?</li>
<li>Energy level 1-10?</li>
</ul>
</div>

<div class="section">
<h2>⚡ Afternoon Preview</h2>
"""
    
    if calendar_data:
        today_events = [e for e in calendar_data.get('events', []) 
                       if datetime.now().strftime('%A, %B %d') in e.get('start', '')]
        afternoon_events = [e for e in today_events if 'PM' in e.get('start', '')]
        
        if afternoon_events:
            html += "<p>Coming up this afternoon:</p><ul>"
            for event in afternoon_events:
                html += f"<li><strong>{event['summary']}</strong> — {event['start']}</li>"
            html += "</ul>"
        else:
            html += "<p>No scheduled events this afternoon. Open calendar = opportunity to focus.</p>"
    
    html += """
</div>

<div class="footer" style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d;">
🏛️ Cicero | Your Digital Familiar
</div>

</body>
</html>"""
    
    return html

def generate_afternoon_update(calendar_data):
    """Generate afternoon wrap-up prep"""
    today = datetime.now().strftime('%A, %B %d')
    
    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; font-size: 24px; border-bottom: 2px solid #9b59b6; padding-bottom: 10px; }}
.section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
</style>
</head>
<body>
<h1>🌤️ Afternoon Check-In — {today}</h1>

<div class="section">
<h2>📝 Wrap-Up Prep</h2>
<p>Day's winding down. Time to think about:</p>
<ul>
<li>What got done today?</li>
<li>What rolls to tomorrow?</li>
<li>Any follow-ups needed before EOD?</li>
<li>Energy for evening activities?</li>
</ul>
</div>

<div class="section">
<h2>🍽️ Dinner Intel</h2>
<p>Need a restaurant recommendation? I can help with:</p>
<ul>
<li>Last-minute reservations</li>
<li>Neighborhood picks</li>
<li>Cuisine cravings</li>
<li>Group-friendly spots</li>
</ul>
</div>

<div class="footer" style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d;">
🏛️ Cicero | Your Digital Familiar
</div>

</body>
</html>"""
    
    return html

def generate_evening_update(calendar_data, whoop_data):
    """Generate evening review"""
    today = datetime.now().strftime('%A, %B %d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%A, %B %d')
    
    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; font-size: 24px; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
.section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
.event {{ background: white; padding: 12px; margin: 10px 0; border-left: 4px solid #3498db; border-radius: 4px; }}
</style>
</head>
<body>
<h1>🌙 Evening Check-In — {today}</h1>

<div class="section">
<h2>📋 Day Review</h2>
<p>Quick reflection:</p>
<ul>
<li>Win of the day?</li>
<li>One thing to improve tomorrow?</li>
<li>How's the energy level?</li>
</ul>
</div>
"""
    
    # Tomorrow preview
    html += f"""
<div class="section">
<h2>📅 Tomorrow ({tomorrow})</h2>
"""
    
    if calendar_data:
        tomorrow_events = [e for e in calendar_data.get('events', []) 
                          if tomorrow in e.get('start', '')]
        
        if tomorrow_events:
            for event in tomorrow_events:
                html += f"""
<div class="event">
<strong>{event['summary']}</strong><br>
🕐 {event['start']}
</div>
"""
        else:
            html += "<p>No events scheduled. Clean slate.</p>"
    
    html += "</div>"
    
    # Health reminder
    html += """
<div class="section">
<h2>💤 Sleep Prep</h2>
<ul>
<li>Wind down routine started?</li>
<li>Screens off 30 min before bed?</li>
<li>Tomorrow's clothes laid out?</li>
</ul>
<p>Sleep = recovery = performance. Prioritize it.</p>
</div>

<div class="footer" style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d;">
🏛️ Cicero | Your Digital Familiar<br>
Good night. See you in the morning.
</div>

</body>
</html>"""
    
    return html

def main():
    """Generate and send check-in email"""
    check_in_type, subject = get_check_in_type()
    
    if not check_in_type:
        print("Not a scheduled check-in time")
        sys.exit(0)
    
    # Load data
    calendar_data = load_calendar()
    whoop_data = load_whoop()
    
    # Generate appropriate update
    if check_in_type == "morning":
        body = generate_morning_update(calendar_data, whoop_data)
    elif check_in_type == "midday":
        body = generate_midday_update(calendar_data)
    elif check_in_type == "afternoon":
        body = generate_afternoon_update(calendar_data)
    else:  # evening
        body = generate_evening_update(calendar_data, whoop_data)
    
    # Send email
    success = send_email(RECIPIENTS, subject, body, html=True)
    
    if success:
        print(f"✅ {subject} sent successfully")
    else:
        print(f"❌ Failed to send {subject}")
        sys.exit(1)

if __name__ == "__main__":
    main()

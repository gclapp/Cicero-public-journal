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

def get_weather_for_location(location_name):
    """Get current weather and 2-day forecast for a location"""
    import subprocess
    import json
    
    # Map location names to wttr.in query
    location_map = {
        'Los Angeles, CA': 'Los+Angeles',
        'New York, NY': 'New+York',
        'Atlanta, GA': 'Atlanta',
        'Scottsdale, AZ': 'Scottsdale',
        'Portland, OR': 'Portland',
        'Santa Barbara, CA': 'Santa+Barbara'
    }
    
    query = location_map.get(location_name, 'Los+Angeles')
    
    try:
        # Get weather data in JSON format
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{query}?format=j1'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            current = data['current_condition'][0]
            forecast = data['weather']
            
            return {
                'current_temp': current['temp_F'],
                'current_condition': current['weatherDesc'][0]['value'],
                'humidity': current['humidity'],
                'wind': current['windspeedMiles'],
                'tomorrow_high': forecast[0]['maxtempF'],
                'tomorrow_low': forecast[0]['mintempF'],
                'tomorrow_condition': forecast[0]['hourly'][4]['weatherDesc'][0]['value'],  # midday
                'day2_high': forecast[1]['maxtempF'],
                'day2_low': forecast[1]['mintempF'],
                'day2_condition': forecast[1]['hourly'][4]['weatherDesc'][0]['value']
            }
    except Exception as e:
        print(f"Weather fetch error: {e}")
    
    return None

def get_location_and_weather():
    """Determine Geoff's location based on calendar and get weather"""
    import pytz
    from datetime import datetime
    
    pt = pytz.timezone('America/Los_Angeles')
    et = pytz.timezone('America/New_York')
    now = datetime.now(pt)
    
    # Default: Los Angeles
    location = "Los Angeles, CA"
    timezone = "PT (Pacific Time)"
    tz_obj = pt
    
    # Check calendar for travel
    calendar_data = load_calendar()
    if calendar_data:
        events = calendar_data.get('events', [])
        today_str = now.strftime('%A, %B %d')
        
        for event in events:
            event_start = event.get('start', '')
            # Check if event is today and is travel
            if today_str in event_start or now.strftime('%Y-%m-%d') in event_start:
                if event.get('is_travel'):
                    location_str = event.get('location', '').lower()
                    if 'new york' in location_str or 'jfk' in location_str or 'lga' in location_str or 'nyc' in location_str:
                        location = "New York, NY"
                        timezone = "ET (Eastern Time)"
                        tz_obj = et
                    elif 'atlanta' in location_str:
                        location = "Atlanta, GA"
                        timezone = "ET (Eastern Time)"
                        tz_obj = et
                    elif 'scottsdale' in location_str or 'phoenix' in location_str or 'arizona' in location_str:
                        location = "Scottsdale, AZ"
                        timezone = "MT (Mountain Time)"
                    elif 'portland' in location_str or 'oregon' in location_str:
                        location = "Portland, OR"
                        timezone = "PT (Pacific Time)"
                    elif 'santa barbara' in location_str:
                        location = "Santa Barbara, CA"
                        timezone = "PT (Pacific Time)"
                # Check for hotel stays
                elif 'stay at' in event.get('summary', '').lower():
                    location_str = event.get('location', '').lower()
                    if 'new york' in location_str:
                        location = "New York, NY"
                        timezone = "ET (Eastern Time)"
                        tz_obj = et
                    elif 'atlanta' in location_str:
                        location = "Atlanta, GA"
                        timezone = "ET (Eastern Time)"
                        tz_obj = et
                    elif 'scottsdale' in location_str or 'arizona' in location_str:
                        location = "Scottsdale, AZ"
                        timezone = "MT (Mountain Time)"
                    elif 'santa barbara' in location_str:
                        location = "Santa Barbara, CA"
                        timezone = "PT (Pacific Time)"
    
    # Get current time in detected timezone
    current_time = datetime.now(tz_obj).strftime('%I:%M %p')
    
    # Get weather for the location
    weather = get_weather_for_location(location)
    
    return {
        'location': location,
        'timezone': timezone,
        'current_time': current_time,
        'weather': weather
    }

def generate_morning_update(calendar_data, whoop_data):
    """Generate morning update"""
    today = datetime.now().strftime('%A, %B %d')
    
    # Get location and weather
    loc_data = get_location_and_weather()
    
    # Build weather HTML if available
    weather_html = ""
    if loc_data['weather']:
        w = loc_data['weather']
        weather_html = f"""
<div class="weather-grid">
<div class="weather-item">
<div style="font-size: 24px;">🌡️</div>
<div style="font-size: 20px; font-weight: bold;">{w['current_temp']}°F</div>
<div style="font-size: 12px;">Current</div>
<div style="font-size: 11px; opacity: 0.9;">{w['current_condition']}</div>
</div>
<div class="weather-item">
<div style="font-size: 24px;">💧</div>
<div style="font-size: 16px; font-weight: bold;">{w['humidity']}%</div>
<div style="font-size: 12px;">Humidity</div>
<div style="font-size: 11px; opacity: 0.9;">Wind {w['wind']} mph</div>
</div>
</div>
<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
<p style="margin: 5px 0; font-size: 13px;"><strong>Forecast:</strong></p>
<p style="margin: 3px 0; font-size: 12px;">Tomorrow: {w['tomorrow_high']}°F / {w['tomorrow_low']}°F — {w['tomorrow_condition']}</p>
<p style="margin: 3px 0; font-size: 12px;">Day after: {w['day2_high']}°F / {w['day2_low']}°F — {w['day2_condition']}</p>
</div>
"""
    
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
.location-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 15px 0; }}
.location-box h2 {{ color: white; margin-top: 0; }}
.weather-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }}
.weather-item {{ background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; text-align: center; }}
</style>
</head>
<body>
<h1>🌅 Good Morning — {today}</h1>

<div class="location-box">
<h2>📍 Where I Think You Are</h2>
<p style="font-size: 20px; margin: 10px 0;"><strong>{loc_data['location']}</strong></p>
<p style="margin: 5px 0;">🕐 Current time: {loc_data['current_time']} {loc_data['timezone']}</p>
<p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">(Based on your calendar)</p>
{weather_html}
</div>
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
    
    # Get location and weather
    loc_data = get_location_and_weather()
    
    # Build weather HTML if available
    weather_html = ""
    if loc_data['weather']:
        w = loc_data['weather']
        weather_html = f"""
<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
<p style="margin: 5px 0; font-size: 14px;">🌡️ {w['current_temp']}°F — {w['current_condition']}</p>
<p style="margin: 3px 0; font-size: 12px; opacity: 0.9;">Next 2 days: {w['tomorrow_high']}°/{w['tomorrow_low']}°F, {w['day2_high']}°/{w['day2_low']}°F</p>
</div>
"""
    
    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; font-size: 24px; border-bottom: 2px solid #f39c12; padding-bottom: 10px; }}
.section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
.location-box {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px; margin: 15px 0; }}
.location-box h2 {{ color: white; margin-top: 0; }}
</style>
</head>
<body>
<h1>☀️ Midday Check-In — {today}</h1>

<div class="location-box">
<h2>📍 Where I Think You Are</h2>
<p style="font-size: 20px; margin: 10px 0;"><strong>{loc_data['location']}</strong></p>
<p style="margin: 5px 0;">🕐 Current time: {loc_data['current_time']} {loc_data['timezone']}</p>
<p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">(Based on your calendar)</p>
{weather_html}
</div>

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
    
    # Get location and weather
    loc_data = get_location_and_weather()
    
    # Build weather HTML if available
    weather_html = ""
    if loc_data['weather']:
        w = loc_data['weather']
        weather_html = f"""
<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
<p style="margin: 5px 0; font-size: 14px;">🌡️ {w['current_temp']}°F — {w['current_condition']}</p>
<p style="margin: 3px 0; font-size: 12px; opacity: 0.9;">Next 2 days: {w['tomorrow_high']}°/{w['tomorrow_low']}°F, {w['day2_high']}°/{w['day2_low']}°F</p>
</div>
"""

    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; font-size: 24px; border-bottom: 2px solid #9b59b6; padding-bottom: 10px; }}
.section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
.location-box {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 8px; margin: 15px 0; }}
.location-box h2 {{ color: white; margin-top: 0; }}
</style>
</head>
<body>
<h1>🌤️ Afternoon Check-In — {today}</h1>

<div class="location-box">
<h2>📍 Where I Think You Are</h2>
<p style="font-size: 20px; margin: 10px 0;"><strong>{loc_data['location']}</strong></p>
<p style="margin: 5px 0;">🕐 Current time: {loc_data['current_time']} {loc_data['timezone']}</p>
<p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">(Based on your calendar)</p>
{weather_html}
</div>

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
    import pytz
    pt = pytz.timezone('America/Los_Angeles')
    now_pt = datetime.now(pt)
    today = now_pt.strftime('%A, %B %d')
    tomorrow = (now_pt + timedelta(days=1)).strftime('%A, %B %d')
    
    # Get location and weather
    loc_data = get_location_and_weather()
    
    # Build weather HTML if available
    weather_html = ""
    if loc_data['weather']:
        w = loc_data['weather']
        weather_html = f"""
<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
<p style="margin: 5px 0; font-size: 14px;">🌡️ {w['current_temp']}°F — {w['current_condition']}</p>
<p style="margin: 3px 0; font-size: 12px; opacity: 0.9;">Tomorrow: {w['tomorrow_high']}°/{w['tomorrow_low']}°F — {w['tomorrow_condition']}</p>
</div>
"""

    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; font-size: 24px; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
.section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
.event {{ background: white; padding: 12px; margin: 10px 0; border-left: 4px solid #3498db; border-radius: 4px; }}
.location-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 15px 0; }}
.location-box h2 {{ color: white; margin-top: 0; }}
</style>
</head>
<body>
<h1>🌙 Evening Check-In — {today}</h1>

<div class="location-box">
<h2>📍 Where I Think You Are</h2>
<p style="font-size: 20px; margin: 10px 0;"><strong>{loc_data['location']}</strong></p>
<p style="margin: 5px 0;">🕐 Current time: {loc_data['current_time']} {loc_data['timezone']}</p>
<p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">(Based on your calendar)</p>
{weather_html}
</div>

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
                          if tomorrow in e.get('start', '') or e.get('start', '').startswith(tomorrow.split(',')[0])]
        
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
    
    # Whoop data section (if available)
    if whoop_data and whoop_data.strip():
        html += f"""
<div class="section">
<h2>💪 Today's Health (Whoop)</h2>
<pre style="white-space: pre-wrap; font-family: inherit;">{whoop_data}</pre>
</div>
"""
    
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

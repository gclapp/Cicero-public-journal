#!/usr/bin/env python3
"""
Generate Morning Update Email (HTML) - v2 Standards
Matches the format locked in with Geoff on March 22, 2026
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

# File paths
CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
WHOOP_SUMMARY_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "whoop" / "latest-summary.txt"
WEIGHT_FILE = Path.home() / ".openclaw" / "workspace" / "memory" / "weight-loss-2026.md"
OUTPUT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "morning-update-email.html"

def get_weather_emoji(condition):
    """Convert weather condition to emoji"""
    condition = condition.lower()
    if 'sun' in condition or 'clear' in condition:
        return '☀️'
    elif 'cloud' in condition:
        return '☁️'
    elif 'rain' in condition:
        return '🌧️'
    elif 'snow' in condition:
        return '❄️'
    elif 'fog' in condition or 'mist' in condition:
        return '🌫️'
    else:
        return '🌤️'

def get_weather(location="Los Angeles"):
    """Get weather with emoji in Fahrenheit"""
    try:
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?u&format=%c+%f', '--max-time', '10'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout:
            # wttr.in returns "emoji +XX°F", clean it up
            weather = result.stdout.strip()
            # Remove the + sign if present
            weather = weather.replace('+', '')
            return weather
        return f"🌤️ --°F"
    except:
        return f"🌤️ --°F"

def get_todoist_tasks():
    """Get Todoist task count"""
    try:
        result = subprocess.run(['todoist', 'today'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            return len(lines)
        return "--"
    except:
        return "--"

def get_whoop_data():
    """Get latest Whoop recovery data"""
    if WHOOP_SUMMARY_FILE.exists():
        try:
            with open(WHOOP_SUMMARY_FILE, 'r') as f:
                content = f.read()
                # Parse recovery percentage
                for line in content.split('\n'):
                    if 'Recovery:' in line or 'recovery' in line.lower():
                        import re
                        match = re.search(r'(\d+)%', line)
                        if match:
                            return int(match.group(1))
        except:
            pass
    return None

def get_latest_weight():
    """Get latest weight from tracker"""
    if WEIGHT_FILE.exists():
        try:
            with open(WEIGHT_FILE, 'r') as f:
                content = f.read()
                # Look for latest weight entry
                import re
                matches = re.findall(r'\*\*(\d{3}\.\d)\*\*', content)
                if matches:
                    return float(matches[0])
        except:
            pass
    return None

def get_calendar_data():
    """Get calendar events"""
    if not CALENDAR_FILE.exists():
        return [], []
    
    try:
        with open(CALENDAR_FILE, 'r') as f:
            data = json.load(f)
        
        today = datetime.now().strftime('%A, %B %d')
        today_events = []
        travel_events = []
        week_events = []
        
        for event in data.get('events', []):
            event_date = event.get('start', '')
            if today in event_date:
                today_events.append(event)
            if event.get('is_travel'):
                travel_events.append(event)
            # Collect next 7 days
            week_events.append(event)
        
        return today_events, travel_events, week_events
    except:
        return [], [], []

def detect_location_and_travel(calendar_events):
    """Detect current location and upcoming travel"""
    utc_now = datetime.now(timezone.utc)
    pt_offset = timedelta(hours=-7)
    et_offset = timedelta(hours=-4)
    
    now_pt = utc_now + pt_offset
    now_et = utc_now + et_offset
    
    location = "Los Angeles"
    timezone_str = "PT"
    status = "Home"
    upcoming_flight = None
    
    today_str = now_pt.strftime('%A, %B %d')
    
    for event in calendar_events:
        if not event.get('is_travel'):
            continue
            
        summary = event.get('summary', '').lower()
        event_date = event.get('start', '')
        is_today = today_str in event_date
        
        # Flight detection
        if 'flight' in summary:
            if 'jfk' in summary or 'new york' in summary or 'lga' in summary:
                if is_today:
                    upcoming_flight = {
                        'route': 'LAX → JFK',
                        'time': event.get('start', 'TBD'),
                        'type': 'departure'
                    }
                    status = "Traveling to NYC"
                location = "New York City"
                timezone_str = "ET"
            elif 'lax' in summary or 'los angeles' in summary:
                if is_today:
                    upcoming_flight = {
                        'route': '→ LAX',
                        'time': event.get('start', 'TBD'),
                        'type': 'arrival'
                    }
                    status = "Returning to LA"
    
    return {
        'city': location,
        'state': 'CA' if location == 'Los Angeles' else 'NY',
        'timezone': timezone_str,
        'status': status,
        'pt_time': now_pt.strftime('%I:%M %p'),
        'et_time': now_et.strftime('%I:%M %p'),
        'upcoming_flight': upcoming_flight
    }

def generate_html_update():
    """Generate HTML morning update"""
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    today_events, travel_events, week_events = get_calendar_data()
    location_info = detect_location_and_travel(travel_events)
    
    # Get data
    la_weather = get_weather("Los Angeles")
    nyc_weather = get_weather("New York")
    todoist_count = get_todoist_tasks()
    whoop_recovery = get_whoop_data()
    latest_weight = get_latest_weight()
    
    # Whoop status color
    whoop_color = "#16a34a"  # green
    whoop_status = "Good"
    if whoop_recovery:
        if whoop_recovery < 50:
            whoop_color = "#dc2626"  # red
            whoop_status = "Low"
        elif whoop_recovery < 70:
            whoop_color = "#ea580c"  # orange
            whoop_status = "Moderate"
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .location {{ background: #dbeafe; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; color: #1e40af; }}
        .section {{ margin: 20px 0; padding: 20px; border-left: 4px solid #3b82f6; background: #f8fafc; }}
        .section h2 {{ margin-top: 0; color: #1e40af; }}
        .weather {{ display: flex; justify-content: space-around; background: #f3f4f6; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .weather-city {{ text-align: center; }}
        .weather-temp {{ font-size: 24px; font-weight: bold; }}
        .travel-alert {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0; }}
        .travel-alert h3 {{ margin-top: 0; color: #b45309; }}
        .flight {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #e5e7eb; }}
        .flight-time {{ font-size: 24px; font-weight: bold; color: #1e40af; }}
        .hotel {{ background: #f0fdf4; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #16a34a; }}
        .stats {{ display: flex; justify-content: space-around; background: #eff6ff; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ font-size: 11px; color: #666; }}
        .week-view {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #e5e7eb; }}
        .day {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
        .day:last-child {{ border-bottom: none; }}
        .day-date {{ font-weight: bold; color: #1e40af; }}
        .flight-badge {{ display: inline-block; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-left: 10px; }}
        .early-flight {{ background: #fef2f2; color: #dc2626; }}
        .checklist {{ list-style: none; padding: 0; }}
        .checklist li {{ padding: 8px 0; padding-left: 30px; position: relative; }}
        .checklist li:before {{ content: "☐"; position: absolute; left: 0; color: #3b82f6; font-size: 18px; }}
        .footer {{ background: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #666; margin-top: 30px; }}
        .success {{ color: #16a34a; font-weight: bold; }}
        .warning {{ color: #ea580c; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #1e40af; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
        a {{ color: #3b82f6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>☀️ Good Morning!</h1>
        <p>{today}</p>
    </div>

    <div class="location">
        📍 {location_info['city']}, {location_info['state']} — {location_info['status']}
    </div>

    <div class="weather">
        <div class="weather-city">
            <div class="weather-temp">{la_weather}</div>
            <div>Los Angeles</div>
        </div>
        <div class="weather-city">
            <div class="weather-temp">{nyc_weather}</div>
            <div>New York</div>
        </div>
    </div>
'''
    
    # Add travel alert if there's a flight today
    if location_info.get('upcoming_flight'):
        flight = location_info['upcoming_flight']
        html += f'''
    <div class="travel-alert">
        <h3>✈️ TODAY'S TRAVEL</h3>
        <div class="flight">
            <div class="flight-time">{flight['time']}</div>
            <p><strong>{flight['route']}</strong></p>
        </div>
    </div>
'''
    
    # Stats section
    html += f'''
    <div class="section">
        <h2>📊 At a Glance</h2>
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{todoist_count}</div>
                <div class="stat-label">TODOIST TASKS</div>
            </div>
            <div class="stat">
                <div class="stat-number" style="color: {whoop_color};">{whoop_recovery if whoop_recovery else '--'}%</div>
                <div class="stat-label">WHOOP RECOVERY</div>
            </div>
            <div class="stat">
                <div class="stat-number">{latest_weight if latest_weight else '--'}</div>
                <div class="stat-label">LBS</div>
            </div>
        </div>
    </div>
'''
    
    # Calendar section
    html += '''
    <div class="section">
        <h2>📅 This Week</h2>
        <div class="week-view">
'''
    
    # Show next 7 days
    for i in range(7):
        day = datetime.now() + timedelta(days=i)
        day_str = day.strftime('%A, %B %d')
        day_events = [e for e in week_events if day_str in e.get('start', '')]
        
        html += f'''            <div class="day">
                <span class="day-date">{day_str}</span>
'''
        
        for event in day_events[:2]:  # Show first 2 events
            if event.get('is_travel'):
                html += f'''                <span class="flight-badge">✈️ TRAVEL</span>
                <p>{event['summary']}</p>
'''
            else:
                html += f'''                <p>📅 {event['summary']}</p>
'''
        
        html += '''            </div>
'''
    
    html += '''        </div>
    </div>
'''
    
    # Health section
    html += f'''
    <div class="section">
        <h2>💓 Health</h2>
        <p><strong>Dashboard:</strong> <a href="https://gclapp.github.io/health-dashboard/">https://gclapp.github.io/health-dashboard/</a></p>
        <p><strong>Whoop:</strong> <span style="color: {whoop_color};">{whoop_recovery}% recovery</span> ({whoop_status})</p>
        <p><strong>Latest weight:</strong> {latest_weight if latest_weight else '--'} lbs</p>
    </div>
'''
    
    # Footer
    html += f'''
    <div class="footer">
        <p>🏛️ Cicero | All systems operational</p>
        <p>Last updated: {datetime.now().strftime('%B %d, %Y %I:%M %p PT')}</p>
    </div>
</body>
</html>
'''
    
    return html

def main():
    """Generate and save morning update"""
    html = generate_html_update()
    
    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)
    
    print(f"✅ Morning update generated: {OUTPUT_FILE}")
    return html

if __name__ == "__main__":
    main()

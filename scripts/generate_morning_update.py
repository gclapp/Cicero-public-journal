#!/usr/bin/env python3
"""
Generate Morning Update - MANDATORY SECTIONS
Includes: Weather, Todoist, Health, Calendar - NO EXCEPTIONS
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

# File paths
CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
WHOOP_SUMMARY_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "whoop" / "latest-summary.txt"
OUTPUT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "morning-update.txt"

def get_weather(location="Los Angeles"):
    """Get weather - MANDATORY"""
    try:
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%l:+%c+%t+%h+%w', '--max-time', '10'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout and 'Unknown' not in result.stdout:
            return result.stdout.strip()
        return f"{location}: Weather data unavailable"
    except:
        return f"{location}: Weather service error"

def get_todoist_tasks():
    """Get Todoist task count - MANDATORY"""
    try:
        result = subprocess.run(['todoist', 'today'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            return len(lines)
        return "Error"
    except:
        return "Unavailable"

def get_health_status():
    """Get health dashboard status - MANDATORY"""
    dashboard_url = "https://gclapp.github.io/health-dashboard/"
    
    # Check if Whoop data exists
    whoop_status = "Not available"
    if WHOOP_SUMMARY_FILE.exists():
        try:
            with open(WHOOP_SUMMARY_FILE, 'r') as f:
                content = f.read()
                if content and "No Whoop data" not in content:
                    whoop_status = "Data available"
        except:
            pass
    
    return {
        'dashboard_url': dashboard_url,
        'whoop_status': whoop_status
    }

def get_calendar_summary():
    """Get calendar summary - MANDATORY"""
    if not CALENDAR_FILE.exists():
        return None, []
    
    try:
        with open(CALENDAR_FILE, 'r') as f:
            data = json.load(f)
        
        today = datetime.now().strftime('%A, %B %d')
        today_events = []
        travel_events = []
        
        for event in data.get('events', []):
            if today in event.get('start', ''):
                today_events.append(event)
            if event.get('is_travel'):
                travel_events.append(event)
        
        return today_events, travel_events
    except:
        return None, []

def get_destination_weather(travel_events):
    """Get weather for travel destinations"""
    destinations = []
    for event in travel_events[:3]:  # Check first 3 travel events
        location = event.get('location', '').lower()
        summary = event.get('summary', '').lower()
        
        # Extract city from location or summary
        if 'new york' in location or 'jfk' in location or 'nyc' in summary:
            destinations.append(('New York', 'New+York'))
        elif 'santa barbara' in location:
            destinations.append(('Santa Barbara', 'Santa+Barbara'))
        elif 'scottsdale' in location or 'phoenix' in location:
            destinations.append(('Scottsdale', 'Scottsdale'))
        elif 'portland' in location:
            destinations.append(('Portland', 'Portland'))
    
    weather_reports = []
    for city_name, city_code in destinations:
        weather = get_weather(city_code)
        weather_reports.append(f"{city_name}: {weather}")
    
    return weather_reports

def detect_current_location(calendar_events):
    """Detect Geoff's current location from calendar and time"""
    from datetime import datetime, timezone, timedelta
    
    # Manual timezone offsets (UTC-7 for PT, UTC-4 for ET during DST)
    utc_now = datetime.now(timezone.utc)
    pt_offset = timedelta(hours=-7)
    et_offset = timedelta(hours=-4)
    
    now_pt = utc_now + pt_offset
    now_et = utc_now + et_offset
    now_utc = utc_now
    current_hour_pt = now_pt.hour
    
    # Default: Los Angeles (home base)
    location = "Los Angeles"
    timezone = "PT"
    status = "Home"
    
    # Look for today's flights first
    today_str = now_pt.strftime('%A, %B %d')
    
    for event in calendar_events:
        if not event.get('is_travel'):
            continue
            
        summary = event.get('summary', '').lower()
        location_str = event.get('location', '').lower()
        event_date = event.get('start', '')
        
        # Check if flight is today
        is_today = today_str in event_date
        
        # Flight to NYC (JFK/LGA/EWR)
        if 'flight' in summary and ('jfk' in summary or 'new york' in summary or 'lga' in summary or 'ewr' in summary):
            if is_today:
                # Flight to NYC today - check if departed or arrived
                # Assume flight is ~6 hours, if it's afternoon PT, likely arrived
                if current_hour_pt >= 14:  # After 2 PM PT
                    location = "New York City"
                    timezone = "ET"
                    status = "Arrived"
                else:
                    status = "Flying to NYC"
            else:
                # Flight was on a previous day - still in NYC
                location = "New York City"
                timezone = "ET"
                status = "In NYC"
                
        # Flight to LA (LAX/BUR)
        elif 'flight' in summary and ('lax' in summary or 'los angeles' in summary or 'bur' in summary):
            if is_today:
                # Flight to LA today
                if current_hour_pt >= 20:  # After 8 PM PT
                    location = "Los Angeles"
                    timezone = "PT"
                    status = "Arrived"
                else:
                    location = "In Transit"
                    timezone = "PT"
                    status = "Flying to LA"
            else:
                location = "Los Angeles"
                timezone = "PT"
                status = "Home"
    
    # Check for hotel stays as backup indicator
    for event in calendar_events:
        summary = event.get('summary', '').lower()
        if 'hotel' in summary or 'stay at' in summary:
            if 'new york' in summary or 'westin' in summary or 'algonquin' in summary:
                if location == "Los Angeles":  # Only override if not already set by flight
                    location = "New York City"
                    timezone = "ET"
            elif 'santa barbara' in summary:
                location = "Santa Barbara"
                timezone = "PT"
    
    return {
        'city': location,
        'timezone': timezone,
        'status': status,
        'pt_time': now_pt.strftime('%I:%M %p'),
        'et_time': now_et.strftime('%I:%M %p'),
        'utc_time': now_utc.strftime('%H:%M UTC')
    }

def generate_morning_update():
    """Generate morning update with ALL MANDATORY sections"""
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    # 4. CALENDAR (MANDATORY) - Get first for location detection
    today_events, travel_events = get_calendar_summary()
    
    # Detect current location
    location_info = detect_current_location(travel_events)
    
    # 1. WEATHER (MANDATORY) - Get weather for current location + LA
    current_weather = get_weather(location_info['city'])
    la_weather = get_weather("Los Angeles")
    
    # 2. TODOIST (MANDATORY)
    todoist_count = get_todoist_tasks()
    
    # 3. HEALTH (MANDATORY)
    health = get_health_status()
    
    # Get destination weather if traveling
    destination_weather = []
    if travel_events:
        destination_weather = get_destination_weather(travel_events)
    
    # Build update
    update = f"""# ☀️ Good Morning! — {today}

## 📍 CURRENT LOCATION
**City:** {location_info['city']}
**Time:** {location_info['pt_time']} PT | {location_info['et_time']} ET | {location_info['utc_time']}

## 🌤️ WEATHER
**{location_info['city']}:** {current_weather}
**Los Angeles:** {la_weather}
"""
    
    # Add destination weather if traveling
    if destination_weather:
        update += "\n**Travel Destinations:**\n"
        for dw in destination_weather:
            update += f"- {dw}\n"
    
    update += f"""
## ✅ TODOIST
**{todoist_count} tasks** pending for today

## 💓 HEALTH
**Dashboard:** {health['dashboard_url']}
**Whoop Status:** {health['whoop_status']}

## 📅 CALENDAR
"""
    
    # Add today's events
    if today_events:
        update += "**Today's Events:**\n"
        for event in today_events[:5]:  # Show first 5
            emoji = "✈️" if event.get('is_travel') else "📅"
            update += f"{emoji} {event['summary']}\n"
            update += f"   🕐 {event['start']}\n"
            if event.get('location'):
                update += f"   📍 {event['location']}\n"
    else:
        update += "No events scheduled for today.\n"
    
    # Add travel alerts
    if travel_events:
        update += "\n**✈️ Upcoming Travel:**\n"
        for trip in travel_events[:3]:
            update += f"- {trip['summary']} ({trip['start']})\n"
    
    update += """
---
🏛️ Cicero | All systems operational
"""
    
    return update

def main():
    """Generate and save morning update"""
    update = generate_morning_update()
    print(update)
    
    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(update)
    
    print(f"\n💾 Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

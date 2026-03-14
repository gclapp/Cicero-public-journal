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

def generate_morning_update():
    """Generate morning update with ALL MANDATORY sections"""
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    # 1. WEATHER (MANDATORY)
    la_weather = get_weather("Los Angeles")
    
    # 2. TODOIST (MANDATORY)
    todoist_count = get_todoist_tasks()
    
    # 3. HEALTH (MANDATORY)
    health = get_health_status()
    
    # 4. CALENDAR (MANDATORY)
    today_events, travel_events = get_calendar_summary()
    
    # Get destination weather if traveling
    destination_weather = []
    if travel_events:
        destination_weather = get_destination_weather(travel_events)
    
    # Build update
    update = f"""# ☀️ Good Morning! — {today}

## 🌤️ WEATHER
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

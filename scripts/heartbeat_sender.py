#!/usr/bin/env python3
"""
heartbeat_sender.py - Sends scheduled check-ins (HTML format)
Called by heartbeat-check.sh when a check-in is due
Uses the format locked on March 22, 2026
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime, timedelta
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

def get_weather(location="Los Angeles"):
    """Get weather with emoji in Fahrenheit"""
    try:
        # Get emoji and temperature separately
        emoji_result = subprocess.run(
            ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%c', '--max-time', '10'],
            capture_output=True, text=True, timeout=15
        )
        temp_result = subprocess.run(
            ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%t', '--max-time', '10'],
            capture_output=True, text=True, timeout=15
        )
        
        if emoji_result.returncode == 0 and temp_result.returncode == 0:
            emoji = emoji_result.stdout.strip()
            temp_str = temp_result.stdout.strip()
            
            # Parse Celsius temperature and convert to Fahrenheit
            # temp_str format: "+11°C" or "-5°C"
            temp_c = 0
            try:
                # Extract numeric part
                temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-' or c == '+'])
                temp_c = int(temp_num)
            except:
                pass
            
            # Convert to Fahrenheit: F = (C × 9/5) + 32
            temp_f = int((temp_c * 9/5) + 32)
            
            return f"{emoji} {temp_f}°F"
        
        return f"🌤️ --°F"
    except:
        return f"🌤️ --°F"

def get_todoist_count():
    """Get Todoist task count"""
    try:
        result = subprocess.run(['todoist', 'today'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            return len(lines)
        return "--"
    except:
        return "--"

def get_stock_summary():
    """Get stock summary for watchlist"""
    try:
        result = subprocess.run(
            ['python3', '/home/ubuntu/.openclaw/workspace/scripts/fetch_stock_data.py', '--summary'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "Stock data unavailable"
    except:
        return "Stock data unavailable"

def get_custody_status(pt_now, calendar_events=None):
    """Determine if Geoff has the kids based on custody schedule and calendar events"""
    # First check calendar for pickup/dropoff events
    if calendar_events:
        today_str = pt_now.strftime('%A, %B %d')
        for event in calendar_events:
            event_date = event.get('start', '')
            summary = event.get('summary', '').lower()
            
            # Check for pickup events today
            if today_str in event_date:
                if any(word in summary for word in ['pick up', 'pickup', 'get oliver', 'get sophie', 'chaparral']):
                    return True, "Picked up Oliver & Sophie today"
                if any(word in summary for word in ['drop off', 'dropoff', 'stacey']):
                    return False, "Dropped off kids today"
    
    # Fallback to standard custody schedule: Pick up Thursday 1:50 PM, drop off Saturday 5:00 PM
    weekday = pt_now.weekday()  # 0=Monday, 3=Thursday, 5=Saturday
    hour = pt_now.hour
    
    # Thursday after 1:50 PM = has kids
    if weekday == 3 and hour >= 14:
        return True, "With Oliver & Sophie (custody weekend)"
    
    # Friday = has kids
    if weekday == 4:
        return True, "With Oliver & Sophie (custody weekend)"
    
    # Saturday before 5:00 PM = has kids
    if weekday == 5 and hour < 17:
        return True, "With Oliver & Sophie (custody weekend)"
    
    # All other times = no kids
    return False, "Home (solo)"

def validate_whoop_token():
    """Check if Whoop token is valid by making a test API call"""
    try:
        import requests
        token_file = Path.home() / '.whoop_token'
        if not token_file.exists():
            return False
        
        token = token_file.read_text().strip()
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            'https://api.prod.whoop.com/developer/v2/recovery',
            headers=headers,
            params={'limit': 1},
            timeout=10
        )
        
        return response.status_code == 200
    except:
        return False

def run_token_health_check():
    """Run token health check and return summary"""
    try:
        result = subprocess.run(
            ['python3', '/home/ubuntu/.openclaw/workspace/scripts/token_health_check.py'],
            capture_output=True, text=True, timeout=30
        )
        # Parse the output for critical issues
        output = result.stdout
        
        # Count only the status emojis (not the header emoji)
        # Look for patterns like "🔴 Whoop" or "✅ Calendar"
        lines = output.split('\n')
        critical_count = 0
        warning_count = 0
        healthy_count = 0
        
        for line in lines:
            # Skip header lines and summary lines
            if 'Token Health Check' in line or 'CRITICAL' in line or 'Immediate action' in line:
                continue
            # Count status emojis in actual status lines
            if line.strip().startswith('🔴'):
                critical_count += 1
            elif line.strip().startswith('🟡') or line.strip().startswith('⚠️'):
                warning_count += 1
            elif line.strip().startswith('✅'):
                healthy_count += 1
        
        if critical_count > 0:
            return f"🔴 {critical_count} critical token issue{'s' if critical_count > 1 else ''}"
        elif warning_count > 0:
            return f"🟡 {warning_count} token warning{'s' if warning_count > 1 else ''}"
        else:
            return "✅ All tokens healthy"
    except Exception as e:
        return f"⚠️ Token check failed: {str(e)}"

def get_whoop_recovery():
    """Get latest Whoop recovery - only if token is valid"""
    # First check if token is valid
    if not validate_whoop_token():
        return None
    
    whoop_file = Path("/home/ubuntu/.openclaw/workspace/data/whoop/latest-summary.txt")
    if whoop_file.exists():
        try:
            with open(whoop_file, 'r') as f:
                content = f.read()
                import re
                match = re.search(r'(\d+)%', content)
                if match:
                    return int(match.group(1))
        except:
            pass
    return None

def get_latest_weight():
    """Get latest weight from tracker - parse from table"""
    weight_file = Path("/home/ubuntu/.openclaw/workspace/memory/weight-loss-2026.md")
    if weight_file.exists():
        try:
            with open(weight_file, 'r') as f:
                content = f.read()
            import re
            # Look for weight table entries: | Mar 22 | 237.0 | ...
            # Pattern: | Date | Weight | ...
            table_rows = re.findall(r'\|\s*(\w{3,4}\s+\d{1,2})\s*\|\s*(\d{3}(?:\.\d)?)\s*\|', content)
            if table_rows:
                # Get the last (most recent) entry
                latest = table_rows[-1]
                return float(latest[1]), table_rows  # Return all rows for trend analysis
        except Exception as e:
            print(f"Error parsing weight: {e}")
            pass
    return None, []

def get_weight_trend():
    """Analyze weight trend from history"""
    weight_file = Path("/home/ubuntu/.openclaw/workspace/memory/weight-loss-2026.md")
    if not weight_file.exists():
        return None
    
    try:
        with open(weight_file, 'r') as f:
            content = f.read()
        import re
        table_rows = re.findall(r'\|\s*(\w{3,4}\s+\d{1,2})\s*\|\s*(\d{3}(?:\.\d)?)\s*\|\s*([\+\-]?\d+\.?\d*)?\s*\|', content)
        
        if len(table_rows) < 2:
            return None
        
        # Get first and last weights
        start_weight = float(table_rows[0][1])
        latest_weight = float(table_rows[-1][1])
        total_lost = start_weight - latest_weight
        
        # Calculate 7-day trend if we have enough data
        week_trend = None
        if len(table_rows) >= 7:
            week_ago = float(table_rows[-7][1])
            week_trend = week_ago - latest_weight
        
        # Calculate pace
        # Estimate weeks since start (approximate from row count)
        weeks = len(table_rows) / 7  # Rough estimate
        if weeks > 0:
            pace = total_lost / weeks
        else:
            pace = 0
        
        return {
            'start': start_weight,
            'current': latest_weight,
            'total_lost': total_lost,
            'week_trend': week_trend,
            'pace': pace,
            'goal': 20,  # 20 lb goal
            'remaining': 20 - total_lost,
            'entries': len(table_rows)
        }
    except Exception as e:
        print(f"Error calculating weight trend: {e}")
        return None

def get_whoop_trend():
    """Get Whoop recovery trend from recent data"""
    whoop_dir = Path("/home/ubuntu/.openclaw/workspace/data/whoop")
    if not whoop_dir.exists():
        return None
    
    try:
        # Get all JSON files sorted by date
        json_files = sorted(whoop_dir.glob("whoop-*.json"))
        
        recovery_data = []
        for f in json_files[-7:]:  # Last 7 days
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    date = data.get('date', '')
                    recovery_list = data.get('recovery', [])
                    if recovery_list and len(recovery_list) > 0:
                        score = recovery_list[0].get('score')
                        if score:
                            recovery_data.append({'date': date, 'score': score})
            except:
                continue
        
        if not recovery_data:
            return None
        
        # Calculate trend
        scores = [d['score'] for d in recovery_data if d['score']]
        if not scores:
            return None
        
        avg_recovery = sum(scores) / len(scores)
        latest = scores[-1] if scores else 0
        
        # Trend direction
        if len(scores) >= 3:
            trend = "improving" if scores[-1] > scores[-3] else "declining" if scores[-1] < scores[-3] else "stable"
        else:
            trend = "unknown"
        
        return {
            'latest': latest,
            'average': round(avg_recovery, 1),
            'trend': trend,
            'days_tracked': len(scores),
            'data': recovery_data
        }
    except Exception as e:
        print(f"Error getting Whoop trend: {e}")
        return None

def generate_health_recommendations(weight_trend, whoop_trend, checkin_type):
    """Generate actionable health recommendations based on trends"""
    recommendations = []
    
    # Weight recommendations
    if weight_trend:
        if weight_trend['pace'] < 1.0:
            recommendations.append({
                'priority': 'high',
                'category': 'Weight Loss',
                'action': 'Increase daily protein to 180g and reduce carbs to 20%',
                'why': f'Current pace ({weight_trend["pace"]:.1f} lbs/week) is below target (1.5-2.0 lbs/week)'
            })
        
        if weight_trend['remaining'] > 15:
            recommendations.append({
                'priority': 'medium',
                'category': 'Weight Loss',
                'action': 'Add 10-min morning walk before breakfast',
                'why': f'{weight_trend["remaining"]:.1f} lbs remaining — small daily habits compound'
            })
    
    # Whoop/Sleep recommendations
    if whoop_trend:
        if whoop_trend['latest'] < 50:
            recommendations.append({
                'priority': 'high',
                'category': 'Recovery',
                'action': 'Prioritize 8+ hours sleep tonight — skip evening screen time',
                'why': f'Recovery at {whoop_trend["latest"]}% — body needs rest'
            })
        elif whoop_trend['latest'] < 70:
            recommendations.append({
                'priority': 'medium',
                'category': 'Recovery',
                'action': 'Light activity only today — walking, stretching, no intense workout',
                'why': f'Moderate recovery ({whoop_trend["latest"]}%) — avoid overtraining'
            })
        
        if whoop_trend['trend'] == 'declining':
            recommendations.append({
                'priority': 'high',
                'category': 'Sleep',
                'action': 'Review sleep hygiene — consistent bedtime, cool room, no alcohol',
                'why': 'Recovery trend declining over past 3 days'
            })
    else:
        # Whoop token issue
        recommendations.append({
            'priority': 'high',
            'category': 'Setup',
            'action': 'Re-authorize Whoop connection — token expired',
            'why': 'No recovery data available — need fresh OAuth token'
        })
    
    # Time-of-day specific recommendations
    if checkin_type == 'morning':
        recommendations.append({
            'priority': 'medium',
            'category': 'Morning Routine',
            'action': 'Weigh-in, check Whoop, drink 16oz water, log breakfast in Lose It!',
            'why': 'Consistent morning habits drive daily success'
        })
    elif checkin_type == 'evening':
        recommendations.append({
            'priority': 'medium',
            'category': 'Evening Routine',
            'action': 'Log dinner, review tomorrow\'s schedule, set bedtime alarm',
            'why': 'Preparation prevents poor evening decisions'
        })
    
    return recommendations

def get_system_status():
    """Get system health status"""
    status = {
        'calendar': 'Unknown',
        'whoop': 'Unknown',
        'email': 'Unknown',
        'cron_jobs': []
    }
    
    # Check token health
    token_file = Path("/home/ubuntu/.openclaw/workspace/logs/token-health.json")
    if token_file.exists():
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                for result in data.get('results', []):
                    message = result.get('message', '')
                    is_healthy = result.get('status') == 'healthy'
                    if 'Google Calendar' in message:
                        status['calendar'] = '✅ Healthy' if is_healthy else '❌ Issue'
                    elif 'Whoop API' in message and 'Refresh' not in message:
                        status['whoop'] = '✅ Healthy' if is_healthy else '❌ Issue'
                    elif 'Gmail' in message:
                        status['email'] = '✅ Healthy' if is_healthy else '❌ Issue'
        except:
            pass
    
    # Check cron jobs
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            cron_lines = result.stdout.strip().split('\n')
            active_jobs = []
            for line in cron_lines:
                if line.strip() and not line.startswith('#'):
                    if 'heartbeat' in line:
                        active_jobs.append('Heartbeat')
                    elif 'competitor' in line:
                        active_jobs.append('Competitive Intel')
                    elif 'whoop' in line:
                        active_jobs.append('Whoop Fetch')
                    elif 'calendar' in line:
                        active_jobs.append('Calendar Sync')
            status['cron_jobs'] = active_jobs if active_jobs else ['None found']
    except:
        status['cron_jobs'] = ['Error checking']
    
    return status

def get_calendar_data():
    """Get calendar events"""
    calendar_file = Path("/home/ubuntu/.openclaw/workspace/config/calendar-events.json")
    if not calendar_file.exists():
        return [], []
    
    try:
        with open(calendar_file, 'r') as f:
            data = json.load(f)
        
        today = datetime.now().strftime('%A, %B %d')
        today_events = []
        travel_events = []
        
        for event in data.get('events', []):
            event_date = event.get('start', '')
            if today in event_date:
                today_events.append(event)
            if event.get('is_travel'):
                travel_events.append(event)
        
        return today_events, travel_events
    except:
        return [], []

def detect_location_and_travel(calendar_events):
    """Detect current location and upcoming travel - includes custody status"""
    pt_now = get_pt_time()
    today_str = pt_now.strftime('%A, %B %d')
    
    # Default: Home in Calabasas/LA
    location = "Calabasas"
    state = "CA"
    status = "Home"
    upcoming_flight = None
    has_travel_today = False
    
    # Check for travel events today
    for event in calendar_events:
        if not event.get('is_travel'):
            continue
            
        summary = event.get('summary', '').lower()
        event_date = event.get('start', '')
        is_today = today_str in event_date
        
        if 'flight' in summary:
            if is_today:
                has_travel_today = True
                if 'jfk' in summary or 'new york' in summary or 'lga' in summary:
                    upcoming_flight = {
                        'route': 'LAX → JFK',
                        'time': event.get('start', 'TBD'),
                        'type': 'departure'
                    }
                    status = "Traveling to NYC"
                    location = "New York City"
                    state = "NY"
                elif 'lax' in summary or 'los angeles' in summary:
                    upcoming_flight = {
                        'route': '→ LAX',
                        'time': event.get('start', 'TBD'),
                        'type': 'arrival'
                    }
                    status = "Returning to LA"
                    location = "Los Angeles"
                    state = "CA"
                elif 'sfo' in summary or 'san francisco' in summary:
                    upcoming_flight = {
                        'route': '→ SFO',
                        'time': event.get('start', 'TBD'),
                        'type': 'arrival'
                    }
                    status = "Traveling to SF"
                    location = "San Francisco"
                    state = "CA"
    
    # If no travel today, check custody schedule (using calendar events if available)
    if not has_travel_today:
        has_kids, custody_status = get_custody_status(pt_now, calendar_events)
        if has_kids:
            status = custody_status
        else:
            status = "Home (solo)"
    
    return {
        'city': location,
        'state': state,
        'status': status,
        'upcoming_flight': upcoming_flight,
        'has_kids': get_custody_status(pt_now, calendar_events)[0]
    }

def get_week_travel_destinations(all_events, pt_now):
    """Get list of cities being traveled to in the next 7 days"""
    destinations = []
    
    for i in range(7):
        day = pt_now + timedelta(days=i)
        day_str = day.strftime('%A, %B %d')
        
        for event in all_events:
            if not event.get('is_travel'):
                continue
            
            event_date = event.get('start', '')
            if day_str not in event_date:
                continue
            
            summary = event.get('summary', '').lower()
            location = event.get('location', '').lower()
            
            # Detect destination city
            if 'jfk' in summary or 'new york' in summary or 'lga' in summary or 'nyc' in location:
                if 'New York' not in [d['name'] for d in destinations]:
                    destinations.append({'name': 'New York', 'code': 'New+York'})
            elif 'lax' in summary or 'los angeles' in summary:
                if 'Los Angeles' not in [d['name'] for d in destinations]:
                    destinations.append({'name': 'Los Angeles', 'code': 'Los+Angeles'})
            elif 'atl' in summary or 'atlanta' in summary:
                if 'Atlanta' not in [d['name'] for d in destinations]:
                    destinations.append({'name': 'Atlanta', 'code': 'Atlanta'})
            elif 'sfo' in summary or 'san francisco' in summary:
                if 'San Francisco' not in [d['name'] for d in destinations]:
                    destinations.append({'name': 'San Francisco', 'code': 'San+Francisco'})
            elif 'phx' in summary or 'phoenix' in summary or 'scottsdale' in summary:
                if 'Scottsdale' not in [d['name'] for d in destinations]:
                    destinations.append({'name': 'Scottsdale', 'code': 'Scottsdale'})
            elif 'pdx' in summary or 'portland' in summary:
                if 'Portland' not in [d['name'] for d in destinations]:
                    destinations.append({'name': 'Portland', 'code': 'Portland'})
    
    # Always include LA and NYC as defaults if no travel detected
    if not destinations:
        destinations = [
            {'name': 'Los Angeles', 'code': 'Los+Angeles'},
            {'name': 'New York', 'code': 'New+York'}
        ]
    
    return destinations

def get_today_events_detailed(pt_now, all_events):
    """Get detailed breakdown of today's events by category"""
    today_str = pt_now.strftime('%A, %B %d')
    
    result = {
        'flights': [],
        'hotels': [],
        'important': [],
        'meetings': []
    }
    
    for event in all_events:
        event_date = event.get('start', '')
        if today_str not in event_date:
            continue
        
        summary = event.get('summary', '').lower()
        location = event.get('location', '').lower()
        
        # Detect flights
        if 'flight' in summary:
            flight_info = {
                'time': event.get('start', 'TBD'),
                'route': 'TBD',
                'details': event.get('location', '')
            }
            if 'jfk' in summary or 'new york' in summary or 'lga' in summary:
                flight_info['route'] = 'LAX → JFK'
            elif 'lax' in summary or 'los angeles' in summary:
                flight_info['route'] = '→ LAX'
            elif 'atl' in summary or 'atlanta' in summary:
                flight_info['route'] = '→ ATL'
            elif 'sfo' in summary or 'san francisco' in summary:
                flight_info['route'] = '→ SFO'
            result['flights'].append(flight_info)
        
        # Detect hotels - check both summary and description for hotel keywords
        elif any(word in summary for word in ['hotel', 'stay at', 'check-in', 'checkout', 'marriott', 'hilton', 'hyatt', 'fairfield', 'courtyard', 'algonquin', 'moxy', 'jw marriott']):
            # Extract hotel name from summary
            hotel_name = event.get('summary', '')
            # Clean up common prefixes
            for prefix in ['Stay at ', 'Hotel: ', 'Geoffrey Clapp - ', 'Mac Spring Break: ']:
                hotel_name = hotel_name.replace(prefix, '')
            # Clean up confirmation numbers (8+ digit numbers)
            hotel_name = re.sub(r'\d{8,}', '', hotel_name).strip()
            # Clean up trailing commas
            hotel_name = hotel_name.rstrip(',').strip()
            
            result['hotels'].append({
                'name': hotel_name,
                'location': event.get('location', ''),
                'raw_summary': event.get('summary', '')
            })
        
        # Detect important dates (birthdays, anniversaries)
        elif any(word in summary for word in ['birthday', 'anniversary', 'graduation']):
            event_type = 'Birthday' if 'birthday' in summary else 'Anniversary' if 'anniversary' in summary else 'Event'
            name = event.get('summary', '').replace('birthday', '').replace('Birthday', '').strip()
            result['important'].append({
                'type': event_type,
                'name': name,
                'note': event.get('description', '')[:100]
            })
    
    return result

def get_day_events(day_date, all_events):
    """Get event indicators for a specific day"""
    day_str = day_date.strftime('%A, %B %d')
    
    result = {
        'flight': False,
        'hotel': False,
        'birthday': False,
        'travel': False
    }
    
    for event in all_events:
        event_date = event.get('start', '')
        if day_str not in event_date:
            continue
        
        summary = event.get('summary', '').lower()
        
        if 'flight' in summary:
            result['flight'] = True
            result['travel'] = True
        elif any(word in summary for word in ['hotel', 'stay at', 'marriott', 'hilton', 'hyatt', 'fairfield', 'courtyard', 'algonquin', 'moxy', 'jw marriott']):
            result['hotel'] = True
            result['travel'] = True
        elif 'birthday' in summary:
            result['birthday'] = True
    
    return result

def generate_html_email(checkin_type, pt_now):
    """Generate HTML check-in using the locked format from March 22, 2026"""
    
    today_str = pt_now.strftime('%A, %B %d, %Y')
    today_events, travel_events = get_calendar_data()
    location_info = detect_location_and_travel(travel_events)
    
    # Get weather for current location + travel destinations
    # Always include current location first
    weather_cities = []
    
    # Current location based on custody/travel status
    if location_info['city'] == 'New York City':
        weather_cities.append({'name': 'New York', 'code': 'New+York'})
    elif location_info['city'] == 'San Francisco':
        weather_cities.append({'name': 'San Francisco', 'code': 'San+Francisco'})
    elif location_info['city'] == 'Atlanta':
        weather_cities.append({'name': 'Atlanta', 'code': 'Atlanta'})
    else:
        # Default to LA/Calabasas
        weather_cities.append({'name': 'Calabasas', 'code': 'Los+Angeles'})
    
    # Add travel destinations for the week (excluding current location if already included)
    week_destinations = get_week_travel_destinations(travel_events, pt_now)
    current_names = [c['name'] for c in weather_cities]
    for dest in week_destinations[:3]:  # Max 3 additional destinations
        if dest['name'] not in current_names:
            weather_cities.append(dest)
    
    # Fetch weather for all cities
    destination_weather = []
    for city in weather_cities[:4]:  # Max 4 total
        weather = get_weather(city['code'])
        destination_weather.append({'name': city['name'], 'weather': weather})
    
    # Get other data
    todoist_count = get_todoist_count()
    whoop_recovery = get_whoop_recovery()
    latest_weight, weight_history = get_latest_weight()
    weight_trend = get_weight_trend()
    whoop_trend = get_whoop_trend()
    health_recommendations = generate_health_recommendations(weight_trend, whoop_trend, checkin_type)
    
    # Whoop status color and display
    if whoop_recovery:
        whoop_display = f"{whoop_recovery}%"
        whoop_color = "#16a34a"  # green
        whoop_status = "Good"
        if whoop_recovery < 50:
            whoop_color = "#dc2626"  # red
            whoop_status = "Low"
        elif whoop_recovery < 70:
            whoop_color = "#ea580c"  # orange
            whoop_status = "Moderate"
    else:
        whoop_display = "No data"
        whoop_color = "#6b7280"  # gray
        whoop_status = "Unavailable"
    
    # Header based on check-in type
    if checkin_type == "morning":
        header_title = "☀️ Good Morning!"
    elif checkin_type == "midday":
        header_title = "☀️ Midday Check-In"
    elif checkin_type == "afternoon":
        header_title = "🌤️ Afternoon Check-In"
    else:
        header_title = "🌙 Evening Check-In"
    
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
        .footer {{ background: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #666; margin-top: 30px; }}
        a {{ color: #3b82f6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{header_title}</h1>
        <p>{today_str}</p>
    </div>

    <div class="location">
        📍 {location_info['city']}, {location_info['state']} — {location_info['status']}
    </div>

    <div class="weather">
        {''.join([f'<div class="weather-city"><div class="weather-temp">{d["weather"]}</div><div>{d["name"]}</div></div>' for d in destination_weather])}
    </div>
'''
    
    # Get today's detailed calendar events
    today_events_detailed = get_today_events_detailed(pt_now, travel_events)
    
    # PRIORITY SECTION: Today's Travel & Important Events (at the top)
    if today_events_detailed['flights'] or today_events_detailed['hotels'] or today_events_detailed['important']:
        html += '''
    <div class="section" style="border-left-color: #dc2626; background: #fef2f2;">
        <h2>🔔 TODAY'S PRIORITIES</h2>
'''
        
        # Flights (highest priority)
        for flight in today_events_detailed['flights']:
            html += f'''
        <div class="flight" style="margin: 10px 0; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #dc2626;">
            <div style="font-size: 24px; font-weight: bold; color: #dc2626;">✈️ {flight['time']}</div>
            <p style="margin: 5px 0; font-size: 16px;"><strong>{flight['route']}</strong></p>
            <p style="margin: 5px 0; color: #666;">{flight.get('details', '')}</p>
        </div>
'''
        
        # Hotels
        for hotel in today_events_detailed['hotels']:
            html += f'''
        <div style="margin: 10px 0; padding: 12px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #16a34a;">
            <strong>🏨 HOTEL:</strong> {hotel['name']}<br>
            <span style="color: #666;">{hotel.get('location', '')}</span>
        </div>
'''
        
        # Important events (birthdays, anniversaries, etc.)
        for event in today_events_detailed['important']:
            html += f'''
        <div style="margin: 10px 0; padding: 12px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
            <strong>🎉 {event['type']}:</strong> {event['name']}<br>
            <span style="color: #666;">{event.get('note', '')}</span>
        </div>
'''
        
        html += '''    </div>
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
                <div class="stat-number" style="color: {whoop_color};">{whoop_display}</div>
                <div class="stat-label">WHOOP RECOVERY</div>
            </div>
            <div class="stat">
                <div class="stat-number">{latest_weight if latest_weight else '--'}</div>
                <div class="stat-label">LBS</div>
            </div>
        </div>
    </div>
'''
    
    # Week ahead view with event indicators
    html += '''
    <div class="section">
        <h2>This Week</h2>
        <div class="week-view">
'''
    for i in range(7):
        day = pt_now + timedelta(days=i)
        day_str = day.strftime('%A, %B %d')
        day_events = get_day_events(day, travel_events)
        
        event_badges = []
        if day_events['flight']:
            event_badges.append('<span style="background: #dc2626; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 5px;">✈️ FLIGHT</span>')
        if day_events['hotel']:
            event_badges.append('<span style="background: #16a34a; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 5px;">🏨 HOTEL</span>')
        if day_events['birthday']:
            event_badges.append('<span style="background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 5px;">🎂 BDAY</span>')
        
        badges_html = ''.join(event_badges)
        
        html += f'''            <div class="day">
                <span class="day-date">{day_str}</span>{badges_html}
            </div>
'''
    html += '''        </div>
    </div>
'''
    
    # Stocks section (only for morning and evening check-ins)
    if checkin_type in ['morning', 'evening']:
        stock_summary = get_stock_summary()
        html += f'''
    <div class="section">
        <h2>📈 Stocks (30-Day)</h2>
        <pre style="background: #f3f4f6; padding: 15px; border-radius: 8px; font-size: 13px; overflow-x: auto;">{stock_summary}</pre>
    </div>
'''
    
    # Token Health section (concise)
    token_health = run_token_health_check()
    token_color = "#16a34a" if "✅" in token_health else "#dc2626" if "🔴" in token_health else "#ea580c"
    html += f'''
    <div class="section">
        <h2>🔐 Token Health</h2>
        <p style="color: {token_color}; font-weight: bold;">{token_health}</p>
        <p style="font-size: 12px; color: #666;">Calendar • Docs • Whoop • Email</p>
    </div>
'''
    
    # Health section with trends and recommendations
    html += f'''
    <div class="section">
        <h2>💓 Health Trends & Actions</h2>
        
        <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="margin-top: 0; color: #166534;">📊 Weight Loss Progress</h3>
'''
    
    if weight_trend:
        progress_pct = (weight_trend['total_lost'] / weight_trend['goal']) * 100
        html += f'''
            <p><strong>Current:</strong> {weight_trend['current']:.1f} lbs | 
               <strong>Start:</strong> {weight_trend['start']:.1f} lbs | 
               <strong>Lost:</strong> {weight_trend['total_lost']:.1f} lbs ({progress_pct:.0f}% of goal)</p>
            <p><strong>Pace:</strong> {weight_trend['pace']:.1f} lbs/week | 
               <strong>Remaining:</strong> {weight_trend['remaining']:.1f} lbs to goal</p>
'''
        if weight_trend['week_trend'] is not None:
            trend_emoji = "📉" if weight_trend['week_trend'] > 0 else "📈" if weight_trend['week_trend'] < 0 else "➡️"
            html += f'<p>{trend_emoji} <strong>7-day trend:</strong> {"-" if weight_trend["week_trend"] > 0 else "+"}{abs(weight_trend["week_trend"]):.1f} lbs this week</p>'
    else:
        html += '<p>Weight data unavailable</p>'
    
    html += '''
        </div>
        
        <div style="background: #eff6ff; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="margin-top: 0; color: #1e40af;">😴 Recovery & Sleep</h3>
'''
    
    if whoop_trend:
        trend_emoji = "📈" if whoop_trend['trend'] == 'improving' else "📉" if whoop_trend['trend'] == 'declining' else "➡️"
        html += f'''
            <p><strong>Latest recovery:</strong> <span style="color: {whoop_color};">{whoop_trend['latest']}%</span> ({whoop_status})</p>
            <p><strong>7-day average:</strong> {whoop_trend['average']}% | 
               <strong>Trend:</strong> {trend_emoji} {whoop_trend['trend']}</p>
'''
    else:
        html += f'''
            <p><strong>Latest recovery:</strong> <span style="color: {whoop_color};">{whoop_display}</span> ({whoop_status})</p>
            <p style="color: #dc2626;">⚠️ Whoop token expired — re-authorization needed for full data</p>
'''
    
    html += '''
        </div>
        
        <div style="background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
            <h3 style="margin-top: 0; color: #b45309;">🎯 Today's Actions</h3>
'''
    
    if health_recommendations:
        for rec in health_recommendations[:3]:  # Show top 3
            priority_color = '#dc2626' if rec['priority'] == 'high' else '#ea580c' if rec['priority'] == 'medium' else '#16a34a'
            html += f'''
            <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 6px;">
                <p style="margin: 0; font-weight: bold; color: {priority_color};">{rec['category']}</p>
                <p style="margin: 5px 0;">✓ {rec['action']}</p>
                <p style="margin: 0; font-size: 12px; color: #666;">💡 {rec['why']}</p>
            </div>
'''
    else:
        html += '<p>No specific recommendations today — keep up the good work!</p>'
    
    html += '''
        </div>
        
        <p style="margin-top: 15px;"><strong>Dashboard:</strong> <a href="https://gclapp.github.io/health-dashboard/">View full health dashboard →</a></p>
    </div>
'''
    
    # Footer
    html += f'''
    <div class="footer">
        <p>🏛️ Cicero | All systems operational</p>
        <p>Last updated: {pt_now.strftime('%B %d, %Y %I:%M %p PT')}</p>
    </div>
</body>
</html>
'''
    
    return html

def main():
    pt_now = get_pt_time()
    checkin_type = get_checkin_type(pt_now.hour, pt_now.minute)
    
    if not checkin_type:
        print(f"No check-in due at {pt_now.strftime('%I:%M %p PT')}")
        sys.exit(0)
    
    # Generate HTML email using the new format
    html_message = generate_html_email(checkin_type, pt_now)
    
    # Write to pending check-in file
    checkin_file = Path("/home/ubuntu/.openclaw/workspace/logs/pending-checkin.json")
    checkin_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checkin_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "checkin_type": checkin_type,
            "message": f"{checkin_type.title()} check-in — see HTML email",  # Telegram gets simple message
            "html_message": html_message,
            "subject": f"☀️ {checkin_type.title()} Check-In — {pt_now.strftime('%A, %B %d, %Y')}",
            "pt_time": pt_now.strftime('%Y-%m-%d %H:%M:%S'),
            "sent": False,
            "channels": ["telegram", "email"]
        }, f, indent=2)
    
    print(f"✅ {checkin_type.title()} check-in queued: {pt_now.strftime('%I:%M %p PT')}")
    
    # Log it
    log_file = Path("/home/ubuntu/.openclaw/workspace/logs/heartbeat.log")
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] {checkin_type.title()} check-in queued\n")

if __name__ == "__main__":
    main()

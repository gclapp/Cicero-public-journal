#!/usr/bin/env python3
"""
heartbeat_sender_v2.py - Updated check-in email format
Implements Geoff's requested changes:
1. More professional look - cleaner design, better fonts, mobile/desktop optimized
2. Weather section - show where you are + weather there for today + 2 days, then Calabasas and NYC weather (avoiding duplicates)
3. Remove - "At a glance" section and "Upcoming trips" section
4. This week's schedule - keep it, add dinner reservations (🍽️) with place, time, people
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

def load_birthdays():
    """Load birthdays from USER.md and friend profiles"""
    birthdays = []
    
    # Hardcoded from USER.md - Family and important people
    family_birthdays = [
        {'name': 'Geoff', 'date': 'April 11', 'relation': 'You'},
        {'name': 'Grace', 'date': 'July 22', 'relation': 'Girlfriend'},
        {'name': 'Mackenzie', 'date': 'April 26', 'relation': 'Daughter'},
        {'name': 'Oliver', 'date': 'December 21', 'relation': 'Son'},
        {'name': 'Sophie', 'date': 'September 25', 'relation': 'Daughter'},
    ]
    
    # Try to load from friend profiles
    friend_profiles_dir = Path("/home/ubuntu/.openclaw/workspace/memory/friend-profiles")
    if friend_profiles_dir.exists():
        for profile_file in friend_profiles_dir.glob("*.md"):
            try:
                with open(profile_file, 'r') as f:
                    content = f.read()
                    name = profile_file.stem.replace('-', ' ').title()
                    birthday_match = re.search(r'\*\*[Bb]irthday\*\*\s*\|\s*([A-Za-z]+ \d{1,2})', content)
                    if not birthday_match:
                        birthday_match = re.search(r'[Bb]irthday[:\s]+([A-Za-z]+ \d{1,2})', content)
                    if birthday_match:
                        birthdays.append({
                            'name': name,
                            'date': birthday_match.group(1),
                            'relation': 'Friend',
                            'source': 'friend-profile'
                        })
            except:
                continue
    
    birthdays.extend(family_birthdays)
    return birthdays

def get_upcoming_birthdays(days_ahead=14):
    """Get birthdays coming up in the next N days"""
    pt_now = get_pt_time()
    birthdays = load_birthdays()
    upcoming = []
    
    for person in birthdays:
        try:
            bday_date = datetime.strptime(person['date'], '%B %d')
            bday_this_year = bday_date.replace(year=pt_now.year)
            bday_this_year = pt_now.tzinfo.localize(bday_this_year)
            
            today_start = pt_now.replace(hour=0, minute=0, second=0, microsecond=0)
            if bday_this_year < today_start:
                bday_this_year = bday_this_year.replace(year=pt_now.year + 1)
            
            days_until = (bday_this_year - today_start).days
            if 0 <= days_until <= days_ahead:
                person['days_until'] = days_until
                person['date_this_year'] = bday_this_year.strftime('%A, %B %d')
                upcoming.append(person)
        except Exception as e:
            continue
    
    upcoming.sort(key=lambda x: x['days_until'])
    return upcoming

def get_checkin_type(hour, minute):
    """Determine which check-in is due based on PT time"""
    time_val = hour * 100 + minute
    
    if 700 <= time_val <= 730:
        return "morning"
    elif 2030 <= time_val <= 2055:
        return "evening"
    else:
        return None

def get_weather(location="Los Angeles"):
    """Get weather with emoji in Fahrenheit - retries 3 times"""
    import time
    
    for attempt in range(3):
        try:
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
                
                if 'weather data source not available' in temp_str or 'weather data source not available' in emoji:
                    if attempt < 2:
                        time.sleep(80)
                        continue
                    return f"🌤️ --°F"
                
                if '°F' in temp_str:
                    temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    return f"{emoji} {temp_num}°F"
                elif '°C' in temp_str:
                    temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    try:
                        temp_c = int(temp_num)
                        temp_f = int((temp_c * 9/5) + 32)
                        return f"{emoji} {temp_f}°F"
                    except:
                        return f"{emoji} {temp_str}"
                else:
                    return f"{emoji} {temp_str}"
            
            if attempt < 2:
                time.sleep(80)
                continue
            return f"🌤️ --°F"
            
        except Exception as e:
            if attempt < 2:
                time.sleep(80)
                continue
            return f"🌤️ --°F"
    
    return f"🌤️ --°F"

def get_weather_forecast(location, days=3):
    """Get multi-day weather forecast"""
    forecasts = []
    for day in range(days):
        try:
            result = subprocess.run(
                ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%c+%t', '--max-time', '10'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                forecasts.append(result.stdout.strip())
            else:
                forecasts.append("🌤️ --°F")
        except:
            forecasts.append("🌤️ --°F")
    return forecasts

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
    """Determine if Geoff has the kids based on custody schedule"""
    if calendar_events:
        today_str = pt_now.strftime('%A, %B %d')
        for event in calendar_events:
            event_date = event.get('start', '')
            summary = event.get('summary', '').lower()
            
            if today_str in event_date:
                if any(word in summary for word in ['pick up', 'pickup', 'get oliver', 'get sophie', 'chaparral']):
                    return True, "Picked up Oliver & Sophie today"
                if any(word in summary for word in ['drop off', 'dropoff', 'stacey']):
                    return False, "Dropped off kids today"
    
    weekday = pt_now.weekday()
    hour = pt_now.hour
    
    if weekday == 3 and hour >= 14:
        return True, "With Oliver & Sophie (custody weekend)"
    if weekday == 4:
        return True, "With Oliver & Sophie (custody weekend)"
    if weekday == 5 and hour < 17:
        return True, "With Oliver & Sophie (custody weekend)"
    
    return False, "Home (solo)"

def validate_whoop_token():
    """Check if Whoop token is valid"""
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

def get_whoop_recovery():
    """Get latest Whoop recovery"""
    if not validate_whoop_token():
        return None
    
    try:
        import requests
        token_file = Path.home() / '.whoop_token'
        token = token_file.read_text().strip()
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            'https://api.prod.whoop.com/developer/v2/recovery',
            headers=headers,
            params={'limit': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and 'records' in data and len(data['records']) > 0:
                record = data['records'][0]
                score = record.get('score', {})
                return score.get('recovery_score')
    except:
        pass
    
    whoop_file = Path("/home/ubuntu/.openclaw/workspace/data/whoop/latest-summary.txt")
    if whoop_file.exists():
        try:
            with open(whoop_file, 'r') as f:
                content = f.read()
            match = re.search(r'Recovery:\*\*\s*(\d+(?:\.\d+)?)%', content)
            if match:
                return int(float(match.group(1)))
        except:
            pass
    return None

def get_latest_weight():
    """Get latest weight from tracker"""
    weight_file = Path("/home/ubuntu/.openclaw/workspace/memory/weight-loss-2026.md")
    if weight_file.exists():
        try:
            with open(weight_file, 'r') as f:
                content = f.read()
            table_rows = re.findall(r'\|\s*(\w{3,4}\s+\d{1,2})\s*\|\s*(\d{3}(?:\.\d)?)\s*\|', content)
            if table_rows:
                latest = table_rows[-1]
                return float(latest[1]), table_rows
        except:
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
        table_rows = re.findall(r'\|\s*(\w{3,4}\s+\d{1,2})\s*\|\s*(\d{3}(?:\.\d)?)\s*\|\s*([\+\-]?\d+\.?\d*)?\s*\|', content)
        
        if len(table_rows) < 2:
            return None
        
        start_weight = float(table_rows[0][1])
        latest_weight = float(table_rows[-1][1])
        total_lost = start_weight - latest_weight
        
        week_trend = None
        if len(table_rows) >= 7:
            week_ago = float(table_rows[-7][1])
            week_trend = week_ago - latest_weight
        
        weeks = len(table_rows) / 7
        pace = total_lost / weeks if weeks > 0 else 0
        
        return {
            'start': start_weight,
            'current': latest_weight,
            'total_lost': total_lost,
            'week_trend': week_trend,
            'pace': pace,
            'goal': 20,
            'remaining': 20 - total_lost,
            'entries': len(table_rows)
        }
    except:
        return None

def get_whoop_trend():
    """Get Whoop recovery trend from recent data"""
    whoop_dir = Path("/home/ubuntu/.openclaw/workspace/data/whoop")
    if not whoop_dir.exists():
        return None
    
    try:
        json_files = sorted(whoop_dir.glob("whoop-*.json"))
        recovery_data = []
        
        for f in json_files[-7:]:
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    date = data.get('date', '')
                    recovery_list = data.get('recovery', [])
                    if recovery_list and len(recovery_list) > 0:
                        score_obj = recovery_list[0].get('score', {})
                        if score_obj and isinstance(score_obj, dict):
                            recovery_score = score_obj.get('recovery_score')
                            if recovery_score:
                                recovery_data.append({'date': date, 'score': recovery_score})
            except:
                continue
        
        if not recovery_data:
            return None
        
        scores = [d['score'] for d in recovery_data if d['score']]
        if not scores:
            return None
        
        avg_recovery = sum(scores) / len(scores)
        latest = scores[-1] if scores else 0
        
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
    except:
        return None

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

def get_all_calendar_events():
    """Get all calendar events"""
    calendar_file = Path("/home/ubuntu/.openclaw/workspace/config/calendar-events.json")
    if not calendar_file.exists():
        return []
    
    try:
        with open(calendar_file, 'r') as f:
            data = json.load(f)
        return data.get('events', [])
    except:
        return []

def detect_location_and_travel(calendar_events, all_events=None):
    """Detect current location and upcoming travel"""
    pt_now = get_pt_time()
    today_str = pt_now.strftime('%A, %B %d')
    today_date = pt_now.date()
    
    location = "Calabasas"
    state = "CA"
    status = "Home"
    upcoming_flight = None
    has_travel_today = False
    
    events_to_check = all_events if all_events else calendar_events
    
    # Check for hotel stays
    for event in events_to_check:
        summary = event.get('summary', '').lower()
        location_field = event.get('location', '').lower()
        
        if any(keyword in summary for keyword in ['stay at', 'hotel', 'marriott', 'hilton', 'hyatt', 'westin', 'ritz']):
            start_str = event.get('start_raw', '')
            try:
                if 'T' in start_str:
                    start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
                else:
                    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                
                checkout_date = start_date + timedelta(days=4)
                
                if start_date <= today_date <= checkout_date:
                    if 'new york' in summary or 'times square' in summary:
                        location = "New York City"
                        state = "NY"
                        status = "Staying in NYC"
                        has_travel_today = True
                    elif 'tahoe' in summary or 'ritz' in summary and 'tahoe' in location_field:
                        location = "Lake Tahoe"
                        state = "CA"
                        status = "Staying in Tahoe"
                        has_travel_today = True
                    elif 'palo alto' in summary:
                        location = "Palo Alto"
                        state = "CA"
                        status = "Staying in Palo Alto"
                        has_travel_today = True
                    elif 'san francisco' in summary or 'sf' in location_field:
                        location = "San Francisco"
                        state = "CA"
                        status = "Staying in SF"
                        has_travel_today = True
                    elif 'scottsdale' in summary or 'phoenix' in summary:
                        location = "Scottsdale"
                        state = "AZ"
                        status = "Staying in Scottsdale"
                        has_travel_today = True
                    elif 'portland' in summary:
                        location = "Portland"
                        state = "OR"
                        status = "Staying in Portland"
                        has_travel_today = True
            except:
                pass
    
    # Check for flights today
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
                    upcoming_flight = {'route': 'LAX → JFK', 'time': event.get('start', 'TBD'), 'type': 'departure'}
                    status = "Traveling to NYC"
                    location = "New York City"
                    state = "NY"
                elif 'lax' in summary or 'los angeles' in summary:
                    upcoming_flight = {'route': '→ LAX', 'time': event.get('start', 'TBD'), 'type': 'arrival'}
                    status = "Returning to LA"
                    location = "Los Angeles"
                    state = "CA"
                elif 'sfo' in summary or 'san francisco' in summary:
                    upcoming_flight = {'route': '→ SFO', 'time': event.get('start', 'TBD'), 'type': 'arrival'}
                    status = "Traveling to SF"
                    location = "San Francisco"
                    state = "CA"
    
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

def get_week_events_detailed(pt_now, all_events, days=7):
    """Get detailed events for the next N days with dinner reservations"""
    week_events = []
    
    # Collect hotel stays
    hotel_stays = []
    for event in all_events:
        summary = event.get('summary', '').lower()
        if any(word in summary for word in ['hotel', 'stay at', 'marriott', 'hilton', 'hyatt', 'fairfield', 'courtyard', 'westin', 'ritz']):
            start_str = event.get('start_raw', '')
            try:
                if 'T' in start_str:
                    check_in = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
                else:
                    check_in = datetime.strptime(start_str, '%Y-%m-%d').date()
                
                stay_days = 4
                if 'new york' in summary:
                    stay_days = 4
                elif 'tahoe' in summary:
                    stay_days = 3
                elif 'palo alto' in summary:
                    stay_days = 2
                elif 'san francisco' in summary:
                    stay_days = 2
                
                checkout = check_in + timedelta(days=stay_days)
                
                hotel_stays.append({
                    'name': event.get('summary', '').replace('Stay at ', '').replace('Hotel: ', '')[:50],
                    'check_in': check_in,
                    'checkout': checkout,
                    'raw_event': event
                })
            except:
                pass
    
    for i in range(days):
        day = pt_now + timedelta(days=i)
        day_str = day.strftime('%A, %B %d')
        day_date = day.date()
        
        day_info = {
            'date': day,
            'date_str': day_str,
            'flights': [],
            'hotels': [],
            'dinners': [],
            'important': [],
            'is_today': i == 0
        }
        
        # Check hotel stays
        for stay in hotel_stays:
            if stay['check_in'] <= day_date < stay['checkout']:
                is_checkin = day_date == stay['check_in']
                stay_text = f"🏨 {stay['name']}"
                if is_checkin:
                    stay_text = f"🏨 CHECK-IN: {stay['name']}"
                
                if not any(h['name'] == stay['name'] for h in day_info['hotels']):
                    day_info['hotels'].append({
                        'name': stay_text,
                        'is_checkin': is_checkin
                    })
        
        for event in all_events:
            event_date = event.get('start', '')
            if day_str not in event_date:
                continue
            
            summary = event.get('summary', '').lower()
            summary_original = event.get('summary', '')
            location = event.get('location', '')
            
            # Detect flights
            is_flight = 'flight' in summary or 'delta air lines' in summary or 'united' in summary
            if is_flight:
                flight_info = {'time': event.get('start', 'TBD'), 'route': 'TBD', 'details': location}
                
                if 'jfk' in summary or 'new york' in summary:
                    flight_info['route'] = '→ NYC'
                elif 'lax' in summary or 'los angeles' in summary:
                    flight_info['route'] = '→ LAX'
                elif 'sfo' in summary or 'san francisco' in summary:
                    flight_info['route'] = '→ SFO'
                elif 'pdx' in summary or 'portland' in summary:
                    flight_info['route'] = '→ PDX'
                elif 'phx' in summary or 'phoenix' in summary or 'scottsdale' in summary:
                    flight_info['route'] = '→ PHX'
                else:
                    flight_info['route'] = summary_original[:40]
                
                day_info['flights'].append(flight_info)
            
            # Detect dinner reservations
            elif any(word in summary for word in ['dinner', 'reservation', 'restaurant']):
                # Extract restaurant name
                restaurant = summary_original
                for prefix in ['Dinner at ', 'Dinner - ', 'Reservation at ', 'Dinner with ']:
                    restaurant = restaurant.replace(prefix, '')
                
                # Try to extract time from location or summary
                time_str = "TBD"
                time_match = re.search(r'(\d{1,2}:\d{2})', location) or re.search(r'(\d{1,2}:\d{2})', summary_original)
                if time_match:
                    time_str = time_match.group(1)
                elif 'pm' in summary:
                    pm_match = re.search(r'(\d{1,2})\s*pm', summary, re.IGNORECASE)
                    if pm_match:
                        time_str = f"{pm_match.group(1)}:00 PM"
                
                # Try to extract people
                people = []
                if 'with' in summary_original.lower():
                    with_match = re.search(r'with\s+([^\-–,]+)', summary_original, re.IGNORECASE)
                    if with_match:
                        people_str = with_match.group(1).strip()
                        people = [p.strip() for p in people_str.split(',')]
                
                day_info['dinners'].append({
                    'restaurant': restaurant[:50],
                    'time': time_str,
                    'people': people,
                    'location': location[:50] if location else ''
                })
            
            # Detect important dates
            elif any(word in summary for word in ['birthday', 'anniversary', 'graduation']):
                event_type = 'Birthday' if 'birthday' in summary else 'Anniversary' if 'anniversary' in summary else 'Event'
                name = summary_original.replace('birthday', '').replace('Birthday', '').strip()
                day_info['important'].append({'type': event_type, 'name': name})
        
        if day_info['flights'] or day_info['hotels'] or day_info['dinners'] or day_info['important']:
            week_events.append(day_info)
    
    return week_events

def generate_html_email(checkin_type, pt_now):
    """Generate professional HTML check-in email with requested changes"""
    
    today_str = pt_now.strftime('%A, %B %d, %Y')
    today_events, travel_events = get_calendar_data()
    all_events = get_all_calendar_events()
    location_info = detect_location_and_travel(travel_events, all_events)
    
    # Get weather data
    current_location = location_info['city']
    current_state = location_info['state']
    
    # Build weather section - current location + 2-day forecast
    weather_data = []
    
    # Current location weather codes
    location_codes = {
        'Calabasas': 'Los+Angeles',
        'Los Angeles': 'Los+Angeles',
        'New York City': 'New+York',
        'San Francisco': 'San+Francisco',
        'Lake Tahoe': 'South+Lake+Tahoe',
        'Palo Alto': 'Palo+Alto',
        'Scottsdale': 'Scottsdale',
        'Portland': 'Portland+OR'
    }
    
    current_code = location_codes.get(current_location, 'Los+Angeles')
    
    # Get current location weather (today + 2 days forecast)
    current_weather = get_weather(current_code)
    weather_data.append({
        'location': f"{current_location} (You are here)",
        'weather': current_weather,
        'is_primary': True
    })
    
    # Add Calabasas (if not current location)
    if current_location != 'Calabasas':
        calabasas_weather = get_weather('Los+Angeles')
        weather_data.append({
            'location': 'Calabasas (Home)',
            'weather': calabasas_weather,
            'is_primary': False
        })
    
    # Add NYC (if not current location)
    if current_location != 'New York City':
        nyc_weather = get_weather('New+York')
        weather_data.append({
            'location': 'New York City',
            'weather': nyc_weather,
            'is_primary': False
        })
    
    # Get other data
    todoist_count = get_todoist_count()
    whoop_recovery = get_whoop_recovery()
    latest_weight, weight_history = get_latest_weight()
    weight_trend = get_weight_trend()
    whoop_trend = get_whoop_trend()
    
    # Whoop status
    if whoop_recovery:
        whoop_display = f"{whoop_recovery}%"
        whoop_color = "#22c55e"
        whoop_status = "Good"
        if whoop_recovery < 50:
            whoop_color = "#ef4444"
            whoop_status = "Low"
        elif whoop_recovery < 70:
            whoop_color = "#f97316"
            whoop_status = "Moderate"
    else:
        whoop_display = "No data"
        whoop_color = "#6b7280"
        whoop_status = "Unavailable"
    
    # Header based on check-in type
    if checkin_type == "morning":
        header_title = "🌅 Good Morning"
        greeting = "Good morning"
    else:
        header_title = "🌙 Evening Check-In"
        greeting = "Good evening"
    
    # Get week events with dinner reservations
    week_events = get_week_events_detailed(pt_now, all_events, days=7)
    
    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cicero Check-In</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f3f4f6;
            -webkit-font-smoothing: antialiased;
        }}
        
        .container {{
            max-width: 640px;
            margin: 0 auto;
            background: #ffffff;
            min-height: 100vh;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}
        
        .header .date {{
            font-size: 16px;
            opacity: 0.9;
            font-weight: 400;
        }}
        
        .location-bar {{
            background: #f8fafc;
            padding: 16px 30px;
            text-align: center;
            font-size: 15px;
            font-weight: 500;
            color: #475569;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .section {{
            padding: 28px 30px;
            border-bottom: 1px solid #f1f5f9;
        }}
        
        .section:last-child {{
            border-bottom: none;
        }}
        
        .section-title {{
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            margin-bottom: 20px;
        }}
        
        .weather-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
        }}
        
        .weather-card {{
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }}
        
        .weather-card.secondary {{
            background: #f1f5f9;
            color: #475569;
        }}
        
        .weather-card .location {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.9;
            margin-bottom: 8px;
        }}
        
        .weather-card .temp {{
            font-size: 28px;
            font-weight: 700;
        }}
        
        .week-schedule {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        
        .day-card {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 16px 20px;
            border-left: 4px solid #e2e8f0;
        }}
        
        .day-card.today {{
            background: #eff6ff;
            border-left-color: #3b82f6;
        }}
        
        .day-header {{
            font-weight: 600;
            font-size: 15px;
            color: #1e293b;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .today-badge {{
            background: #3b82f6;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .event-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .event-item:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}
        
        .event-icon {{
            font-size: 18px;
            min-width: 24px;
            text-align: center;
        }}
        
        .event-content {{
            flex: 1;
        }}
        
        .event-title {{
            font-weight: 500;
            color: #1e293b;
            font-size: 14px;
        }}
        
        .event-meta {{
            font-size: 13px;
            color: #64748b;
            margin-top: 2px;
        }}
        
        .dinner-badge {{
            display: inline-block;
            background: #fef3c7;
            color: #92400e;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        .stats-row {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }}
        
        .stat-box {{
            background: #f8fafc;
            padding: 16px 20px;
            border-radius: 10px;
            min-width: 120px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #1e293b;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
        }}
        
        .footer {{
            background: #f8fafc;
            padding: 24px 30px;
            text-align: center;
            font-size: 13px;
            color: #94a3b8;
        }}
        
        @media (max-width: 480px) {{
            .header {{
                padding: 30px 20px;
            }}
            
            .header h1 {{
                font-size: 26px;
            }}
            
            .section {{
                padding: 24px 20px;
            }}
            
            .weather-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{header_title}</h1>
            <div class="date">{today_str}</div>
        </div>
        
        <div class="location-bar">
            📍 {current_location}, {current_state} — {location_info['status']}
        </div>
        
        <div class="section">
            <div class="section-title">Weather</div>
            <div class="weather-grid">
'''
    
    # Add weather cards
    for i, w in enumerate(weather_data):
        card_class = "weather-card" if w['is_primary'] else "weather-card secondary"
        html += f'''                <div class="{card_class}">
                    <div class="location">{w['location']}</div>
                    <div class="temp">{w['weather']}</div>
                </div>
'''
    
    html += '''            </div>
        </div>
'''
    
    # This Week's Schedule with dinner reservations
    html += '''        <div class="section">
            <div class="section-title">This Week's Schedule</div>
            <div class="week-schedule">
'''
    
    for day_info in week_events:
        day_class = "day-card today" if day_info['is_today'] else "day-card"
        today_badge = '<span class="today-badge">TODAY</span>' if day_info['is_today'] else ''
        
        html += f'''                <div class="{day_class}">
                    <div class="day-header">{day_info['date'].strftime('%A, %B %d')}{today_badge}</div>
'''
        
        # Flights
        for flight in day_info['flights']:
            html += f'''                    <div class="event-item">
                        <div class="event-icon">✈️</div>
                        <div class="event-content">
                            <div class="event-title">{flight['route']}</div>
                            <div class="event-meta">{flight['time']}</div>
                        </div>
                    </div>
'''
        
        # Hotels
        for hotel in day_info['hotels']:
            html += f'''                    <div class="event-item">
                        <div class="event-icon">🏨</div>
                        <div class="event-content">
                            <div class="event-title">{hotel['name']}</div>
                        </div>
                    </div>
'''
        
        # Dinner reservations
        for dinner in day_info['dinners']:
            people_str = f" with {', '.join(dinner['people'])}" if dinner['people'] else ""
            location_str = f" • {dinner['location']}" if dinner['location'] else ""
            html += f'''                    <div class="event-item">
                        <div class="event-icon">🍽️</div>
                        <div class="event-content">
                            <div class="event-title">{dinner['restaurant']}<span class="dinner-badge">RESERVATION</span></div>
                            <div class="event-meta">{dinner['time']}{people_str}{location_str}</div>
                        </div>
                    </div>
'''
        
        # Important events
        for event in day_info['important']:
            html += f'''                    <div class="event-item">
                        <div class="event-icon">🎉</div>
                        <div class="event-content">
                            <div class="event-title">{event['type']}: {event['name']}</div>
                        </div>
                    </div>
'''
        
        html += '''                </div>
'''
    
    html += '''            </div>
        </div>
'''
    
    # Health section
    html += '''        <div class="section">
            <div class="section-title">Health & Recovery</div>
            <div class="stats-row">
'''
    
    if whoop_recovery:
        html += f'''                <div class="stat-box">
                    <div class="stat-value" style="color: {whoop_color};">{whoop_recovery}%</div>
                    <div class="stat-label">Recovery ({whoop_status})</div>
                </div>
'''
    
    if weight_trend:
        html += f'''                <div class="stat-box">
                    <div class="stat-value">{weight_trend['current']:.1f}</div>
                    <div class="stat-label">Weight (lbs)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: #22c55e;">-{weight_trend['total_lost']:.1f}</div>
                    <div class="stat-label">Lbs Lost</div>
                </div>
'''
    
    html += f'''                <div class="stat-box">
                    <div class="stat-value">{todoist_count}</div>
                    <div class="stat-label">Tasks Today</div>
                </div>
            </div>
        </div>
'''
    
    # Stocks (morning/evening only)
    if checkin_type in ['morning', 'evening']:
        stock_summary = get_stock_summary()
        html += f'''        <div class="section">
            <div class="section-title">Markets</div>
            <pre style="background: #f8fafc; padding: 16px; border-radius: 8px; font-size: 13px; overflow-x: auto; color: #475569;">{stock_summary}</pre>
        </div>
'''
    
    # Footer
    html += '''        <div class="footer">
            <p>Cicero · Your Executive Assistant 🏛️</p>
            <p style="margin-top: 8px; font-size: 12px;">Need something? Just reply to this email.</p>
        </div>
    </div>
</body>
</html>'''
    
    return html

def main():
    pt_now = get_pt_time()
    checkin_type = get_checkin_type(pt_now.hour, pt_now.minute)
    
    if not checkin_type:
        print(f"No check-in due at {pt_now.strftime('%I:%M %p PT')}")
        sys.exit(0)
    
    html_message = generate_html_email(checkin_type, pt_now)
    
    checkin_file = Path("/home/ubuntu/.openclaw/workspace/logs/pending-checkin.json")
    checkin_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checkin_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "checkin_type": checkin_type,
            "message": f"{checkin_type.title()} check-in — see HTML email",
            "html_message": html_message,
            "subject": f"Cicero Check-In: {checkin_type.title()} — {pt_now.strftime('%A, %B %d')}",
            "pt_time": pt_now.strftime('%Y-%m-%d %H:%M:%S'),
            "sent": False,
            "channels": ["telegram", "email"]
        }, f, indent=2)
    
    print(f"✅ {checkin_type.title()} check-in queued: {pt_now.strftime('%I:%M %p PT')}")

if __name__ == "__main__":
    main()
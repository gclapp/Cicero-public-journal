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
import html as html_lib
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add workspace to path for imports
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace')

TODOIST_PATH = '/home/ubuntu/.npm-global/bin/todoist'

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

def get_weather_detailed(location):
    """Get detailed weather with temp, humidity, and precipitation"""
    import time
    
    for attempt in range(2):
        try:
            # Get condition emoji
            emoji_result = subprocess.run(
                ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%c', '--max-time', '10'],
                capture_output=True, text=True, timeout=15
            )
            # Get temperature
            temp_result = subprocess.run(
                ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%t', '--max-time', '10'],
                capture_output=True, text=True, timeout=15
            )
            # Get humidity
            humidity_result = subprocess.run(
                ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%h', '--max-time', '10'],
                capture_output=True, text=True, timeout=15
            )
            # Get precipitation probability
            precip_result = subprocess.run(
                ['curl', '-s', f'wttr.in/{location.replace(" ", "+")}?format=%p', '--max-time', '10'],
                capture_output=True, text=True, timeout=15
            )
            
            if emoji_result.returncode == 0 and temp_result.returncode == 0:
                emoji = emoji_result.stdout.strip()
                temp_str = temp_result.stdout.strip()
                humidity = humidity_result.stdout.strip() if humidity_result.returncode == 0 else "--"
                precip = precip_result.stdout.strip() if precip_result.returncode == 0 else "0"
                
                # Parse temperature
                if '°F' in temp_str:
                    temp = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    temp = f"{temp}°F"
                elif '°C' in temp_str:
                    temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    try:
                        temp_c = int(temp_num)
                        temp_f = int((temp_c * 9/5) + 32)
                        temp = f"{temp_f}°F"
                    except:
                        temp = temp_str
                else:
                    temp = temp_str
                
                # Parse precipitation - if empty or 0, show as "0%"
                precip_val = precip.strip()
                if not precip_val or precip_val == '0.0' or precip_val == '0':
                    precip_display = "0%"
                else:
                    # wttr.in returns mm, convert to probability approximation
                    try:
                        precip_mm = float(precip_val)
                        if precip_mm == 0:
                            precip_display = "0%"
                        elif precip_mm < 1:
                            precip_display = "20%"
                        elif precip_mm < 2.5:
                            precip_display = "40%"
                        elif precip_mm < 5:
                            precip_display = "60%"
                        elif precip_mm < 10:
                            precip_display = "80%"
                        else:
                            precip_display = "90%+"
                    except:
                        precip_display = f"{precip_val}mm"
                
                return {
                    'emoji': emoji,
                    'temp': temp,
                    'humidity': humidity if humidity else "--",
                    'precip': precip_display
                }
            
            if attempt < 1:
                time.sleep(2)
                continue
            return {'emoji': '🌤️', 'temp': '--°F', 'humidity': '--', 'precip': '0%'}
            
        except Exception as e:
            if attempt < 1:
                time.sleep(2)
                continue
            return {'emoji': '🌤️', 'temp': '--°F', 'humidity': '--', 'precip': '0%'}
    
    return {'emoji': '🌤️', 'temp': '--°F', 'humidity': '--', 'precip': '0%'}

def get_todoist_count():
    """Get Todoist task count"""
    tasks = run_todoist_json(['today'])
    if tasks is None:
        return "--"
    return len(tasks)

def run_todoist_json(args):
    """Run Todoist CLI with JSON output using the cron-safe absolute path."""
    try:
        cmd = [TODOIST_PATH] + args
        if '--json' not in cmd:
            cmd.append('--json')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Todoist command failed: {result.stderr.strip()}")
            return None
        output = result.stdout.strip()
        if not output:
            return []
        return json.loads(output)
    except Exception as e:
        print(f"Error running Todoist command: {e}")
        return None

def get_todoist_due_label(task):
    """Return a concise PT-aware due label for a Todoist task."""
    due = task.get('due') or {}
    due_date = (due.get('date') or '')[:10]
    if not due_date:
        return "No due date"

    pt_now = get_pt_time()
    today = pt_now.date()
    tomorrow = today + timedelta(days=1)

    try:
        due_day = datetime.strptime(due_date, '%Y-%m-%d').date()
    except ValueError:
        return due.get('string') or due_date

    if due_day < today:
        return f"Overdue: {due_day.strftime('%b %-d')}"
    if due_day == today:
        return "Today"
    if due_day == tomorrow:
        return "Tomorrow"
    return due_day.strftime('%b %-d')

def get_todoist_priorities():
    """Get Todoist P1/P2 tasks that are overdue, due today, or due tomorrow."""
    todoist_tasks = run_todoist_json(['tasks', '--filter', '(p1 | p2) & (overdue | today | tomorrow)'])
    if todoist_tasks is None:
        return []

    priority_tasks = []
    for task in todoist_tasks:
        todoist_priority = task.get('priority', 1)
        # Todoist JSON priorities are inverted: 4=P1, 3=P2, 2=P3, 1=P4.
        if todoist_priority < 3:
            continue
        priority_tasks.append({
            'title': task.get('content', 'Untitled task'),
            'priority': 1 if todoist_priority == 4 else 2,
            'due': get_todoist_due_label(task),
            'due_sort': ((task.get('due') or {}).get('date') or '9999-12-31')[:10],
        })

    priority_tasks.sort(key=lambda x: (x['priority'], x['due_sort'], x['title'].lower()))
    return priority_tasks

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
                # Extract restaurant name - remove common prefixes
                restaurant = summary_original
                for prefix in ['Dinner at ', 'Dinner - ', 'Reservation at ', 'Dinner with ', 'Dinner: ']:
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
                elif 'am' in summary:
                    am_match = re.search(r'(\d{1,2})\s*am', summary, re.IGNORECASE)
                    if am_match:
                        time_str = f"{am_match.group(1)}:00 AM"
                
                # Try to extract people - multiple patterns
                people = []
                summary_lower = summary_original.lower()
                
                # Pattern 1: "Dinner with [Name] at [Restaurant]"
                if 'with ' in summary_lower and ' at ' in summary_lower:
                    with_match = re.search(r'with\s+(.+?)\s+at\s+', summary_original, re.IGNORECASE)
                    if with_match:
                        people_str = with_match.group(1).strip()
                        # Split by common separators
                        people = [p.strip() for p in re.split(r',|\s+and\s+', people_str) if p.strip()]
                
                # Pattern 2: "Dinner at [Restaurant] with [Name]"
                elif ' at ' in summary_lower and 'with ' in summary_lower:
                    with_match = re.search(r'with\s+(.+)$', summary_original, re.IGNORECASE)
                    if with_match:
                        people_str = with_match.group(1).strip()
                        # Remove trailing punctuation
                        people_str = re.sub(r'[\-–].*$', '', people_str).strip()
                        people = [p.strip() for p in re.split(r',|\s+and\s+', people_str) if p.strip()]
                
                # Pattern 3: Just "with [Name]" anywhere
                elif 'with ' in summary_lower:
                    with_match = re.search(r'with\s+(.+?)(?:\s*[\-–]|\s+at\s+|\s*$)', summary_original, re.IGNORECASE)
                    if with_match:
                        people_str = with_match.group(1).strip()
                        people = [p.strip() for p in re.split(r',|\s+and\s+', people_str) if p.strip()]
                
                # Clean up restaurant name - remove "with [people]" part if it's still there
                for person in people:
                    restaurant = re.sub(rf'\s+with\s+{re.escape(person)}.*$', '', restaurant, flags=re.IGNORECASE)
                    restaurant = re.sub(rf'\s*{re.escape(person)}.*$', '', restaurant, flags=re.IGNORECASE)
                restaurant = re.sub(r'\s+with\s+.*$', '', restaurant, flags=re.IGNORECASE)
                restaurant = restaurant.strip()
                
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
    
    # Get detailed weather for all locations
    weather_data = []
    
    # Current location weather (with humidity and precip)
    current_weather_detailed = get_weather_detailed(current_code)
    weather_data.append({
        'location': f"{current_location} (You are here)",
        'weather': current_weather_detailed,
        'is_primary': True
    })
    
    # Add Calabasas (if not current location)
    if current_location != 'Calabasas':
        calabasas_weather = get_weather_detailed('Los+Angeles')
        weather_data.append({
            'location': 'Calabasas (Home)',
            'weather': calabasas_weather,
            'is_primary': False
        })
    
    # Add NYC (if not current location)
    if current_location != 'New York City':
        nyc_weather = get_weather_detailed('New+York')
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
        
        .weather-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .weather-row {{
            display: block;
            padding: 16px 20px;
            border-radius: 12px;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
        }}
        
        .weather-row.secondary {{
            background: #f1f5f9;
            color: #475569;
        }}
        
        .weather-row .location {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .weather-row .main-info {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }}
        
        .weather-row .emoji {{
            font-size: 32px;
        }}
        
        .weather-row .temp {{
            font-size: 28px;
            font-weight: 700;
        }}
        
        .weather-row .details {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            font-size: 13px;
            opacity: 0.9;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }}
        
        .weather-row.secondary .details {{
            border-top-color: #e2e8f0;
            color: #64748b;
        }}
        
        .weather-row .detail-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .week-schedule {{
            display: block;
            width: 100%;
        }}
        
        .day-card {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 16px;
            border-left: 4px solid #e2e8f0;
            width: 100%;
            margin-bottom: 12px;
            box-sizing: border-box;
        }}
        
        .day-card:last-child {{
            margin-bottom: 0;
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
            flex-wrap: wrap;
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
            display: block;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
            width: 100%;
        }}
        
        .event-item:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}
        
        .event-icon {{
            font-size: 20px;
            display: inline-block;
            margin-right: 8px;
            vertical-align: top;
        }}
        
        .event-content {{
            display: inline-block;
            vertical-align: top;
            max-width: calc(100% - 40px);
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
        
        .priority-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .priority-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 16px;
            background: #f8fafc;
            border-radius: 10px;
            border-left: 3px solid #e2e8f0;
        }}
        
        .priority-badge {{
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            flex-shrink: 0;
        }}
        
        .priority-content {{
            flex: 1;
        }}
        
        .priority-title {{
            font-weight: 500;
            color: #1e293b;
            font-size: 14px;
        }}
        
        .priority-meta {{
            font-size: 12px;
            color: #64748b;
            margin-top: 2px;
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
                padding: 24px 16px;
            }}
            
            .header h1 {{
                font-size: 24px;
            }}
            
            .section {{
                padding: 20px 16px;
            }}
            
            .weather-row {{
                flex-wrap: wrap;
                padding: 12px 16px;
            }}
            
            .weather-row .temp {{
                font-size: 20px;
                margin-right: 12px;
            }}
            
            .weather-row .details {{
                width: 100%;
                margin-top: 8px;
                justify-content: flex-start;
            }}
            
            .day-card {{
                padding: 12px;
            }}
            
            .event-item {{
                padding: 8px 0;
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
            <div class="weather-list">
'''
    
    # Add weather rows with detailed info - stacked vertically
    for i, w in enumerate(weather_data):
        row_class = "weather-row" if w['is_primary'] else "weather-row secondary"
        weather = w['weather']
        html += f'''                <div class="{row_class}">
                    <div class="location">{w['location']}</div>
                    <div class="main-info">
                        <div class="emoji">{weather['emoji']}</div>
                        <div class="temp">{weather['temp']}</div>
                    </div>
                    <div class="details">
                        <div class="detail-item">💧 Humidity: {weather['humidity']}</div>
                        <div class="detail-item">🌧️ Precipitation: {weather['precip']}</div>
                    </div>
                </div>
'''
    
    html += '''            </div>
        </div>
'''
    
    # This Week's Schedule - show all 7 days as rows
    html += '''        <div class="section">
            <div class="section-title">This Week's Schedule</div>
            <div class="week-schedule">
'''
    
    # Generate all 7 days, even if no events
    for i in range(7):
        day = pt_now + timedelta(days=i)
        day_str = day.strftime('%A, %B %d')
        is_today = i == 0
        
        # Find events for this day
        day_events = None
        for de in week_events:
            if de['date'].strftime('%A, %B %d') == day_str:
                day_events = de
                break
        
        day_class = "day-card today" if is_today else "day-card"
        today_badge = '<span class="today-badge">TODAY</span>' if is_today else ''
        
        html += f'''                <div class="{day_class}">
                    <div class="day-header">{day.strftime('%A, %B %d')}{today_badge}</div>
'''
        
        if day_events and (day_events['flights'] or day_events['hotels'] or day_events['dinners'] or day_events['important']):
            # Flights
            for flight in day_events['flights']:
                html += f'''                    <div class="event-item">
                        <div class="event-icon">✈️</div>
                        <div class="event-content">
                            <div class="event-title">{flight['route']}</div>
                            <div class="event-meta">{flight['time']}</div>
                        </div>
                    </div>
'''
            
            # Hotels
            for hotel in day_events['hotels']:
                html += f'''                    <div class="event-item">
                        <div class="event-icon">🏨</div>
                        <div class="event-content">
                            <div class="event-title">{hotel['name']}</div>
                        </div>
                    </div>
'''
            
            # Dinner reservations
            for dinner in day_events['dinners']:
                people_str = f" with {', '.join(dinner['people'])}" if dinner['people'] else ""
                location_str = f" • {dinner['location']}" if dinner['location'] else ""
                
                # Build the meta line with people prominently displayed
                meta_parts = [dinner['time']] if dinner['time'] != "TBD" else []
                if dinner['people']:
                    meta_parts.append(f"with {', '.join(dinner['people'])}")
                if dinner['location']:
                    meta_parts.append(dinner['location'])
                
                meta_line = " • ".join(meta_parts) if meta_parts else "Time TBD"
                
                html += f'''                    <div class="event-item">
                        <div class="event-icon">🍽️</div>
                        <div class="event-content">
                            <div class="event-title">{dinner['restaurant']}<span class="dinner-badge">RESERVATION</span></div>
                            <div class="event-meta">{meta_line}</div>
                        </div>
                    </div>
'''
            
            # Important events
            for event in day_events['important']:
                html += f'''                    <div class="event-item">
                        <div class="event-icon">🎉</div>
                        <div class="event-content">
                            <div class="event-title">{event['type']}: {event['name']}</div>
                        </div>
                    </div>
'''
        else:
            # No events for this day
            html += '''                    <div class="event-item" style="opacity: 0.6;">
                        <div class="event-icon">📅</div>
                        <div class="event-content">
                            <div class="event-title" style="color: #94a3b8; font-weight: 400;">No events scheduled</div>
                        </div>
                    </div>
'''
        
        html += '''                </div>
'''
    
    html += '''            </div>
        </div>
'''
    
    # Today's Priorities - Todoist p1 and p2 tasks due today or tomorrow
    priority_tasks = get_todoist_priorities()
    if priority_tasks:
        html += '''        <div class="section">
            <div class="section-title">Today's Priorities</div>
            <div class="priority-list">
'''
        for task in priority_tasks:
            priority_color = '#dc2626' if task['priority'] == 1 else '#ea580c'
            priority_label = 'P1' if task['priority'] == 1 else 'P2'
            html += f'''                <div class="priority-item">
                    <div class="priority-badge" style="background: {priority_color};">{priority_label}</div>
                    <div class="priority-content">
                        <div class="priority-title">{html_lib.escape(task['title'])}</div>
                        <div class="priority-meta">Due: {task['due']}</div>
                    </div>
                </div>
'''
        html += '''            </div>
        </div>
'''
    
    # Stocks (morning/evening only)
    if checkin_type in ['morning', 'evening']:
        stock_summary = get_stock_summary()
        # Convert markdown to HTML
        stock_html = stock_summary
        # Convert **bold** to <strong>
        stock_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stock_html)
        # Convert *italic* to <em>
        stock_html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', stock_html)
        # Convert newlines to <br>
        stock_html = stock_html.replace('\n', '<br>')
        # Convert | to table-like structure
        if '|' in stock_html:
            lines = stock_summary.split('\n')
            table_html = '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
            for line in lines:
                if '|' in line and '---' not in line:
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if cells:
                        table_html += '<tr>'
                        for cell in cells:
                            # Check if it's a header row (all bold)
                            if '**' in cell:
                                cell = cell.replace('**', '')
                                table_html += f'<th style="text-align: left; padding: 8px; border-bottom: 2px solid #e2e8f0; font-weight: 600;">{cell}</th>'
                            else:
                                # Color positive/negative changes
                                cell_html = cell
                                if '▲' in cell or '+' in cell and '%' in cell:
                                    cell_html = f'<span style="color: #16a34a;">{cell}</span>'
                                elif '▼' in cell or ('-' in cell and '%' in cell):
                                    cell_html = f'<span style="color: #dc2626;">{cell}</span>'
                                table_html += f'<td style="padding: 8px; border-bottom: 1px solid #f1f5f9;">{cell_html}</td>'
                        table_html += '</tr>'
            table_html += '</table>'
            stock_html = table_html
        
        html += f'''        <div class="section">
            <div class="section-title">Markets</div>
            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; overflow-x: auto;">
                {stock_html}
            </div>
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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

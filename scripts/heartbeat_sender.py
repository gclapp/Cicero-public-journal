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
                    # Look for birthday in the file
                    name = profile_file.stem.replace('-', ' ').title()
                    # Simple regex to find birthday patterns (handles "Birthday: April 8" or "| **Birthday** | April 8 |")
                    import re
                    # Try table format first: | **Birthday** | April 8 |
                    birthday_match = re.search(r'\*\*[Bb]irthday\*\*\s*\|\s*([A-Za-z]+ \d{1,2})', content)
                    # Fall back to regular format: Birthday: April 8
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
    
    # Add family birthdays
    birthdays.extend(family_birthdays)
    
    return birthdays

def get_upcoming_birthdays(days_ahead=14):
    """Get birthdays coming up in the next N days"""
    pt_now = get_pt_time()
    birthdays = load_birthdays()
    upcoming = []
    
    for person in birthdays:
        try:
            # Parse the birthday date (naive datetime)
            bday_date = datetime.strptime(person['date'], '%B %d')
            # Set to current year
            bday_this_year = bday_date.replace(year=pt_now.year)
            
            # Make it timezone-aware to match pt_now
            bday_this_year = pt_now.tzinfo.localize(bday_this_year)
            
            # If birthday already passed this year, check next year
            today_start = pt_now.replace(hour=0, minute=0, second=0, microsecond=0)
            if bday_this_year < today_start:
                bday_this_year = bday_this_year.replace(year=pt_now.year + 1)
            
            # Check if within lookahead window
            days_until = (bday_this_year - today_start).days
            if 0 <= days_until <= days_ahead:
                person['days_until'] = days_until
                person['date_this_year'] = bday_this_year.strftime('%A, %B %d')
                upcoming.append(person)
        except Exception as e:
            print(f"Error processing birthday for {person.get('name', 'unknown')}: {e}")
            continue
    
    # Sort by days until
    upcoming.sort(key=lambda x: x['days_until'])
    return upcoming

def get_checkin_type(hour, minute):
    """Determine which check-in is due based on PT time"""
    time_val = hour * 100 + minute
    
    # Evening only: 8:30-8:55 PM (per user request April 10, 2026)
    if 2030 <= time_val <= 2055:
        return "evening"
    else:
        return None

def get_weather(location="Los Angeles"):
    """Get weather with emoji in Fahrenheit - retries 3 times over 4 minutes"""
    import time
    
    for attempt in range(3):  # Try 3 times
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
                
                # Check for wttr.in error message
                if 'weather data source not available' in temp_str or 'weather data source not available' in emoji:
                    if attempt < 2:  # Retry if not last attempt
                        print(f"Weather attempt {attempt+1}/3 failed (source not available), waiting 80s...")
                        time.sleep(80)  # Wait 80 seconds between attempts (4 min total)
                        continue
                    return f"🌤️ --°F"
                
                # Check if wttr.in is already returning Fahrenheit
                if '°F' in temp_str:
                    # Already Fahrenheit, just extract the number
                    temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    return f"{emoji} {temp_num}°F"
                elif '°C' in temp_str:
                    # Celsius - need to convert
                    temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    try:
                        temp_c = int(temp_num)
                        temp_f = int((temp_c * 9/5) + 32)
                        return f"{emoji} {temp_f}°F"
                    except:
                        return f"{emoji} {temp_str}"
                else:
                    # Unknown format, return as-is
                    return f"{emoji} {temp_str}"
            
            # If we got here, curl failed but didn't raise exception
            if attempt < 2:
                print(f"Weather attempt {attempt+1}/3 failed (curl error), waiting 80s...")
                time.sleep(80)  # Wait 80 seconds between attempts (4 min total)
                continue
            return f"🌤️ --°F"
            
        except Exception as e:
            if attempt < 2:
                print(f"Weather attempt {attempt+1}/3 failed (exception: {e}), waiting 80s...")
                time.sleep(80)  # Wait 80 seconds between attempts (4 min total)
                continue
            return f"🌤️ --°F"
    
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

def auto_refresh_whoop():
    """Auto-refresh Whoop token if needed"""
    try:
        import requests
        from pathlib import Path
        
        # Load config
        with open('/home/ubuntu/.openclaw/workspace/config/whoop-config.json') as f:
            config = json.load(f)
        
        # Load refresh token
        refresh_token_path = Path.home() / '.whoop_refresh_token'
        if not refresh_token_path.exists():
            return False, "No refresh token"
        
        refresh_token = refresh_token_path.read_text().strip()
        
        # Exchange for new tokens
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'redirect_uri': config['redirect_uri']
        }
        
        response = requests.post('https://api.prod.whoop.com/oauth/oauth2/token', data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            
            # Save access token
            (Path.home() / '.whoop_token').write_text(tokens['access_token'])
            
            # Update credentials file
            creds_file = Path.home() / '.openclaw/credentials/whoop-tokens.json'
            with open(creds_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            
            # Update refresh token if provided
            if 'refresh_token' in tokens:
                (Path.home() / '.whoop_refresh_token').write_text(tokens['refresh_token'])
            
            return True, "Auto-refreshed"
        else:
            return False, f"Refresh failed: {response.status_code}"
    except Exception as e:
        return False, str(e)

def get_google_reauth_links():
    """Generate Google re-authorization links"""
    import secrets
    from urllib.parse import urlencode
    
    state = secrets.token_urlsafe(16)
    
    # Calendar link
    calendar_params = {
        'response_type': 'code',
        'client_id': '[REDACTED]',
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'scope': 'https://www.googleapis.com/auth/calendar.readonly',
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    calendar_link = f"https://accounts.google.com/o/oauth2/auth?{urlencode(calendar_params)}"
    
    # Docs link
    docs_params = {
        'response_type': 'code',
        'client_id': '[REDACTED]',
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'scope': 'https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive.file',
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    docs_link = f"https://accounts.google.com/o/oauth2/auth?{urlencode(docs_params)}"
    
    return {'calendar': calendar_link, 'docs': docs_link}

def run_token_health_check():
    """Run token health check, auto-refresh Whoop, return summary with re-auth links"""
    try:
        result = subprocess.run(
            ['python3', '/home/ubuntu/.openclaw/workspace/scripts/token_health_check.py'],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout
        
        # Try to auto-refresh Whoop if expired
        whoop_refreshed = False
        if 'Whoop API' in output and ('expired' in output.lower() or '401' in output):
            refreshed, msg = auto_refresh_whoop()
            whoop_refreshed = refreshed
        
        # Parse the output
        lines = output.split('\n')
        critical_count = 0
        warning_count = 0
        issues = []
        
        for line in lines:
            if 'Token Health Check' in line or 'CRITICAL' in line or 'Immediate action' in line:
                continue
            if line.strip().startswith('🔴'):
                critical_count += 1
                issues.append(line.strip())
            elif line.strip().startswith('🟡') or line.strip().startswith('⚠️'):
                warning_count += 1
                issues.append(line.strip())
        
        # Get re-auth links for Google tokens
        reauth_links = get_google_reauth_links()
        
        # Build summary
        if whoop_refreshed:
            summary = "✅ Whoop auto-refreshed"
        elif critical_count > 0:
            summary = f"🔴 {critical_count} issue{'s' if critical_count > 1 else ''} need attention"
        elif warning_count > 0:
            summary = f"🟡 {warning_count} warning{'s' if warning_count > 1 else ''}"
        else:
            summary = "✅ All tokens healthy"
        
        return {
            'summary': summary,
            'issues': issues,
            'reauth_links': reauth_links,
            'whoop_refreshed': whoop_refreshed
        }
    except Exception as e:
        return {'summary': f"⚠️ Check failed: {str(e)}", 'issues': [], 'reauth_links': {}, 'whoop_refreshed': False}

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
                # Look for "Recovery:** XX%" (markdown bold format)
                match = re.search(r'Recovery:\*\*\s*(\d+(?:\.\d+)?)%', content)
                if match:
                    return int(float(match.group(1)))
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
                        score_obj = recovery_list[0].get('score', {})
                        if score_obj and isinstance(score_obj, dict):
                            recovery_score = score_obj.get('recovery_score')
                            if recovery_score:
                                recovery_data.append({'date': date, 'score': recovery_score})
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

def get_all_calendar_events():
    """Get all calendar events for hotel/birthday detection"""
    calendar_file = Path("/home/ubuntu/.openclaw/workspace/config/calendar-events.json")
    if not calendar_file.exists():
        return []
    
    try:
        with open(calendar_file, 'r') as f:
            data = json.load(f)
        return data.get('events', [])
    except:
        return []

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

def get_upcoming_trips_for_packing(all_events, pt_now):
    """Get upcoming trips with weather info for packing decisions"""
    trips = []
    
    for event in all_events:
        if not event.get('is_travel'):
            continue
        
        # Parse event date
        event_date_str = event.get('start_raw', '')
        try:
            if 'T' in event_date_str:
                event_date = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
                event_date = event_date.replace(tzinfo=None)
            else:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        except:
            continue
        
        # Only show trips in next 14 days
        days_until = (event_date - pt_now.replace(tzinfo=None)).days
        if days_until < 0 or days_until > 14:
            continue
        
        summary = event.get('summary', '').lower()
        location = event.get('location', '').lower()
        
        # Determine destination
        destination = None
        weather_code = None
        if 'jfk' in summary or 'new york' in summary or 'lga' in summary or 'nyc' in location:
            destination = 'New York'
            weather_code = 'New+York'
        elif 'lax' in summary or 'los angeles' in summary:
            destination = 'Los Angeles'
            weather_code = 'Los+Angeles'
        elif 'atl' in summary or 'atlanta' in summary:
            destination = 'Atlanta'
            weather_code = 'Atlanta'
        elif 'sfo' in summary or 'san francisco' in summary:
            destination = 'San Francisco'
            weather_code = 'San+Francisco'
        elif 'phx' in summary or 'phoenix' in summary or 'scottsdale' in summary:
            destination = 'Scottsdale'
            weather_code = 'Scottsdale'
        elif 'pdx' in summary or 'portland' in summary:
            destination = 'Portland'
            weather_code = 'Portland'
        elif 'fll' in summary or 'fort lauderdale' in summary or 'miami' in summary:
            destination = 'Fort Lauderdale'
            weather_code = 'Fort+Lauderdale'
        elif 'pbi' in summary or 'west palm beach' in summary:
            destination = 'West Palm Beach'
            weather_code = 'West+Palm+Beach'
        
        if destination and weather_code:
            # Get weather for destination
            weather = get_weather(weather_code)
            
            trips.append({
                'destination': destination,
                'date': event.get('start', 'TBD'),
                'weather': weather,
                'days_until': days_until,
                'type': 'flight' if 'flight' in summary else 'hotel'
            })
    
    # Sort by date
    trips.sort(key=lambda x: x['days_until'])
    return trips

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
    # Get all events for hotel/birthday detection (not just travel events)
    all_events = get_all_calendar_events()
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
    
    # PACKING SECTION: Upcoming trips with weather for packing decisions
    upcoming_trips = get_upcoming_trips_for_packing(travel_events, pt_now)
    if upcoming_trips:
        html += f'''
    <div class="section" style="border-left-color: #3b82f6; background: #eff6ff;">
        <h2>🎒 Upcoming Trips (Pack Accordingly)</h2>
'''
        for trip in upcoming_trips[:3]:  # Show max 3 trips
            trip_date = trip.get('date', 'TBD')
            trip_dest = trip.get('destination', 'Unknown')
            trip_weather = trip.get('weather', '')
            days_until = trip.get('days_until', 0)
            
            html += f'''
        <div style="margin: 10px 0; padding: 12px; background: white; border-radius: 8px; border-left: 4px solid #3b82f6;">
            <div style="font-weight: bold; color: #1e40af;">{trip_dest} — {trip_date}</div>
            <div style="color: #666; font-size: 14px; margin-top: 4px;">
                {trip_weather} • Pack in {days_until} day{'s' if days_until != 1 else ''}
            </div>
        </div>
'''
        html += '''    </div>
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
        day_events = get_day_events(day, all_events)
        
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
    
    # Upcoming Birthdays section
    upcoming_birthdays = get_upcoming_birthdays(days_ahead=30)
    if upcoming_birthdays:
        html += '''
    <div class="section">
        <h2>🎂 Upcoming Birthdays</h2>
        <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 8px;">
'''
        for person in upcoming_birthdays[:5]:  # Show max 5
            days_text = f"in {person['days_until']} days" if person['days_until'] > 0 else "TODAY! 🎉"
            html += f'''            <div style="margin: 8px 0; padding: 8px; background: white; border-radius: 6px;">
                <strong>{person['name']}</strong> — {person['date_this_year']} <span style="color: #666; font-size: 12px;">({days_text})</span>
                <br><span style="font-size: 12px; color: #888;">{person['relation']}</span>
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
    
    # Token Health section with auto-refresh and re-auth links
    token_health_data = run_token_health_check()
    token_summary = token_health_data['summary']
    token_issues = token_health_data['issues']
    reauth_links = token_health_data['reauth_links']
    whoop_refreshed = token_health_data['whoop_refreshed']
    
    token_color = "#16a34a" if "✅" in token_summary else "#dc2626" if "🔴" in token_summary else "#ea580c"
    
    html += f'''
    <div class="section">
        <h2>🔐 Token Health</h2>
        <p style="color: {token_color}; font-weight: bold;">{token_summary}</p>
'''
    
    # Show Whoop auto-refresh status
    if whoop_refreshed:
        html += '<p style="color: #16a34a; font-size: 13px;">✅ Whoop token auto-refreshed</p>'
    
    # Show issues and re-auth links
    if token_issues:
        html += '<div style="margin-top: 10px;">'
        for issue in token_issues[:3]:  # Show max 3 issues
            html += f'<p style="font-size: 12px; margin: 5px 0;">{issue}</p>'
        
        # Add re-auth links for Google tokens
        if 'Calendar' in str(token_issues) or 'calendar' in str(token_issues).lower():
            html += f'<p style="font-size: 11px; margin: 8px 0;"><a href="{reauth_links.get("calendar", "#")}">Refresh Calendar →</a></p>'
        if 'Docs' in str(token_issues) or 'docs' in str(token_issues).lower():
            html += f'<p style="font-size: 11px; margin: 8px 0;"><a href="{reauth_links.get("docs", "#")}">Refresh Google Docs →</a></p>'
        
        html += '</div>'
    
    html += '<p style="font-size: 12px; color: #666; margin-top: 10px;">Calendar • Docs • Whoop • Email</p>'
    html += '</div>'

    
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

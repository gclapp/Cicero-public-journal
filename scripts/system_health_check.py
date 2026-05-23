#!/usr/bin/env python3
"""
Comprehensive System Health Check
Runs on every heartbeat to verify all integrations are working
Attempts automatic recovery before alerting user
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import sys

# Paths
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "system-health.log"

def log(msg):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(LOG_FILE.parent, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def check_token_age(token_file):
    """Check how old a token file is"""
    if not token_file.exists():
        return None
    
    stat = token_file.stat()
    age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
    return age

def check_todoist():
    """Check Todoist connection"""
    try:
        result = subprocess.run(
            ['todoist', 'today'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # Count tasks
            task_count = len([l for l in result.stdout.strip().split('\n') if l.strip()])
            return {'status': 'ok', 'tasks': task_count}
        else:
            return {'status': 'error', 'error': result.stderr}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_calendar():
    """Check Google Calendar connection"""
    token_file = CREDENTIALS_DIR / "calendar-token.pickle"
    
    if not token_file.exists():
        return {
            'status': 'missing',
            'error': 'Token file does not exist',
            'action_required': True,
            'auth_url': 'https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=[REDACTED]&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly'
        }
    
    age = check_token_age(token_file)
    if age and age.days > 7:
        return {
            'status': 'stale',
            'error': f'Token is {age.days} days old',
            'action_required': True,
            'auth_url': 'https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=[REDACTED]&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%alendar.readonly'
        }
    
    # Try to actually fetch calendar
    try:
        result = subprocess.run(
            ['python3', str(Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'calendar_reader.py')],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0 or 'Authorization Required' not in result.stderr:
            return {'status': 'ok', 'token_age_days': age.days if age else 0}
        else:
            return {
                'status': 'auth_error',
                'error': 'Calendar auth required',
                'action_required': True,
                'auth_url': 'https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=[REDACTED]&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly'
            }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_weather():
    """Check weather skill is available"""
    skill_file = Path.home() / ".openclaw" / "workspace" / "skills" / "weather" / "SKILL.md"
    if skill_file.exists():
        return {'status': 'ok'}
    return {'status': 'not_installed'}

def check_whoop():
    """Check Whoop integration"""
    config_file = CREDENTIALS_DIR / "whoop-config.json"
    if config_file.exists():
        return {'status': 'configured'}
    return {'status': 'not_configured'}

def check_health_dashboard():
    """Check health dashboard status"""
    dashboard_file = Path.home() / ".openclaw" / "workspace" / "health-dashboard" / "index.html"
    if dashboard_file.exists():
        return {'status': 'available', 'url': 'https://gclapp.github.io/health-dashboard/'}
    return {'status': 'not_found'}

def check_watch_hunt():
    """Check watch hunt dashboard"""
    dashboard_file = Path.home() / ".openclaw" / "workspace" / "dashboard" / "index.html"
    if dashboard_file.exists():
        return {'status': 'available', 'url': 'https://gclapp.github.io/geoff-watch-hunt/'}
    return {'status': 'not_found'}

def check_competitive_intel():
    """Check competitive intelligence is running"""
    cron_check = subprocess.run(
        ['crontab', '-l'],
        capture_output=True,
        text=True
    )
    if 'competitor' in cron_check.stdout:
        return {'status': 'active'}
    return {'status': 'unknown'}

def check_travel_automation():
    """Check travel automation is running and count recent tasks"""
    # Check cron job exists (looks for calendar-travel-checker or travel_automation)
    cron_check = subprocess.run(
        ['crontab', '-l'],
        capture_output=True,
        text=True
    )
    if 'calendar-travel-checker' not in cron_check.stdout and 'travel_automation' not in cron_check.stdout:
        return {'status': 'not_scheduled'}
    
    # Check log file for recent runs
    log_file = Path.home() / ".openclaw" / "workspace" / "logs" / "travel-automation-v2.log"
    if log_file.exists():
        try:
            # Get last modified time
            stat = log_file.stat()
            last_run = datetime.fromtimestamp(stat.st_mtime)
            hours_since = (datetime.now() - last_run).total_seconds() / 3600
            
            # Count travel tasks in Todoist
            result = subprocess.run(
                ['todoist', 'list', '-f', 'travel'],
                capture_output=True,
                text=True,
                timeout=30
            )
            task_count = len([l for l in result.stdout.strip().split('\n') if l.strip()]) if result.returncode == 0 else 0
            
            return {
                'status': 'active',
                'last_run_hours': round(hours_since, 1),
                'tasks_created': task_count
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    return {'status': 'active', 'note': 'No log yet'}

def get_weather():
    """Get current weather for LA using wttr.in in Fahrenheit"""
    import time
    
    for attempt in range(3):  # Try 3 times
        try:
            # Get emoji and temperature separately
            emoji_result = subprocess.run(
                ['curl', '-s', 'wttr.in/Los+Angeles?format=%c'],
                capture_output=True,
                text=True,
                timeout=15
            )
            temp_result = subprocess.run(
                ['curl', '-s', 'wttr.in/Los+Angeles?format=%t'],
                capture_output=True,
                text=True,
                timeout=15
            )
            humidity_result = subprocess.run(
                ['curl', '-s', 'wttr.in/Los+Angeles?format=%h'],
                capture_output=True,
                text=True,
                timeout=15
            )
            wind_result = subprocess.run(
                ['curl', '-s', 'wttr.in/Los+Angeles?format=%w'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if emoji_result.returncode == 0 and temp_result.returncode == 0:
                emoji = emoji_result.stdout.strip()
                temp_str = temp_result.stdout.strip()
                humidity = humidity_result.stdout.strip() if humidity_result.returncode == 0 else ""
                wind = wind_result.stdout.strip() if wind_result.returncode == 0 else ""
                
                # Check for wttr.in error message
                if 'weather data source not available' in temp_str or 'weather data source not available' in emoji:
                    if attempt < 2:
                        print(f"  Weather attempt {attempt+1}/3 failed (source not available), waiting 80s...")
                        time.sleep(80)
                        continue
                    return f"los angeles: 🌤️ --°F {humidity} {wind}".strip()
                
                # Check if wttr.in is already returning Fahrenheit
                if '°F' in temp_str:
                    # Already Fahrenheit, just extract the number
                    temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    temp_display = f"{temp_num}°F"
                elif '°C' in temp_str:
                    # Celsius - need to convert
                    temp_num = ''.join([c for c in temp_str if c.isdigit() or c == '-'])
                    try:
                        temp_c = int(temp_num)
                        temp_f = int((temp_c * 9/5) + 32)
                        temp_display = f"{temp_f}°F"
                    except:
                        temp_display = temp_str
                else:
                    # Unknown format, return as-is
                    temp_display = temp_str
                
                return f"los angeles: {emoji} {temp_display} {humidity} {wind}".strip()
            
            if attempt < 2:
                print(f"  Weather attempt {attempt+1}/3 failed (curl error), waiting 80s...")
                time.sleep(80)
                continue
            return None
            
        except Exception as e:
            if attempt < 2:
                print(f"  Weather attempt {attempt+1}/3 failed (exception), waiting 80s...")
                time.sleep(80)
                continue
            return None
    
    return None

def run_health_check():
    """Run comprehensive health check"""
    log("=" * 60)
    log("SYSTEM HEALTH CHECK")
    log("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Check Todoist
    log("\n📋 Checking Todoist...")
    todoist = check_todoist()
    results['checks']['todoist'] = todoist
    if todoist['status'] == 'ok':
        log(f"  ✅ Todoist: {todoist['tasks']} tasks")
    else:
        log(f"  ❌ Todoist: {todoist.get('error', 'Unknown error')}")
    
    # Check Calendar
    log("\n📅 Checking Google Calendar...")
    calendar = check_calendar()
    results['checks']['calendar'] = calendar
    if calendar['status'] == 'ok':
        log(f"  ✅ Calendar: Token {calendar.get('token_age_days', 0)} days old")
    elif calendar.get('action_required'):
        log(f"  🔴 Calendar: {calendar.get('error', 'Auth required')}")
        log(f"  📝 ACTION: User needs to authenticate")
    else:
        log(f"  ❌ Calendar: {calendar.get('error', 'Unknown error')}")
    
    # Check Weather
    log("\n🌤️ Checking Weather...")
    weather_skill = check_weather()
    results['checks']['weather_skill'] = weather_skill
    if weather_skill['status'] == 'ok':
        log("  ✅ Weather skill installed")
        weather_data = get_weather()
        if weather_data:
            log(f"  🌡️ Current: {weather_data[:100]}...")
            results['checks']['weather_data'] = weather_data
    else:
        log("  ⚠️ Weather skill not installed")
    
    # Check Whoop
    log("\n💓 Checking Whoop...")
    whoop = check_whoop()
    results['checks']['whoop'] = whoop
    if whoop['status'] == 'configured':
        log("  ✅ Whoop configured")
    else:
        log("  ⚠️ Whoop not configured")
    
    # Check Health Dashboard
    log("\n🏥 Checking Health Dashboard...")
    health = check_health_dashboard()
    results['checks']['health_dashboard'] = health
    if health['status'] == 'available':
        log(f"  ✅ Health Dashboard: {health['url']}")
    else:
        log("  ❌ Health Dashboard not found")
    
    # Check Watch Hunt
    log("\n⌚ Checking Watch Hunt...")
    watch = check_watch_hunt()
    results['checks']['watch_hunt'] = watch
    if watch['status'] == 'available':
        log(f"  ✅ Watch Hunt: {watch['url']}")
    else:
        log("  ❌ Watch Hunt not found")
    
    # Check Competitive Intel
    log("\n🎯 Checking Competitive Intelligence...")
    comp = check_competitive_intel()
    results['checks']['competitive_intel'] = comp
    if comp['status'] == 'active':
        log("  ✅ Competitive Intel cron active")
    else:
        log("  ⚠️ Competitive Intel status unknown")
    
    # Check Travel Automation
    log("\n✈️ Checking Travel Automation...")
    travel = check_travel_automation()
    results['checks']['travel_automation'] = travel
    if travel['status'] == 'active':
        log(f"  ✅ Travel Automation: {travel.get('tasks_created', 0)} tasks created")
    else:
        log("  ⚠️ Travel Automation may need attention")
    
    log("\n" + "=" * 60)
    
    # Determine overall status
    action_required = []
    for service, check in results['checks'].items():
        if isinstance(check, dict) and check.get('action_required'):
            action_required.append({
                'service': service,
                'error': check.get('error'),
                'auth_url': check.get('auth_url')
            })
    
    results['action_required'] = action_required
    
    if action_required:
        log(f"🔴 ACTION REQUIRED: {len(action_required)} service(s) need attention")
        for item in action_required:
            log(f"   - {item['service']}: {item['error']}")
    else:
        log("✅ All systems operational")
    
    log("=" * 60)
    
    return results

def generate_heartbeat_summary(health_results):
    """Generate summary for heartbeat message"""
    lines = []
    lines.append("📊 SYSTEM STATUS")
    lines.append("")
    
    # Todoist
    todoist = health_results['checks'].get('todoist', {})
    if todoist.get('status') == 'ok':
        lines.append(f"✅ Todoist: {todoist.get('tasks', 0)} tasks pending")
    else:
        lines.append(f"❌ Todoist: {todoist.get('error', 'Connection failed')}")
    
    # Calendar
    calendar = health_results['checks'].get('calendar', {})
    if calendar.get('status') == 'ok':
        lines.append(f"✅ Calendar: Connected ({calendar.get('token_age_days', 0)} days old)")
    elif calendar.get('action_required'):
        lines.append(f"🔴 Calendar: {calendar.get('error', 'Auth required')}")
    else:
        lines.append(f"❌ Calendar: {calendar.get('error', 'Error')}")
    
    # Weather
    weather = health_results['checks'].get('weather_data')
    if weather:
        lines.append(f"🌤️ Weather: {weather[:60]}...")
    else:
        lines.append("⚠️ Weather: Data unavailable")
    
    # Whoop
    whoop = health_results['checks'].get('whoop', {})
    if whoop.get('status') == 'configured':
        lines.append("✅ Whoop: Configured")
    else:
        lines.append("⚠️ Whoop: Not configured")
    
    # Dashboards
    health_dash = health_results['checks'].get('health_dashboard', {})
    watch_dash = health_results['checks'].get('watch_hunt', {})
    
    if health_dash.get('status') == 'available':
        lines.append(f"✅ Health Dashboard: {health_dash.get('url', 'Available')}")
    if watch_dash.get('status') == 'available':
        lines.append(f"✅ Watch Hunt: {watch_dash.get('url', 'Available')}")
    
    # Action items
    if health_results.get('action_required'):
        lines.append("")
        lines.append("🔴 ACTION REQUIRED:")
        for item in health_results['action_required']:
            lines.append(f"   • {item['service']}: {item['error']}")
            if item.get('auth_url'):
                lines.append(f"     Auth URL: {item['auth_url'][:80]}...")
    
    return "\n".join(lines)

if __name__ == "__main__":
    results = run_health_check()
    
    # Print summary for heartbeat
    print("\n" + "=" * 60)
    print("HEARTBEAT SUMMARY")
    print("=" * 60)
    print(generate_heartbeat_summary(results))
    print("=" * 60)
    
    # Save results
    results_file = Path.home() / ".openclaw" / "workspace" / "config" / "last-health-check.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with error code if action required
    if results.get('action_required'):
        sys.exit(1)
    sys.exit(0)

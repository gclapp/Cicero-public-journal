#!/usr/bin/env python3
"""
Comprehensive System Health Check
Runs on every heartbeat to verify all integrations are working
Attempts automatic recovery before alerting user
"""

import json
import os
import base64
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import sys
import socket

# Paths
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "system-health.log"
TODOIST_PATH = "/home/ubuntu/.npm-global/bin/todoist"

def get_calendar_auth_url():
    """Build the same PKCE calendar auth URL used by calendar_reader.py."""
    code_verifier_file = CREDENTIALS_DIR / "calendar-code-verifier.txt"
    if code_verifier_file.exists():
        code_verifier = code_verifier_file.read_text().strip()
    else:
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        code_verifier_file.write_text(code_verifier)

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')

    return (
        "https://accounts.google.com/o/oauth2/auth"
        "?response_type=code"
        "&client_id=[REDACTED]"
        "&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob"
        "&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly"
        f"&code_challenge={code_challenge}"
        "&code_challenge_method=S256"
        "&prompt=consent"
        "&access_type=offline"
    )

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
            [TODOIST_PATH, 'today', '--json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            tasks = json.loads(result.stdout or '[]')
            task_count = len(tasks)
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
            'auth_url': get_calendar_auth_url()
        }
    
    age = check_token_age(token_file)
    if age and age.days > 7:
        return {
            'status': 'stale',
            'error': f'Token is {age.days} days old',
            'action_required': True,
            'auth_url': get_calendar_auth_url()
        }
    
    # Try to actually fetch calendar
    try:
        result = subprocess.run(
            [
                'python3',
                str(Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'calendar_reader.py'),
                '--days',
                '1',
                '--max',
                '1',
                '--no-save',
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return {'status': 'ok', 'token_age_days': age.days if age else 0}
        output = f"{result.stdout}\n{result.stderr}".lower()
        if (
            'authorization required' in output
            or 'invalid_grant' in output
            or 'refresherror' in output
            or 'expired or revoked' in output
            or 'expired or been revoked' in output
            or 'has expired' in output
            or 'been revoked' in output
        ):
            return {
                'status': 'auth_error',
                'error': 'Calendar auth token expired or revoked',
                'action_required': True,
                'auth_url': get_calendar_auth_url()
            }
        return {
            'status': 'error',
            'error': (result.stderr or result.stdout or 'Calendar reader failed').strip()[-500:]
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

def check_model_status():
    """Check current AI model status"""
    PRIMARY_MODEL = "moonshot/kimi-k2.7-code"
    FALLBACK_MODELS = [
        "openai/gpt-5.5",
        "openai/gpt-5.4-mini",
        "openai/o3-mini",
        "moonshot/kimi-k2.5",
        "openai/gpt-5.4-nano",
    ]

    # Try to read from marker file
    marker_file = Path.home() / ".openclaw" / "workspace" / "logs" / "current-model.txt"
    current = None
    if marker_file.exists():
        try:
            with open(marker_file) as f:
                current = f.read().strip()
        except:
            pass

    # Fallback to environment
    if not current:
        current = os.environ.get('OPENCLAW_CURRENT_MODEL', 'unknown')

    is_primary = current == PRIMARY_MODEL
    is_fallback = not is_primary and any(fb in current for fb in FALLBACK_MODELS)

    return {
        'status': 'ok' if is_primary else ('fallback' if is_fallback else 'unknown'),
        'current': current,
        'primary': PRIMARY_MODEL,
        'is_fallback': is_fallback,
        'is_primary': is_primary
    }

def check_travel_automation():
    """Check travel automation is running and count recent tasks"""
    # Check cron job exists. Aero is the current travel automation; keep older
    # names for compatibility with archived/legacy deployments.
    cron_check = subprocess.run(
        ['crontab', '-l'],
        capture_output=True,
        text=True
    )
    travel_cron_names = [
        'aero_travel_cron.sh',
        'aero_monitor_cron.sh',
        'calendar-travel-checker',
        'travel_automation',
    ]
    if not any(name in cron_check.stdout for name in travel_cron_names):
        return {'status': 'not_scheduled'}
    
    # Check log file for recent runs
    log_dir = Path.home() / ".openclaw" / "workspace" / "logs"
    log_files = [
        log_dir / "aero-monitor.log",
        log_dir / "aero-cron.log",
        log_dir / "travel-automation-v2.log",
    ]
    existing_logs = [path for path in log_files if path.exists()]
    if existing_logs:
        try:
            # Get most recent travel automation log update.
            log_file = max(existing_logs, key=lambda path: path.stat().st_mtime)
            stat = log_file.stat()
            last_run = datetime.fromtimestamp(stat.st_mtime)
            hours_since = (datetime.now() - last_run).total_seconds() / 3600
            
            # Count travel tasks in Todoist
            result = subprocess.run(
                [TODOIST_PATH, 'list', '-f', 'travel'],
                capture_output=True,
                text=True,
                timeout=30
            )
            task_count = len([l for l in result.stdout.strip().split('\n') if l.strip()]) if result.returncode == 0 else 0
            
            return {
                'status': 'active',
                'last_run_hours': round(hours_since, 1),
                'tasks_created': task_count,
                'log_file': log_file.name
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    return {'status': 'active', 'note': 'No log yet'}

def _read_meminfo():
    """Read /proc/meminfo values in KiB."""
    values = {}
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                key, raw_value = line.split(':', 1)
                parts = raw_value.strip().split()
                if parts and parts[0].isdigit():
                    values[key] = int(parts[0])
    except Exception:
        pass
    return values

def _recent_journal_matches(minutes=90):
    """Return recent host-level OOM/power/reboot warning evidence."""
    patterns = [
        'oom',
        'out of memory',
        'killed by the oom',
        'power key pressed',
        'the system will power off now',
        'temporary failure resolving',
        'eai_again',
        'err_name_not_resolved',
    ]
    try:
        result = subprocess.run(
            [
                'journalctl',
                '-b',
                '--since',
                f'{minutes} minutes ago',
                '--no-pager',
                '-o',
                'short-iso',
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            return []
        matches = []
        for line in result.stdout.splitlines():
            lower = line.lower()
            if any(pattern in lower for pattern in patterns):
                matches.append(line[-500:])
        return matches[-12:]
    except Exception:
        return []

def _top_memory_processes(limit=8):
    try:
        result = subprocess.run(
            ['ps', '-eo', 'pid,comm,rss,args', '--sort=-rss'],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        processes = []
        for line in result.stdout.splitlines()[1:limit + 1]:
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            pid, command, rss_kib, args = parts
            try:
                rss_mib = round(int(rss_kib) / 1024, 1)
            except ValueError:
                rss_mib = None
            processes.append({
                'pid': pid,
                'command': command,
                'rss_mib': rss_mib,
                'args': args[:180],
            })
        return processes
    except Exception:
        return []

def check_host_health():
    """Check host-level uptime risks: RAM, swap, DNS, reboot/OOM evidence, OpenClaw."""
    meminfo = _read_meminfo()
    mem_total = meminfo.get('MemTotal', 0)
    mem_available = meminfo.get('MemAvailable', 0)
    swap_total = meminfo.get('SwapTotal', 0)
    swap_free = meminfo.get('SwapFree', 0)

    mem_available_pct = round((mem_available / mem_total) * 100, 1) if mem_total else None
    swap_used_pct = round(((swap_total - swap_free) / swap_total) * 100, 1) if swap_total else 0

    issues = []
    status = 'ok'
    if mem_available_pct is not None and mem_available_pct < 12:
        status = 'critical'
        issues.append(f'Available memory is critically low: {mem_available_pct}%')
    elif mem_available_pct is not None and mem_available_pct < 20:
        status = 'warn'
        issues.append(f'Available memory is low: {mem_available_pct}%')

    if swap_used_pct >= 75:
        status = 'critical'
        issues.append(f'Swap usage is critically high: {swap_used_pct}%')
    elif swap_used_pct >= 50 and status != 'critical':
        status = 'warn'
        issues.append(f'Swap usage is elevated: {swap_used_pct}%')

    dns_ok = True
    dns_error = None
    try:
        socket.getaddrinfo('api.openai.com', 443)
        socket.getaddrinfo('github.com', 443)
    except Exception as exc:
        dns_ok = False
        dns_error = str(exc)
        status = 'critical'
        issues.append(f'DNS resolution failed: {dns_error}')

    openclaw_running = False
    openclaw_rss_mib = 0.0
    try:
        result = subprocess.run(
            ['pgrep', '-af', 'openclaw/dist/index.js gateway'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        openclaw_running = result.returncode == 0 and bool(result.stdout.strip())
        if not openclaw_running:
            status = 'critical'
            issues.append('OpenClaw gateway process is not running')
        for line in result.stdout.splitlines():
            pid = line.split(None, 1)[0]
            try:
                with open(f'/proc/{pid}/status') as f:
                    for status_line in f:
                        if status_line.startswith('VmRSS:'):
                            openclaw_rss_mib += int(status_line.split()[1]) / 1024
                            break
            except Exception:
                pass
    except Exception as exc:
        if status != 'critical':
            status = 'warn'
        issues.append(f'Could not check OpenClaw process: {exc}')

    recent_events = _recent_journal_matches()
    if recent_events and status == 'ok':
        status = 'warn'
        issues.append('Recent host-level warning events found in journal')

    return {
        'status': status,
        'issues': issues,
        'memory': {
            'total_mib': round(mem_total / 1024, 1) if mem_total else None,
            'available_mib': round(mem_available / 1024, 1) if mem_available else None,
            'available_pct': mem_available_pct,
        },
        'swap': {
            'total_mib': round(swap_total / 1024, 1) if swap_total else 0,
            'free_mib': round(swap_free / 1024, 1) if swap_free else 0,
            'used_pct': swap_used_pct,
        },
        'dns_ok': dns_ok,
        'dns_error': dns_error,
        'openclaw_running': openclaw_running,
        'openclaw_rss_mib': round(openclaw_rss_mib, 1),
        'recent_events': recent_events,
        'top_memory_processes': _top_memory_processes(),
        'action_required': status == 'critical',
    }

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
    
    # Check Model Status
    log("\n🤖 Checking Model Status...")
    model_status = check_model_status()
    results['checks']['model'] = model_status
    if model_status['status'] == 'ok':
        log(f"  ✅ Model: {model_status.get('current', 'Unknown')} (Primary: {model_status.get('primary', 'Unknown')})")
    elif model_status.get('is_fallback'):
        log(f"  ⚠️ Model: Using fallback {model_status.get('current')} (Expected: {model_status.get('primary')})")
    else:
        log(f"  ⚠️ Model: Status unknown")

    # Check Host Health
    log("\n🖥️ Checking Host Health...")
    host = check_host_health()
    results['checks']['host'] = host
    mem = host.get('memory', {})
    swap = host.get('swap', {})
    host_line = (
        f"mem avail {mem.get('available_mib')} MiB "
        f"({mem.get('available_pct')}%), "
        f"swap used {swap.get('used_pct')}%, "
        f"OpenClaw RSS {host.get('openclaw_rss_mib')} MiB"
    )
    if host['status'] == 'ok':
        log(f"  ✅ Host: {host_line}")
    elif host['status'] == 'warn':
        log(f"  ⚠️ Host: {host_line}")
        for issue in host.get('issues', []):
            log(f"     - {issue}")
    else:
        log(f"  🔴 Host: {host_line}")
        for issue in host.get('issues', []):
            log(f"     - {issue}")
    
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
    
    # Model Status
    model = health_results['checks'].get('model', {})
    if model.get('is_primary'):
        lines.append(f"✅ Model: {model.get('primary', 'GPT-4o')} (Primary)")
    elif model.get('is_fallback'):
        lines.append(f"⚠️ Model: FALLBACK - Using {model.get('current', 'Unknown')} (Expected: {model.get('primary', 'GPT-4o')})")
    else:
        lines.append("⚠️ Model: Status unknown")

    # Host Health
    host = health_results['checks'].get('host', {})
    if host:
        mem = host.get('memory', {})
        swap = host.get('swap', {})
        host_text = (
            f"{mem.get('available_mib')} MiB available "
            f"({mem.get('available_pct')}%), swap {swap.get('used_pct')}%"
        )
        if host.get('status') == 'ok':
            lines.append(f"✅ Host: {host_text}")
        elif host.get('status') == 'warn':
            lines.append(f"⚠️ Host: {host_text}")
        else:
            lines.append(f"🔴 Host: {host_text}")
    
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

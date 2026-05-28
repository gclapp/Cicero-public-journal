#!/usr/bin/env python3
"""
Vitus - Whoop Token Monitor
Proactively monitors Whoop token health and alerts when re-authentication is needed
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

TOKEN_FILE = Path.home() / '.whoop_token'
LOG_FILE = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'whoop-token-monitor.log'
ALERT_FILE = Path.home() / '.openclaw' / 'workspace' / 'data' / 'whoop' / 'token-status.json'
EMAIL_SCRIPT = Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'send_email.py'


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f'[{ts}] {msg}'
    print(full_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(full_msg + '\n')


def check_token_health():
    """Check if Whoop token is valid"""
    if not TOKEN_FILE.exists():
        log('❌ No token file found')
        return {'valid': False, 'error': 'No token file', 'action_required': True}
    
    token = TOKEN_FILE.read_text().strip()
    if not token:
        log('❌ Token file is empty')
        return {'valid': False, 'error': 'Empty token', 'action_required': True}
    
    # Test token with a simple API call
    headers = {'Authorization': f'Bearer {token}'}
    BASE_URL = 'https://api.prod.whoop.com/developer/v2'
    
    try:
        # Try to fetch user profile (lightweight endpoint)
        response = requests.get(f'{BASE_URL}/user/profile/basic', headers=headers, timeout=10)
        
        if response.status_code == 200:
            log('✅ Token is valid')
            return {
                'valid': True,
                'checked_at': datetime.now().isoformat(),
                'action_required': False
            }
        elif response.status_code == 401:
            log('❌ Token expired (401 Unauthorized)')
            return {
                'valid': False,
                'error': 'Token expired',
                'status_code': 401,
                'action_required': True,
                'reauth_needed': True
            }
        else:
            log(f'⚠️ Unexpected status code: {response.status_code}')
            return {
                'valid': False,
                'error': f'HTTP {response.status_code}',
                'action_required': response.status_code >= 500
            }
            
    except requests.exceptions.Timeout:
        log('⚠️ Request timeout - Whoop API may be down')
        return {'valid': False, 'error': 'Timeout', 'action_required': False, 'retry_later': True}
    except Exception as e:
        log(f'❌ Error checking token: {e}')
        return {'valid': False, 'error': str(e), 'action_required': True}


def save_status(status):
    """Save token status to file"""
    ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERT_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def load_status():
    """Load previous token status"""
    if ALERT_FILE.exists():
        try:
            with open(ALERT_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def should_send_alert(current_status, previous_status):
    """Determine if we should send an alert email"""
    # Always alert if token is invalid and action is required
    if current_status.get('action_required') and not current_status.get('valid'):
        # Don't spam - only alert once per day for the same issue
        if previous_status.get('last_alert_sent'):
            last_alert = datetime.fromisoformat(previous_status['last_alert_sent'])
            if datetime.now() - last_alert < timedelta(hours=24):
                return False
        return True
    return False


def send_reauth_alert():
    """Send email alert that re-authentication is needed"""
    html_body = f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; background: #f5f5f5; }}
.container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #e74c3c; }}
h1 {{ color: #e74c3c; margin-top: 0; }}
.code {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 0.9em; overflow-x: auto; }}
ol {{ line-height: 2; }}
li {{ margin: 10px 0; }}
</style>
</head>
<body>
<div class="container">
<h1>🫀 Vitus Alert: Whoop Re-Authentication Required</h1>

<p>Your Whoop API token has expired. Vitus cannot fetch your health data until this is resolved.</p>

<h2>What happened?</h2>
<p>Whoop OAuth tokens expire after 1 hour and need to be refreshed. The current token is no longer valid.</p>

<h2>How to fix:</h2>
<ol>
<li>Run the OAuth flow to get a new token:</li>
</ol>

<div class="code">
python3 ~/.openclaw/workspace/skills/whoop-openclaw-skill/scripts/whoop_oauth.py \\
  --config ~/.openclaw/workspace/config/whoop-config.json
</div>

<ol start="2">
<li>Click the authorization URL and log in to Whoop</li>
<li>Copy the authorization code from the redirect page</li>
<li>Exchange the code for a token:</li>
</ol>

<div class="code">
python3 ~/.openclaw/workspace/skills/whoop-openclaw-skill/scripts/whoop_oauth.py \\
  --config ~/.openclaw/workspace/config/whoop-config.json \\
  exchange &lt;YOUR_CODE&gt;
</div>

<p>Once complete, Vitus will resume normal health monitoring.</p>

<hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
<p style="color: #7f8c8d; font-size: 0.9em;">
Alert sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
Vitus | Your dedicated health coach
</p>
</div>
</body>
</html>"""
    
    temp_file = Path('/tmp/vitus_whoop_alert.html')
    temp_file.write_text(html_body)
    
    import subprocess
    result = subprocess.run([
        'python3', str(EMAIL_SCRIPT),
        '--to', '[REDACTED]',
        '--subject', f'🫀 Vitus Alert: Whoop Re-Authentication Required',
        '--body-file', str(temp_file),
        '--html'
    ], capture_output=True, text=True)
    
    return result.returncode == 0


def main():
    """Main monitoring function"""
    log('Starting Whoop token health check...')
    
    previous_status = load_status()
    current_status = check_token_health()
    
    # Save current status
    current_status['checked_at'] = datetime.now().isoformat()
    
    # Send alert if needed
    if should_send_alert(current_status, previous_status):
        log('🚨 Sending re-authentication alert...')
        if send_reauth_alert():
            log('✅ Alert sent successfully')
            current_status['last_alert_sent'] = datetime.now().isoformat()
        else:
            log('❌ Failed to send alert')
    
    save_status(current_status)
    
    # Exit with error code if token is invalid
    if not current_status.get('valid'):
        exit(1)
    
    exit(0)


if __name__ == '__main__':
    main()

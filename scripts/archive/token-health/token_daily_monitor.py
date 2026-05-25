#!/usr/bin/env python3
"""
Aggressive Token Monitor - Daily check with auto-refresh attempts
Run every morning at 7:15 AM PT (before check-ins)
"""

import os
import sys
import json
import pickle
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Token configurations
TOKENS = {
    'calendar': {
        'path': Path.home() / '.openclaw' / 'credentials' / 'calendar-token.pickle',
        'name': 'Google Calendar',
        'alert_days': 6,
        'critical': True,
        'refreshable': True
    },
    'gdocs': {
        'path': Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle',
        'name': 'Google Docs',
        'alert_days': 6,
        'critical': True,
        'refreshable': True
    },
    'whoop': {
        'path': Path.home() / '.whoop_token',
        'name': 'Whoop API',
        'alert_days': 25,
        'critical': True,
        'refreshable': True
    },
    'email': {
        'path': Path.home() / '.openclaw' / 'email_config.json',
        'name': 'Gmail SMTP',
        'alert_days': 60,  # App passwords rarely expire
        'critical': True,
        'refreshable': False
    }
}

def send_alert_email(subject, body):
    """Send alert email to Geoff"""
    try:
        subprocess.run([
            'python3', '/home/ubuntu/.openclaw/workspace/scripts/send_email.py',
            '--to', '[REDACTED]',
            '--subject', subject,
            '--body', body,
            '--html'
        ], check=True, timeout=30)
        return True
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False

def refresh_google_token(token_path, token_name):
    """Attempt to refresh a Google OAuth token"""
    try:
        from google.auth.transport.requests import Request
        
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)
        
        if creds.valid:
            return True, "Already valid"
        
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token
                with open(token_path, 'wb') as f:
                    pickle.dump(creds, f)
                return True, "Auto-refreshed successfully"
            except Exception as e:
                return False, f"Refresh failed: {str(e)}"
        
        return False, "No refresh token available"
    except Exception as e:
        return False, f"Error: {str(e)}"

def refresh_whoop_token():
    """Attempt to refresh Whoop token using refresh token"""
    try:
        import requests
        
        refresh_path = Path.home() / '.whoop_refresh_token'
        if not refresh_path.exists():
            return False, "No refresh token file"
        
        # Load Whoop config for client credentials
        config_path = Path.home() / '.openclaw' / 'credentials' / 'whoop-config.json'
        if not config_path.exists():
            return False, "No Whoop config (client credentials missing)"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        refresh_token = refresh_path.read_text().strip()
        
        # OAuth2 token refresh with client credentials
        response = requests.post(
            'https://api.prod.whoop.com/oauth/oauth2/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': config.get('client_id', ''),
                'client_secret': config.get('client_secret', '')
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Save new access token
            token_path = Path.home() / '.whoop_token'
            token_path.write_text(data['access_token'])
            
            # Save new refresh token if provided
            if 'refresh_token' in data:
                refresh_path.write_text(data['refresh_token'])
            
            return True, "Auto-refreshed successfully"
        else:
            return False, f"API error {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_and_refresh_token(token_key):
    """Check token health and attempt refresh if needed"""
    config = TOKENS[token_key]
    path = config['path']
    
    result = {
        'name': config['name'],
        'status': 'unknown',
        'message': '',
        'action_required': False,
        'critical': config['critical'],
        'auto_refreshed': False
    }
    
    if not path.exists():
        result['status'] = 'missing'
        result['message'] = f"❌ {config['name']}: Token file not found"
        result['action_required'] = True
        return result
    
    # Get file age
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    age_days = (datetime.now() - mtime).days
    result['age_days'] = age_days
    
    # Check if refresh needed
    needs_refresh = False
    
    if token_key in ['calendar', 'gdocs']:
        try:
            with open(path, 'rb') as f:
                creds = pickle.load(f)
            if not creds.valid:
                needs_refresh = True
        except:
            needs_refresh = True
    
    elif token_key == 'whoop':
        try:
            import requests
            token = path.read_text().strip()
            response = requests.get(
                'https://api.prod.whoop.com/developer/v2/recovery',
                headers={'Authorization': f'Bearer {token}'},
                params={'limit': 1},
                timeout=10
            )
            if response.status_code == 401:
                needs_refresh = True
        except:
            needs_refresh = True
    
    # Attempt auto-refresh if needed and possible
    if needs_refresh and config['refreshable']:
        print(f"  Attempting auto-refresh for {config['name']}...")
        
        if token_key in ['calendar', 'gdocs']:
            success, msg = refresh_google_token(path, config['name'])
        elif token_key == 'whoop':
            success, msg = refresh_whoop_token()
        else:
            success, msg = False, "Not refreshable"
        
        if success:
            result['status'] = 'refreshed'
            result['message'] = f"✅ {config['name']}: Auto-refreshed ({msg})"
            result['auto_refreshed'] = True
            return result
        else:
            result['refresh_failed'] = msg
    
    # Check age-based alerts
    if age_days > config['alert_days']:
        result['status'] = 'stale'
        result['message'] = f"⚠️ {config['name']}: {age_days} days old"
        result['action_required'] = True
        return result
    
    # Healthy
    result['status'] = 'healthy'
    result['message'] = f"✅ {config['name']}: Healthy ({age_days} days)"
    return result

def run_daily_check():
    """Run complete daily token check with auto-refresh"""
    print("=" * 70)
    print(f"🔐 Daily Token Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = []
    critical_issues = []
    refreshed = []
    
    for token_key in TOKENS:
        result = check_and_refresh_token(token_key)
        results.append(result)
        print(f"  {result['message']}")
        
        if result.get('auto_refreshed'):
            refreshed.append(result)
        
        if result['action_required'] or (result['status'] == 'stale' and result['critical']):
            critical_issues.append(result)
    
    print("=" * 70)
    
    # Summary
    if refreshed:
        print(f"\n🔄 Auto-refreshed: {len(refreshed)}")
        for r in refreshed:
            print(f"   - {r['name']}")
    
    if critical_issues:
        print(f"\n🔴 CRITICAL ({len(critical_issues)}): Manual action required")
        for issue in critical_issues:
            print(f"   - {issue['name']}: {issue.get('refresh_failed', 'Token expired')}")
        
        # Send alert email
        alert_body = "<h2>🔐 Token Alert - Action Required</h2><ul>"
        for issue in critical_issues:
            alert_body += f"<li><strong>{issue['name']}</strong>: {issue.get('refresh_failed', 'Token expired')}</li>"
        alert_body += "</ul><p>Run token re-authorization to fix.</p>"
        
        send_alert_email(
            "🔐 Token Alert: Manual Re-Auth Required",
            alert_body
        )
    
    if not critical_issues:
        print("\n✅ All tokens healthy or auto-refreshed")
    
    # Save report
    report_file = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'token-daily.json'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'refreshed_count': len(refreshed),
            'critical_count': len(critical_issues)
        }, f, indent=2)
    
    return len(critical_issues) == 0

if __name__ == "__main__":
    success = run_daily_check()
    sys.exit(0 if success else 1)

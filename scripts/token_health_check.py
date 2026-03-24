#!/usr/bin/env python3
"""
Token Health Monitor - Daily check of all OAuth tokens
Run as part of morning check-in (7:30 AM PT)
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path

# Token locations
TOKENS = {
    'calendar': {
        'path': Path.home() / '.openclaw' / 'credentials' / 'calendar-token.pickle',
        'name': 'Google Calendar',
        'alert_threshold_days': 6,
        'auto_refresh': True,
        'critical': True
    },
    'whoop': {
        'path': Path.home() / '.whoop_token',
        'name': 'Whoop API',
        'alert_threshold_days': 25,
        'auto_refresh': False,
        'critical': False
    },
    'whoop_refresh': {
        'path': Path.home() / '.whoop_refresh_token',
        'name': 'Whoop Refresh Token',
        'alert_threshold_days': 25,
        'auto_refresh': False,
        'critical': False
    },
    'email': {
        'path': Path.home() / '.openclaw' / 'email_config.json',
        'name': 'Gmail SMTP',
        'alert_threshold_days': 30,  # App passwords don't expire
        'auto_refresh': False,
        'critical': True
    }
}

def validate_whoop_token():
    """Actually try to use the Whoop token to verify it works"""
    try:
        import requests
        token_file = Path.home() / '.whoop_token'
        if not token_file.exists():
            return False, "Token file not found"
        
        token = token_file.read_text().strip()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to fetch recovery data
        response = requests.get(
            'https://api.prod.whoop.com/developer/v2/recovery',
            headers=headers,
            params={'limit': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Token valid"
        elif response.status_code == 401:
            return False, "Token expired (401)"
        else:
            return False, f"API error {response.status_code}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def check_token_health(token_key):
    """Check health of a specific token"""
    config = TOKENS[token_key]
    path = config['path']
    
    if not path.exists():
        return {
            'status': 'missing',
            'message': f"❌ {config['name']}: Token file not found",
            'action_required': True,
            'critical': config['critical']
        }
    
    # Get file modification time
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    age_days = (datetime.now() - mtime).days
    
    # For Whoop, actually validate the token works
    if token_key == 'whoop':
        is_valid, validation_msg = validate_whoop_token()
        if not is_valid:
            return {
                'status': 'invalid',
                'age_days': age_days,
                'message': f"🔴 {config['name']}: {validation_msg} — RE-AUTH REQUIRED",
                'action_required': True,
                'critical': True  # Upgrade to critical since it's actually broken
            }
    
    # Check if token needs attention based on age
    if age_days > config['alert_threshold_days']:
        return {
            'status': 'stale',
            'age_days': age_days,
            'message': f"⚠️ {config['name']}: Token is {age_days} days old (threshold: {config['alert_threshold_days']})",
            'action_required': True,
            'critical': config['critical']
        }
    
    return {
        'status': 'healthy',
        'age_days': age_days,
        'message': f"✅ {config['name']}: Healthy ({age_days} days old)",
        'action_required': False,
        'critical': config['critical']
    }

def run_health_check():
    """Run complete token health check"""
    results = []
    critical_issues = []
    warnings = []
    
    print("🔐 Token Health Check - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    for token_key in TOKENS:
        result = check_token_health(token_key)
        results.append(result)
        print(result['message'])
        
        if result['action_required']:
            if result['critical']:
                critical_issues.append(result)
            else:
                warnings.append(result)
    
    print("=" * 70)
    
    # Summary
    if critical_issues:
        print(f"\n🔴 CRITICAL ({len(critical_issues)}): Immediate action required")
        for issue in critical_issues:
            print(f"   - {issue['message']}")
    
    if warnings:
        print(f"\n🟡 WARNINGS ({len(warnings)}): Attention needed soon")
        for warning in warnings:
            print(f"   - {warning['message']}")
    
    if not critical_issues and not warnings:
        print("\n✅ All tokens healthy")
    
    # Save report
    report_file = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'token-health.json'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'critical_count': len(critical_issues),
        'warning_count': len(warnings)
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved: {report_file}")
    
    return len(critical_issues) == 0

if __name__ == "__main__":
    import sys
    success = run_health_check()
    sys.exit(0 if success else 1)
